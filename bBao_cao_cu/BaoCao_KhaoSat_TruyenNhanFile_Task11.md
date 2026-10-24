# BÁO CÁO KHẢO SÁT TOÀN DIỆN CƠ CHẾ TRUYỀN & NHẬN FILE TỪ TRUNG TÂM (WAZUH CENTRAL) XUỐNG THIẾT BỊ BIÊN (OPNSENSE/OTSA)

| Thông tin | Chi tiết |
|---|---|
| **Giai đoạn** | Khảo sát & Đánh giá thực nghiệm cơ chế truyền nhận file phục vụ cấu hình, luật IDS và mô hình AI |
| **Môi trường lab** | • **Thiết bị biên (OTSA):** OPNsense VM (`192.168.56.56`) — Wazuh Agent v4.14.7 (FreeBSD 14.x)<br>• **Trung tâm (OTSD):** Ubuntu Server `otsd-server` (`192.168.56.10`) — Cụm Wazuh Central v4.14.7 Docker (Single-Node)<br>• **Máy trạm kiểm thử:** Windows Host (`192.168.56.1`) |

---

## I. MỤC TIÊU & BỐI CẢNH NHIỆM VỤ
1. **Tạm hoãn thiết kế GUI** để tập trung giải quyết bài toán hạ tầng truyền thông tầng dưới.
2. **Khảo sát toàn diện & kiểm chứng thực nghiệm bằng số liệu thật** cơ chế truyền & nhận file từ Wazuh Central xuống OPNsense/OTSA, trả lời các câu hỏi:
   - Cơ chế phân phối file có sẵn của Wazuh gốc (`merged.mg`, WPK) hoạt động ra sao?
   - Giới hạn kỹ thuật nằm ở đâu (kích thước, định dạng file nhị phân vs văn bản, rủi ro an ninh)?
   - Có đáp ứng được việc truyền tải tập luật Suricata (~50MB) và mô hình AI (~200MB) trong mạng OT hay không?

---

## II. Thực nghiệm

 Thiết lập môi trường cô lập và thực hiện đo kiểm thực tế trên lab, thu được **5 phát hiện**:

### 1. Cô lập nhóm kiểm thử (`ot_test_group`)
* Để tránh làm ảnh hưởng đến nhóm `default`, nhóm đã tạo nhóm riêng `ot_test_group` trên Manager và gán Agent `001` (`OPNsense.internal`) vào nhóm này.
* Lệnh xác thực: `/var/ossec/bin/agent_groups -c -i 001`.
---

### 2. Bắt gói trên dây bằng `tcpdump` chứng minh cổng giao tiếp (Phê bình 8)
* **Thực nghiệm:** Khởi chạy `tcpdump -i vtnet1 -nn -s 0 "host 192.168.56.10" -c 30 -w /tmp/wazuh_file_transfer.pcap` trên OPNsense trong lúc đồng bộ file.
* **Số liệu đo được:**
  - `192.168.56.10.1514` (Manager) $\longleftrightarrow$ `192.168.56.56.10996` (OPNsense client TCP socket).
  - Hoàn toàn **không xuất hiện cổng 1515** (chỉ dành cho Authd lúc đăng ký), không có SSH/SCP hay cổng phụ nào khác.
* **Kết luận:** Quá trình truyền `merged.mg` diễn ra **độc quyền 100% trên cổng 1514 (TCP)**.

> ![alt text](image.png)
> *(Ảnh trích xuất file pcap: các dòng gói tin trao đổi cờ [P.], seq/ack giữa IP 56.10 cổng 1514 và 56.56 cổng 10996).*

---

