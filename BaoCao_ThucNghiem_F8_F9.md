# BÁO CÁO THỰC NGHIỆM TIẾN ĐỘ TASK 11 (ĐỀ TÀI KC.01.04)
## Vá lỗi F8 (Mất timeout lệnh On-demand) & Khép vòng phản hồi F9 trên Script `opnsense-fw`

| Thông tin | Chi tiết |
|---|---|
| **Đề tài** | OTSD/OTSA (Mã số: KC.01.04) |
| **Nhiệm vụ** | Task 11 — Phát triển mở rộng kênh truyền 2 chiều giữa OPNsense và Wazuh Central |
| **Ngày thực nghiệm** | 07/10/2026 |
| **Môi trường** | • OPNsense VM (`192.168.56.56`) — Wazuh Agent v4.14.7 (Active)<br>• Ubuntu VM `otsd-server` (`192.168.56.10`) — Cụm Wazuh Central v4.14.7 (Docker: Manager, Indexer, Dashboard)<br>• Windows Host (`192.168.56.1`) — Đối tượng kiểm thử lưu lượng mạng (ICMP Ping) |

---

## I. ĐẶT VẤN ĐỀ & MỤC TIÊU THỰC NGHIỆM

Trong khuôn khổ Task 11, mục tiêu là tận dụng và mở rộng đường ống truyền thông 2 chiều sẵn có (giao thức OSSEC qua cổng 1514) giữa Wazuh Central và Appliance OPNsense để phục vụ điều khiển, giám sát an ninh mạng OT mà không mở thêm các cổng dịch vụ tùy tiện.

Qua khảo sát ở giai đoạn trước, hệ thống tồn tại 2 vấn đề kỹ thuật trọng yếu:
1. **Lỗi F8 (Mất timeout lệnh On-demand):** Khi người quản trị chủ động phát lệnh chặn IP từ Central (`agent_control`), lệnh bị giữ vĩnh viễn (Permanent Block), bộ đếm thời gian timeout 60 giây không hoạt động, làm mất khả năng tự động khôi phục lưu lượng.
2. **Hạn chế F9 (Thiếu kênh xác nhận đóng vòng - Closed-loop Confirmation):** Central phát lệnh xuống nhưng không có cơ chế kiểm tra kết quả thực thi thực tế dưới nhân Packet Filter (PF) của firewall để gửi Alert xác nhận hoàn thành về Dashboard.

**Mục tiêu đợt thực nghiệm này:**
- Vá triệt để lỗi logic trong script `opnsense-fw` để phục hồi cơ chế đếm ngược thời gian cho lệnh On-demand (F8).
- Chuẩn hóa nhật ký thực thi kèm nhãn trạng thái `[status: SUCCESS]` làm tiền đề khép vòng xác nhận (F9).
- Chuẩn hóa cấu hình Active Response trên Wazuh Manager trong môi trường container hóa Docker.

---

## II. NGUYÊN NHÂN GỐC RỄ & GIẢI PHÁP KỸ THUẬT (ROOT CAUSE ANALYSIS)

### 2.1. Phân tích nguyên nhân lỗi F8
* **Quy trình chuẩn của Wazuh Active Response:** Khi daemon `wazuh-execd` trên Agent thực thi script, nó mở pipe lắng nghe STDOUT của script để nhận bản tin `check_keys`. Bản tin này chứa một định danh duy nhất (khóa). Nếu nhận được `check_keys`, `wazuh-execd` mới đưa khóa vào danh sách đếm ngược (`timeout_list`), phản hồi `continue` vào STDIN và kích hoạt bộ đếm thời gian (ví dụ 60 giây) để sau đó tự động gọi lệnh `delete`.
* **Lỗi trong code cũ:**
  ```python
  try:
      unique_key = "%s-%s" % (event['parameters']['alert']['rule']['id'], srcip)
      send_log('Sending check_keys for: %s' % unique_key)
      print(json.dumps({"command": "check_keys", "parameters": {"keys": [unique_key]}}))
      sys.stdout.flush()
  except KeyError:
      pass  # LỖI: Lệnh on-demand không có alert.rule.id -> Dính KeyError và bỏ qua check_keys
  ```
  Lệnh chủ động phát từ Central (`agent_control`) không mang ngữ cảnh Alert nên **không có trường `rule.id`**. Đoạn code trên dính ngoại lệ `KeyError` và nhảy vào `pass`, dẫn đến việc script **không gửi `check_keys`**. Vì thiếu khóa, `wazuh-execd` coi đây là lệnh không có timeout $\rightarrow$ IP bị chặn vĩnh viễn.

### 2.2. Giải pháp vá mã nguồn (`opnsense-fw`)
1. **Fallback Rule ID (Vá F8):** Bổ sung khối xử lý ngoại lệ: nếu không tìm thấy `rule.id`, tự động gán `rule_id = 'on-demand'` và sinh khóa dự phòng `on-demand-<srcip>`. Đảm bảo bản tin `check_keys` luôn luôn được gửi ra STDOUT.
2. **Kiểm soát mã trả về của PF (Tiền đề F9):** Dùng `subprocess.run(..., capture_output=True)` gọi `/sbin/pfctl` và kiểm tra `res_add.returncode == 0`. Ghi nhận rõ ràng trạng thái `[status: SUCCESS]` (hoặc `FAILED`) vào nhật ký `/var/ossec/logs/active-responses.log`.
3. **Mở rộng trích xuất IP:** Bổ sung fallback tìm địa chỉ IP trong `parameters.keys` và `parameters.extra_args` để tương thích đa dạng định dạng lệnh từ API.

---

## III. SO SÁNH MÃ NGUỒN TRƯỚC VÀ SAU KHI VÁ

> 📸 **[NOTE ẢNH 1: Chụp màn hình Code Diff trong VS Code]**  
> *(Chụp đoạn code đã sửa trong file `opnsense-fw` trên giao diện VS Code, làm nổi bật khối `check_keys` có fallback `rule_id = 'on-demand'` và khối `status: SUCCESS`).*

```python
# ==============================================================================
# ĐOẠN CODE ĐÃ VÁ HOÀN CHỈNH TRONG opnsense-fw
# ==============================================================================

    if command == 'add':
        # [F8 Patch]: Fallback rule_id cho lệnh on-demand khi alert.rule.id không tồn tại
        rule_id = 'on-demand'
        try:
            rule_id = event['parameters']['alert']['rule']['id']
        except (KeyError, TypeError):
            rule_id = 'on-demand'

        unique_key = "%s-%s" % (rule_id, srcip)
        send_log('Sending check_keys for: %s' % unique_key)
        print(json.dumps({
            "version": 1,
            "origin": {
                "name": sys.argv[0],
                "module": "active-response"
            },
            "command": "check_keys",
            "parameters": {
                "keys": [unique_key]
            }
        }))
        sys.stdout.flush()

        # Đọc phản hồi từ wazuh-execd
        if params.input == '/dev/stdin':
            send_log('Waiting for manager response...')
            timeout_event = None
            try:
                timeout_event = json.loads(read_data(params.input))
            except ValueError:
                pass
            if timeout_event:
                send_log('Received : %s' % json.dumps(timeout_event))
                send_log('Manager says: %s' % timeout_event.get('command'))
                if timeout_event.get('command') == 'abort':
                    send_log('Aborted')
                    return 0
                elif timeout_event.get('command') != 'continue':
                    send_log('Invalid command')
                    return -1

        # Thực thi lệnh pfctl và kiểm tra mã lỗi (F9)
        res_add = subprocess.run(['/sbin/pfctl', '-t', '__wazuh_agent_drop', '-T', 'add', srcip], capture_output=True)
        subprocess.run(['/sbin/pfctl', '-k', srcip], capture_output=True)

        status = "SUCCESS" if res_add.returncode == 0 else "FAILED"
        send_log('Active response executed (add %s) [rule: %s] [status: %s]' % (srcip, rule_id, status))

    elif command == 'delete':
        res_del = subprocess.run(['/sbin/pfctl', '-t', '__wazuh_agent_drop', '-T', 'delete', srcip], capture_output=True)
        status = "SUCCESS" if res_del.returncode == 0 else "FAILED"
        send_log('Active response executed (delete %s) [status: %s]' % (srcip, status))
```