### 3. Phát hiện xung đột: `wazuh-agentd` Reload nhưng `wazuh-execd` Restart (Ảnh hưởng F8) (Phê bình 7)
* **Thực nghiệm:** Theo dõi PID của 2 tiến trình trọng yếu trên OPNsense trước và sau khi nhận file:
  - Trước khi nhận file: `wazuh-agentd` có PID **`63709`** (user `wazuh`), `wazuh-execd` có PID **`9227`** (user `root`).
  - Sau khi nhận file: `wazuh-agentd` nhận `SIGNAL [(30)...] Reload agentd` $\rightarrow$ **PID 63709 giữ nguyên** (Nạp lại cấu hình, không restart).
  - **NHƯNG `wazuh-execd` bị RESTART:** PID đổi từ `9227` $\rightarrow$ `90871` $\rightarrow$ `28950`!
* **Nguyên nhân:** Tệp `merged.mg` mang theo file `ar.conf`. Khi `ar.conf` thay đổi, hệ thống buộc phải khởi động lại `wazuh-execd` để nạp các định nghĩa Active Response mới.
* **Tác động kỹ thuật đến F8:** Daemon `wazuh-execd` lưu danh sách đếm ngược 60s (`timeout_list`) trong RAM. Việc restart làm **xóa sạch timer đang chạy**, có nguy cơ khiến IP bị kẹt chặn vĩnh viễn nếu lệnh on-demand phát ra trùng thời điểm Manager đẩy file cấu hình.

> ![alt text](image-1.png) | ![alt text](image-3.png)
![alt text](image-2.png)
> *(Ảnh chụp lệnh `ps aux | grep -E 'wazuh-agentd|wazuh-execd'` kèm log `SIGNAL 30 Reload agentd`).*

---

### 4. Bóc tách cơ chế Allowlist: File Nhị phân (AI) bị chặn 100%, File Text (Suricata) được nạp (Phê bình 2 & 7)
* **Thực nghiệm với File Nhị phân (Binary):**
  - Tạo các file 10KB, 50KB, 100KB, 1MB bằng dữ liệu `/dev/urandom`.
  - Kết quả: `wazuh-remoted` lập tức loại bỏ toàn bộ và ghi log:
  ![alt text](<Screenshot 2026-10-12 221338.png>)
  - **Ý nghĩa:** Wazuh Manager có bộ lọc kiểm tra ký tự nhị phân / null byte (`\0`). **Các file mô hình AI nhị phân (.bin, .onnx, weights 200MB) HOÀN TOÀN KHÔNG THỂ truyền qua cơ chế này.**
* **Thực nghiệm với File Văn bản (Plain-text Rules):**
  - Tạo 2 file luật Suricata chuẩn ASCII: `suricata_test_100k.txt` (100KB) và `suricata_test_1m.txt` (1.0MB).
  - Kết quả: File `merged.mg` trên Manager tăng từ **424 bytes lên 1.1MB** mà không gặp bất kỳ lỗi `Invalid shared file` nào!

> ![alt text](<Screenshot 2026-10-12 221649.png>)
> *(Ảnh chụp log `ERROR: Invalid shared file` đối với file urandom và ảnh `ls -lh` thấy `merged.mg` đạt 1.1M).*

---

### 5. Phát hiện sự cố Socket (Connection Reset) & Khoảng mù an ninh 20 giây
* **Thực nghiệm trên OPNsense khi kéo file 1.1MB:**
  - OPNsense nhận và giải nén thành công `suricata_test_100k.txt` và `suricata_test_1m.txt` vào `/var/ossec/etc/shared/`.
  - **Sự cố ghi nhận ngay sau đó trong `ossec.log`:**
    ```text
    2026/10/12 15:15:50 wazuh-agentd: ERROR: Connection socket: Connection reset by peer (54)
    2026/10/12 15:15:50 wazuh-agentd: ERROR: (1137): Lost connection with manager. Setting lock.
    2026/10/12 15:15:50 wazuh-modulesd: WARNING: Process locked due to agent is offline. Waiting for connection...
    ...
    2026/10/12 15:16:10 wazuh-agentd: INFO: (4102): Connected to the server ([192.168.56.10]:1514/tcp).
    2026/10/12 15:16:10 wazuh-modulesd: INFO: Agent is now online. Process unlocked, continuing...
    ```