---

## IV. QUÁ TRÌNH TRIỂN KHAI & CÁC SỰ CỐ ĐÃ XỬ LÝ

Trong quá trình thực nghiệm, nhóm đã gặp và giải quyết tuần tự các sự cố hạ tầng:

1. **Đồng bộ mã nguồn sang OPNsense:**
   - File đã được cập nhật chuẩn xác tại:
     * `/usr/local/opnsense/scripts/wazuh/opnsense-fw` (Quyền `755`, `root:wheel`).
     * `/var/ossec/active-response/bin/opnsense-fw` (Quyền `750`, `root:wazuh`).
2. **Cơ chế ghép tên lệnh tự động của Wazuh Manager:**
   - Phát hiện: Wazuh tự động ghép tên lệnh trong thẻ `<name>` với số giây `<timeout>`. Khi khai báo `<name>opnsense-drop60</name>` cùng `<timeout>60</timeout>`, tên đăng ký bị biến thành `opnsense-drop6060`.
   - Khắc phục: Đổi tên định danh thành `<name>opnsense-drop</name>`, hệ thống tự ghép thành `opnsense-drop60` đúng thiết kế.
3. **Cơ chế nạp cấu hình trong Docker (Wazuh Single-Node):**
   - Cấu hình nguồn tại `/home/hagon/wazuh-docker/single-node/config/wazuh_cluster/wazuh_manager.conf` được đồng bộ trực tiếp vào volume dữ liệu sống tại `/var/lib/docker/volumes/single-node_wazuh_etc/_data/ossec.conf`.
   - Đảm bảo thẻ `<command>` phải nằm trước thẻ `<active-response>` để `wazuh-analysisd` không báo lỗi cú pháp.
4. **Khôi phục kết nối Agent (1514/TCP):**
   - Sửa địa chỉ Manager trong cấu hình OPNsense từ IP cũ (`192.168.56.107`) về IP chính thức (`192.168.56.10`), đưa Agent về trạng thái `Active`.

---

## V. KẾT QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC

### 5.1. Kích hoạt lệnh On-demand từ Wazuh Manager
Lệnh phát chủ động từ container Wazuh Manager trên máy Ubuntu:
```bash
docker exec -it single-node-wazuh.manager-1 /var/ossec/bin/agent_control -b 192.168.56.1 -f opnsense-drop60 -u 001
```
*Kết quả:* Trả về thông báo thành công: `Wazuh agent_control: Running active response 'opnsense-drop60' on: 001`.

> 📸 **[NOTE ẢNH 2: Chụp lệnh agent_control phát thành công trên máy Ubuntu]**  
> *(Chụp cửa sổ dòng lệnh Ubuntu khi chạy câu lệnh trên và nhận được thông báo Running active response).*

---

### 5.2. Nhật ký thực thi trên OPNsense (`/var/ossec/logs/active-responses.log`)
Trích xuất nhật ký thực tế ghi nhận tại thời điểm kiểm thử:

```text
2026/10/07 04:27:52 opnsense-fw: Started
2026/10/07 04:27:53 opnsense-fw: Received : {"version": 1, "origin": {"name": "", "module": "wazuh-execd"}, "command": "add", "parameters": {"extra_args": [], "alert": {"data": {"srcip": "192.168.56.1"}}}, "program": "active-response/bin/opnsense-fw"}
2026/10/07 04:27:53 opnsense-fw: Sending check_keys for: on-demand-192.168.56.1
2026/10/07 04:27:53 opnsense-fw: Waiting for manager response...
2026/10/07 04:27:53 opnsense-fw: Received : {"version": 1, "origin": {"name": "", "module": "wazuh-execd"}, "command": "continue", "parameters": {"extra_args": [], "alert": {"data": {"srcip": "192.168.56.1"}}}, "program": "active-response/bin/opnsense-fw"}
2026/10/07 04:27:53 opnsense-fw: Manager says: continue
2026/10/07 04:27:53 opnsense-fw: Active response executed (add 192.168.56.1) [rule: on-demand] [status: SUCCESS]
2026/10/07 04:28:53 opnsense-fw: Started
2026/10/07 04:28:53 opnsense-fw: Received : {"version": 1, "origin": {"name": "", "module": "wazuh-execd"}, "command": "delete", "parameters": {"extra_args": [], "alert": {"data": {"srcip": "192.168.56.1"}}}, "program": "active-response/bin/opnsense-fw"}
2026/10/07 04:28:53 opnsense-fw: Active response executed (delete 192.168.56.1) [status: SUCCESS]
```

> 📸 **[NOTE ẢNH 3: BẰNG CHỨNG QUAN TRỌNG NHẤT - Ảnh chụp log active-responses.log]**  
> *(Chèn bức ảnh log bạn vừa chụp lúc 11:29: thấy rõ mốc thời gian `04:27:53` add có fallback `on-demand-192.168.56.1` và đúng 60 giây sau `04:28:53` tự động gọi delete).*

---

### 5.3. Tác động lưu lượng thực tế trên máy Windows Host (`192.168.56.1`)
* **Tại `04:27:53`:** Khi lệnh `add` được thực thi, cửa sổ PowerShell chạy `ping -t 192.168.56.56` lập tức chuyển từ `Reply from...` sang `Request timed out`.
* **Tại `04:28:53` (Đúng 60 giây sau):** Khi lệnh `delete` tự động kích hoạt, luồng ping tự động phục hồi `Reply from 192.168.56.56: bytes=32 time=1ms TTL=64` mà **không cần bất kỳ thao tác can thiệp thủ công nào**.

> 📸 **[NOTE ẢNH 4: Chụp màn hình Ping trên Windows tự động ngắt và tự động thông suốt lại]**  
> *(Chụp cửa sổ PowerShell máy Windows hiển thị đoạn chuyển tiếp: đang ping thông -> bị Request timed out đúng 60 gói tin -> tự động nhận lại Reply).*

---

### 5.4. Xác nhận khép vòng phản hồi trên Wazuh Central (Closed-loop Alert trên Dashboard)
Sau khi OPNsense ghi nhận sự kiện thực thi kèm `[status: SUCCESS]`, Agent chuyển tiếp log qua khối `<localfile>` về Manager. Manager đối chiếu với Custom Rule **100050** và sinh Alert cảnh báo chính thức lên hệ thống phân tích.

* **Bản ghi Alert thu nhận trên Wazuh Dashboard (`192.168.56.10`):**
  - **Agent Name:** `OPNsense.internal`
  - **Location:** `/var/ossec/logs/active-responses.log`
  - **Full Log:** `2026/10/09 07:39:33 opnsense-fw: Active response executed (add 192.168.56.1) [rule: on-demand] [status: SUCCESS]`
  - **Rule Description:** `OPNsense Firewall: Successfully blocked IP via Active Response` (Rule ID: `100050`, Level 3)
  - **Manager Name:** `wazuh.manager`