* **Đánh giá rủi ro an ninh OT:**
  - Ngay cả ở mức **1.1MB**, việc truyền stream trên socket TCP 1514 đã làm nghẽn luồng điều khiển, dẫn tới **`Connection reset by peer (54)`**.
  - Agent rơi vào trạng thái **OFFLINE kéo dài đúng 20 giây** (từ `15:15:50` đến `15:16:10`). Toàn bộ module bị khóa (`Process locked`), tạo ra một **khoảng mù an ninh (Security Blind-spot)** mà trong thời gian này các cảnh báo tấn công mạng OT không thể gửi về trung tâm!

> ![alt text](<Screenshot 2026-10-12 221822.png>) 
> *(Ảnh chụp `ls -lh` thấy file 1.1M và log `ERROR: Connection reset by peer (54)` kèm `Process locked due to agent is offline`).*

---

## III. BẢNG TỔNG HỢP SỐ LIỆU ĐO KIỂM THỰC TẾ (ĐỢT 1 - 12/10/2026)

| Thử nghiệm | Loại dữ liệu | Kích thước | Kết quả đóng gói Manager | Kết quả nhận trên OPNsense | Thời gian Offline / Sự cố |
|---|---|---|---|---|---|
| **Test Baseline** | Plain-text (`test_file.txt`) | 24 Bytes | Thành công (`merged.mg` = 424B) | Nhận thành công, bóc tách chuẩn | **0 giây** (Không rớt mạng) |
| **Test Binary 1** | Random Binary (`/dev/urandom`) | 10 KB - 100 KB | **Bị từ chối** (`Invalid shared file`) | Không nhận | Không ảnh hưởng |
| **Test Binary 2** | Random Binary (`test_1mb.bin`) | 1.0 MB | **Bị từ chối** (`Invalid shared file`) | Không nhận | Không ảnh hưởng |
| **Test Suricata Text** | ASCII Rules (`100K + 1M`) | **1.1 MB** | **Thành công** (`merged.mg` = 1.1MB) | Nhận thành công, bóc tách chuẩn | **Rớt mạng 20 giây** (`Connection reset`, Offline từ 15:15:50 đến 15:16:10) |

---

## IV. BẢNG SO SÁNH CÁC PHƯƠNG ÁN TRUYỀN FILE TRONG MẠNG OT

 bảng so sánh đa chiều giữa 5 phương án:

| Tiêu chí | 1. Wazuh Shared (`merged.mg`) | 2. Gói WPK Wazuh | 3. Cơ chế Rule Fetch có sẵn của OPNsense IDS | 4. rsync / SFTP qua SSH | 5. Kiến trúc đề xuất: Active Response + HTTPS (mTLS) |
|---|---|---|---|---|---|
| **Kênh truyền & Cổng** | Kênh sự kiện Cổng 1514 (TCP). | Cổng 1514 (TCP). | HTTPS Cổng 443 ra Repo luật (chuẩn OPNsense). | Cổng 22 (SSH). | **Control:** Cổng 1514 (AR), **Data:** HTTPS Cổng 8443 (mTLS). |
| **Hỗ trợ File lớn (50MB - 200MB)** | **Kém:** Nghẽn socket, gây rớt mạng 20s ngay từ 1.1MB. | **Kém:** Thiết kế riêng cho nâng cấp Agent binary. | **Rất tốt:** Tải mượt mà qua HTTP/HTTPS. | **Rất tốt:** Tối ưu truyền file lớn. | **Rất tốt:** Truyền luồng riêng qua HTTPS, có resume, không nghẽn 1514. |
| **Hỗ trợ Mô hình AI nhị phân** | **Không thể:** Bị chặn bởi bộ lọc binary. | **Không thể:** Phải đóng gói thành binary nâng cấp. | **Không thể:** OPNsense IDS chỉ hiểu file luật Suricata. | **Tốt:** Truyền mọi loại file. | **Rất tốt:** Hỗ trợ mọi định dạng file (rules, model AI, weights). |
| **Hỗ trợ FreeBSD / OPNsense** | Có sẵn. | **Không hỗ trợ chính thức:** WPK chỉ có cho Linux, Win, macOS. FreeBSD là bản build cộng đồng. | Có sẵn trên OPNsense (chỉ cho Suricata). | Cần mở SSH port 22 vào OPNsense (vi phạm bảo mật OT). | **Hoàn toàn tương thích:** Tận dụng Python/fetch có sẵn trên FreeBSD. |
| **Xác thực & Chữ ký số** | Chỉ có MD5 (lỗi thời, không có chữ ký). | Có chữ ký RSA-SHA256 với Root CA. | Kiểm tra mã băm MD5/SHA256 của tập luật OPNsense. | Phụ thuộc SSH Key. | **Chữ ký số Ed25519 offline** + Checksum SHA-256 + mTLS hai chiều. |
| **Tự động áp dụng & Khép vòng F9** | Tự bóc tách nhưng lưu cố định tại `shared/`. | Tự chạy script upgrade. | Phải kích hoạt thủ công hoặc cron job OPNsense. | Phải viết thêm script cron. | **Tự động 100%:** Nhận lệnh $\rightarrow$ Tải $\rightarrow$ Verify $\rightarrow$ Atomic move $\rightarrow$ Sinh Alert 100050 lên Dashboard. |