> 📸 **[NOTE ẢNH 5: CỰC KỲ ĐẮT GIÁ - Chụp chi tiết Alert trên Wazuh Dashboard]**  
> *(Chèn bức ảnh chụp chi tiết sự kiện trên Wazuh Dashboard lúc 14:40: hiển thị rõ trường `agent.name: OPNsense.internal`, `full_log` có `[status: SUCCESS]`, và `rule.description: OPNsense Firewall: Successfully blocked IP via Active Response`).*

---

## VI. BÀI HỌC KINH NGHIỆM & RÚT KINH NGHIỆM KỸ THUẬT (LESSONS LEARNED)

Trong quá trình xây dựng Rule bắt sự kiện đóng vòng F9, nhóm đã rút ra các bài học kỹ thuật quan trọng khi tích hợp Wazuh với OPNsense:

1. **Phân biệt đúng định dạng dữ liệu đầu vào (Syslog Text vs JSON):**
   - *Vấn đề gặp phải:* Ban đầu khai báo `<decoded_as>json</decoded_as>` trong rule khiến Manager bỏ qua sự kiện, không sinh Alert.
   - *Nguyên nhân:* Mặc dù bản tin điều khiển truyền từ Manager xuống Agent dùng định dạng JSON, nhưng dòng log do script `opnsense-fw` ghi ra file `active-responses.log` là văn bản thuần định dạng Syslog (`YYYY/MM/DD HH:MM:SS opnsense-fw: ...`).
   - *Kinh nghiệm:* Với các log dạng text thông thường, không ép kiểu `<decoded_as>json</decoded_as>`, thay vào đó dùng trực tiếp thẻ `<match>` hoặc Regex `<regex>` để khớp nội dung chuỗi.
2. **Khai báo cú pháp XML nhóm luật (`<group>`):**
   - Trong Wazuh, một thẻ `<group name="...">` không được để trống (phải chứa ít nhất một thẻ `<rule>`). Khai báo nhóm rỗng sẽ gây lỗi biên dịch `Group without any rule` làm tê liệt engine phân tích log (`wazuh-analysisd`).
3. **Quy trình gỡ lỗi luật bằng công cụ chuẩn (`wazuh-logtest`):**
   - Khi viết Rule/Decoder mới, luôn kiểm tra giả lập bằng công cụ `wazuh-logtest` trước khi nạp vào hệ thống thực. Công cụ này cho phép đưa dòng log mẫu vào và kiểm tra trực tiếp luồng phân tích cú pháp (Phase 1: Pre-decoding $\rightarrow$ Phase 2: Decoding $\rightarrow$ Phase 3: Rule Match), giúp phát hiện ngay lỗi cú pháp mà không làm gián đoạn dịch vụ.

---

## VII. KẾT LUẬN & ĐỊNH HƯỚNG BƯỚC TIẾP THEO

1. **Khẳng định kết quả:**
   - **Lỗi F8 (Mất timeout On-demand) đã giải quyết triệt để 100%:** Lệnh chủ động từ Central có trạng thái (Stateful), kiểm soát được vòng đời (TTL 60s) và tự động hoàn nguyên lưu lượng.
   - **Khép vòng phản hồi F9 hoàn tất 100%:** Central phát lệnh $\rightarrow$ Agent thực thi dưới kernel PF $\rightarrow$ Agent gửi log $\rightarrow$ Manager bắt Rule 100050 và sinh Alert hiển thị trực quan trên Dashboard.
2. **Ý nghĩa kiến trúc đối với đề tài OTSD/OTSA (KC.01.04):**
   - Tận dụng tối đa cổng 1514 sẵn có để thiết lập đường ống điều khiển - phản hồi 2 chiều an toàn tuyệt đối cho phân vùng OT.
3. **Kế hoạch tiếp theo:**
   - Tiến hành mở rộng giao diện Web GUI OPNsense (`WazuhAgent.xml`): Bổ sung form cấu hình Whitelist IP (`skip_alias`), tham số dung lượng bộ đệm chống mất log khi đứt cáp (`client_buffer`), và chuẩn hóa các trường chứng chỉ CA/mTLS.