---

## V. ĐÁNH GIÁ MỞ RỘNG VỀ GIỚI HẠN CỦA WPK VÀ NGUY CƠ NGHẼN CẢNH BÁO

### 1. Khảo sát cơ chế nâng cấp gói WPK (Wazuh Signed Package) trên OPNsense
* **Tài liệu chính thức từ Wazuh:** 
  - Cơ chế WPK (`packages.wazuh.com/4.x/wpk/`) được thiết kế riêng cho việc nâng cấp Agent từ xa thông qua các định dạng gói dựng sẵn: Linux (`.deb`, `.rpm`), Windows (`.msi`), macOS (`.pkg`).
  - Nền tảng **FreeBSD / HardenedBSD (hệ điều hành gốc của OPNsense)** là bản cài đặt cộng đồng (FreeBSD Ports/Packages: `security/wazuh-agent`), **hoàn toàn KHÔNG được hỗ trợ kho WPK chính thức từ Wazuh**.
* **Thực nghiệm điều khiển từ Manager:**
  - Khi phát lệnh nâng cấp từ xa từ Wazuh Manager xuống OPNsense:
    ```bash
    /var/ossec/bin/agent_upgrade -a 001
    # hoặc gọi qua Wazuh RESTful API: PUT /agents/001/upgrade
    ```
  - Wazuh Manager trả về thông báo từ chối chính thức:
    ```text
    ERROR: (1743): Cannot upgrade agent 001. The agent's platform is not supported: FreeBSD.
    ```
* **Kết luận:** Cơ chế WPK hoàn toàn không tương thích với môi trường OPNsense, không thể áp dụng để cập nhật phần mềm cũng như phân phối file cho thiết bị OTSA.

---

### 2. Phân tích hiện tượng Nghẽn cảnh báo (Head-of-Line Blocking) và Ngưỡng tới hạn (Breaking Point)
* **Bản chất kỹ thuật của hiện tượng sụp đổ kết nối:**
  - Kênh truyền cổng 1514 (TCP) của Wazuh sử dụng giao thức độc quyền (OSSEC Protocol) tối ưu hóa cho các dòng bản tin sự kiện ngắn và đều đặn (vài chục bytes/bản tin).
  - Khi nhồi nhét một dòng dữ liệu lớn (Stream 1.1MB của tập luật) vào cùng socket này, bộ đệm truyền nhận bị bão hòa, dẫn tới vi phạm timeout và kích hoạt sự kiện sụp kết nối `Connection reset by peer (54)`.
* **Hậu quả mất an toàn nghiêm trọng (Khoảng mù an ninh):**
  - Trong suốt 20 giây Agent rơi vào trạng thái mất kết nối (`Lost connection with manager. Setting lock`), tiến trình `wazuh-modulesd` bị khóa (`Process locked`).
  - Toàn bộ các cảnh báo tấn công mạng OT phát sinh trong khoảng thời gian này bị tắc nghẽn, không thể đẩy về trung tâm điều hành SIEM/SOC. 
* **Đánh giá về thang đo kích thước cao hơn (5MB, 10MB, 25MB, 50MB):**
  - Số liệu thực nghiệm ở ngưỡng 1.1MB đã xác lập rõ ràng giới hạn tới hạn của socket. Việc tiếp tục đẩy file 5MB hay 50MB chỉ làm kéo dài thời gian offline hoặc khiến kết nối bị hủy vĩnh viễn.
  - Kết quả đợt 1 đã cung cấp đầy đủ 100% bằng chứng kỹ thuật để loại bỏ hoàn toàn ý tưởng truyền file dữ liệu lớn qua cổng 1514.

---

## VI. KẾT LUẬN & ĐỀ XUẤT KIẾN TRÚC HOÀN THIỆN 

### 1. Kết luận từ khảo sát thực nghiệm
1. **Cơ chế `merged.mg` (Cổng 1514):**
   - Không hỗ trợ file nhị phân (chặn 100% mô hình AI qua cơ chế allowlist).
   - Truyền file văn bản trên 1MB gây sốc socket, làm đứt kết nối và tê liệt cảnh báo an ninh suốt 20 giây.
   - Quá trình nạp file làm khởi động lại `wazuh-execd`, xóa sạch danh sách timer của Active Response, gây xung đột trực tiếp với nhiệm vụ F8/F9.
2. **Cơ chế WPK:** Không hỗ trợ hệ điều hành FreeBSD của OPNsense.

### 2. Kiến trúc giải pháp đề xuất: Mô hình 2 kênh độc lập (Dual-Channel Architecture)
Từ các phát hiện trên, đề xuất mô hình phân tách chức năng rõ rệt, kết hợp chặt chẽ giữa OPNsense và Wazuh:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TRUNG TÂM (OTSD / WAZUH)                        │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
     [ KÊNH ĐIỀU KHIỂN & GIÁM SÁT ]        [ KÊNH TRUYỀN DỮ LIỆU & GÓI ]
         Wazuh Agent Protocol                 HTTPS Pull qua mTLS
              Cổng 1514/TCP                       Cổng 8443/TCP
                   │                                 │
                   ▼                                 ▼
┌──────────────────┴─────────────────────────────────┴───────────────────┐
│                     THIẾT BỊ BIÊN OTSA (OPNSENSE)                      │
│                                                                        │
│  • Tiếp nhận lệnh Active Response          • Kéo tập luật IDS (V3)     │
│  • Đẩy Log/Alert về SIEM thời gian thực    • Kéo IP Blacklist (V4)     │
│  • Giữ kết nối ổn định (không nghẽn)       • Kéo luật tường lửa (V5)   │
│                                            • Kéo gói phần mềm (.pkg)   │
└────────────────────────────────────────────────────────────────────────┘
```

* **Kênh Dữ liệu (Data Channel):** Thiết lập luồng HTTPS độc lập kết hợp xác thực chứng chỉ số hai chiều (mTLS). Thiết bị OTSA đóng vai trò chủ động kéo dữ liệu khi cần:
  - Tải tập luật Suricata IDS (~50MB) và mô hình AI (~200MB), có hỗ trợ resume và nén stream.
  - Toàn bộ dữ liệu được ký số ngoại tuyến (Offline Signing) bằng cặp khóa bất đối xứng và kiểm tra mã băm SHA-256 trước khi giải nén.
  - Tích hợp cơ chế khôi phục ZFS Boot Environment (BE) để đảm bảo đường lùi an toàn tuyệt đối khi bản cập nhật gặp sự cố.

