# Kịch bản demo ngày 24/10/2026 — đưa file vào trung tâm thử, OTSA tải qua mTLS

Mục tiêu: Hoàng tự chạy được từng bước, diễn tập trước rồi khôi phục để trình bày lại. Kịch bản chính chứng minh tải luật Suricata và danh sách IP qua hai bộ tải Core thật, nhận đúng dữ liệu mới và giữ dữ liệu cũ khi file không hợp lệ.

Đọc bảng đối chiếu đủ 6 việc trong `DOI-CHIEU-6-VIEC.md`. Bài demo trực tiếp tập trung Việc 3 và phần dùng chứng chỉ của Việc 2. Những ca Việc 1/4/5/6 có bằng chứng riêng; không gọi bài này là chạy lại đầy đủ nghiệm thu 6 việc.

## 1. Máy nào, file nào, luồng nào?

Chỉ dùng VM local **192.168.56.56**, hostname `OPNsense.internal`, SSH qua `127.0.0.1:2222`. Script không nhận tham số đổi máy. Không truy cập `.35`, `.36` hoặc OTSD thật.

```text
Windows của Hoàng
  │  publish: chép 4 file mẫu qua SSH
  ▼
Kho file của OTSD thử trên VM local
  │  HTTPS mTLS 127.0.0.1:8443/otsa
  ├── Suricata downloader → kiểm hash + cú pháp → cache và CSDL luật native
  └── URI URL Table       → kiểm hash + IP     → bảng alias PF
```

OTSD thử và OTSA cùng nằm trên VM local, giao tiếp qua loopback. Hai vai trò tách biệt trong demo, không phải hai máy vật lý hoặc OTSD thật.

| File gửi lên kho thử | Thành phần nhận | Dấu hiệu cần nhìn thấy |
|---|---|---|
| `otsd-firewall.rules` | Suricata, nguồn firewall | SID 9900001, cổng 502 |
| `otsd-detection.rules` | Suricata, nguồn detection | SID 9900002, cổng 102 |
| `otsd-blacklist.txt` | URI → `OTSD_BLACKLIST` | 203.0.113.7 và 198.51.100.0/24 |
| `otsd-whitelist.txt` | URI → `OTSD_WHITELIST` | 192.0.2.10 |

Hai luồng nhưng bốn file dữ liệu để đúng yêu cầu hai nguồn Suricata và blacklist/whitelist của anh Dương. Script tự tạo thêm manifest, SHA256 và version.txt cho mỗi loại. Không phải chỉ hai file là đủ cho toàn bộ Việc 3.

Máy chủ thử trong bộ này phục vụ cùng các đường dẫn cần dùng của `otsd-thu`, có thêm manifest/header phù hợp adapter hiện hành. Không chạy nguyên xi toàn bộ script cũ và không dùng nó làm OTSD production. TLS buộc gửi chứng chỉ client và kiểm CA/SAN thật; không có `verify=False`.

## 2. Chuẩn bị trước buổi trình bày

1. Bật VM local đã có trong VirtualBox. Nếu đang bật thì giữ nguyên, không provision hoặc cài lại.
2. Mở PowerShell trên Windows. Mở trình duyệt vào **https://192.168.56.56** và đăng nhập tài khoản lab đang có. Không dùng URL `.35`/`.36`.
3. Mở sẵn hai màn hình chỉ để xem:
   - IDS/IPS hoặc Intrusion Detection → **Rules**, tìm SID. Có thể vào `/ui/ids`, chọn Rules. Bỏ bộ lọc chỉ hiện luật enabled nếu không thấy SID.
   - Firewall → Diagnostics → **Aliases**, chọn bảng `OTSD_BLACKLIST` hoặc `OTSD_WHITELIST`; đường dẫn native `/ui/firewall/alias_util/`.
4. Không bấm Apply, Download & Update, bật IDS hoặc sửa cấu hình trên web trong lúc script đang demo. Chỉ tải lại trang để xem. Script theo dõi hash cấu hình; thay đổi ngoài bài sẽ làm nó dừng để tránh ghi đè.

Trong PowerShell:

```powershell
Set-Location 'C:\work\opnsense\KichBan_Demo_OTSD_2026-10-24'
.\Demo.ps1 -Step preflight
```

Kết quả mong đợi: LAN `.56`, hai nguồn OTSD, IDS/PF loader/package worker đều `false`. Nếu kiểm tra lỗi thì dừng, không đổi máy đích để cố chạy.

SSH dùng private key Vagrant có sẵn và kiểm host key đã lưu; không cần nhập mật khẩu. Nếu host key thay đổi, không xóa/bỏ kiểm host key để vượt lỗi.

## 3. Diễn tập một lần trước

Lệnh này chạy toàn bộ các bước, sau đó tự khôi phục dù một bước thất bại:

```powershell
.\Rehearse.ps1
```

Nếu báo dữ liệu demo cũ còn tồn tại và vòng trước đã khôi phục thành công, chạy:

```powershell
.\Demo.ps1 -Step archive
.\Rehearse.ps1
```

Cuối lượt phải có `REHEARSAL PASSED` và kết quả restore đều true. Sau đó cất log lượt diễn tập để chuẩn bị lần trình bày:

```powershell
.\Demo.ps1 -Step archive
```

`archive` chỉ cất dữ liệu/log demo đã khôi phục, không reset VM, không thay gói hay hệ thống. Không dùng nó thay cho restore.

## 4. Lần trình bày: chạy từng bước, dừng để giải thích và chụp ảnh

Dự kiến dành 10–15 phút để thao tác, nói và chụp hình. Tốc độ máy có thể khác lần diễn tập.

### Bước A — dựng trung tâm thử và chứng chỉ lab

```powershell
.\Demo.ps1 -Step prepare
.\Demo.ps1 -Step start
```

Script sao lưu trạng thái, sinh CA/server/device **thử** và tạm chọn cặp CA/chứng chỉ thiết bị trong **System Trust**. Server chỉ mở `127.0.0.1:8443`. Identity enrollment đang có không bị thay. Cấu hình trước demo được giữ để restore.

Nhìn kết quả: `started: true`, `uses_system_trust: true`, `engine_started: false`.

Nói: “Đây là trung tâm mô phỏng. Thiết bị và máy chủ xác thực hai chiều bằng chứng chỉ thử. Bài này dùng chứng chỉ cấp sẵn cho lab, không demo lại giao thức tự xin chứng chỉ v2.”

### Bước B — đưa file từ Windows lên kho trung tâm thử

```powershell
.\Demo.ps1 -Step publish
```

Bốn file nguồn nằm trong `sample-files` ngay cạnh script. Lệnh đọc byte từ Windows, gửi qua SSH tới đúng bốn đường dẫn trong kho thử, rồi tạo manifest/hash/version. Kết quả có `uploaded_from_windows: true`, tên file, số byte và SHA256.

**Chụp ảnh 1:** PowerShell hiện bốn file đã chép lên và mã băm.

Nói: “Đây là đưa file vào kho trung tâm bằng SSH để mô phỏng vận hành. Phía OTSD thật chưa phối hợp đầu upload, nên chưa tuyên bố đã có API hay giao diện upload OTSD.”

### Bước C — OTSA tải xuống bằng hai bộ tải native

```powershell
.\Demo.ps1 -Step pull
.\Demo.ps1 -Step status
```

`pull` thực sự chạy `suricata/rule-updater.py`, `suricata/installRules.py` và `filter/update_tables.py` của VM. Không thay các lệnh này bằng hàm giả. Chứng chỉ lấy qua helper System Trust bình thường, không thay hàm lấy credential trong tiến trình.

Kết quả mong đợi:

- `native_update: PASS`, `installer: PASS`.
- `peer_cns` có `OPNsense.internal`; request ghi `/files/...`, status 200.
- Blacklist có hai mục đầu, whitelist có `192.0.2.10`.
- Trang Rules sau khi tải lại có SID 9900001 và 9900002. Script đã dựng CSDL luật native, **chưa bật engine**.

**Chụp ảnh 2:** log mTLS hiện CN thiết bị và request file.

**Chụp ảnh 3:** Rules có SID 9900001/9900002; bảng alias có đúng IP.

Nói: “Thiết bị tự kéo file, kiểm hash trước khi nhận. Luật đã vào cache/CSDL luật và IP đã vào bảng alias. Chưa phát lưu lượng để chứng minh Suricata đang cảnh báo/chặn.”

### Bước D — không đổi phiên bản thì không tải lại luật

```powershell
.\Demo.ps1 -Step same
```

Phải thấy `same_version: PASS`, `rules_not_redownloaded: true`, `hash_and_mtime_unchanged: true`. Việc hỏi manifest/version vẫn có thể phát sinh; không nhầm nó với tải lại file luật.

### Bước E — đổi riêng nguồn detection

```powershell
.\Demo.ps1 -Step detection
```

Kho thử thêm SID **9900003**, detection thành `1.0.1 demo`; firewall vẫn `1.0.0 demo`. Script cập nhật bằng bộ tải native.

Phải thấy `independent_version: PASS`, `unchanged_source: firewall`. Hash và mtime file luật firewall giữ nguyên. Tải lại trang Rules, tìm 9900003.

**Chụp ảnh 4:** SID mới và kết quả nguồn firewall giữ nguyên.

### Bước F — đổi riêng nguồn firewall

```powershell
.\Demo.ps1 -Step firewall
```

Thêm SID **9900004**, nguồn firewall thành `1.0.1 demo`; detection giữ nguyên. Phải thấy `unchanged_source: detection`.

Không nhầm file Suricata `otsd-firewall.rules` với bộ nạp các luật Firewall › Rules của Việc 4: chúng là hai thành phần khác nhau.

### Bước G — cập nhật danh sách IP

```powershell
.\Demo.ps1 -Step ips
```

Thêm **203.0.113.88** vào blacklist. Bảng `OTSD_BLACKLIST` phải có ba mục; whitelist giữ `192.0.2.10`.

Phiên bản nhóm firewall thành `1.0.2 demo`. Vì các file cùng nhóm firewall dùng chung version, bộ tải Suricata có thể tải lại file luật firewall dù nội dung luật không đổi. Đây là hành vi dự kiến, không phải lỗi độc lập giữa detection và firewall.

**Chụp ảnh 5:** bảng alias hiện IP mới. Không cần phát gói hoặc tạo thêm luật chặn để chứng minh bước tải IP.

### Bước H — chứng minh từ chối dữ liệu sai

```powershell
.\Demo.ps1 -Step negative
```

Script chạy các ca:

| Ca | Kết quả mong đợi |
|---|---|
| Kết nối HTTPS thiếu chứng chỉ client | TLS từ chối |
| File detection bị sửa nhưng hash manifest không đổi | Native updater trả mã lỗi; cache luật cũ giữ nguyên |
| Blacklist sai hash | Bảng alias và cache địa chỉ cũ giữ nguyên |
| Blacklist có IP không hợp lệ, hash vẫn đúng | Bảng/cache cũ giữ nguyên |
| Blacklist rỗng, hash vẫn đúng | Bảng/cache cũ giữ nguyên |

Phải thấy các cờ từ chối true và `native_uri_rejections` đủ ba ca. Native alias có thể trả status chung “ok” vì dùng lại dữ liệu cũ; kịch bản đối chiếu bảng/cache thật, không dùng riêng mã thoát để kết luận tải thành công.

Ca thiếu client chứng minh chính sách mTLS của server bằng kết nối không có cert; không xóa chứng chỉ khỏi System Trust để ép bộ tải native chạy.

**Chụp ảnh 6:** kết quả từ chối và bảo toàn dữ liệu cũ.

### Bước I — chốt log và khôi phục

```powershell
.\Demo.ps1 -Step status
.\Demo.ps1 -Step restore
```

Restore phải có các cờ true:

- `config_core_cron_repo_settings_unchanged`.
- `inventory_unchanged`.
- `pf_rules_and_tables_restored`.
- `temporary_private_keys_removed`.

Nội dung cache luật/CSDL và file cache alias cũng được so với bản sao lưu. Server tắt, System Trust/config trả về trước bài, file khóa thử do bài tạo được dọn. IDS vẫn tắt; không cài gói hoặc reboot.

**Chụp ảnh 7:** kết quả khôi phục. Lúc này refresh web sẽ thấy lại dữ liệu baseline, không còn SID mới 9900003/9900004 của demo.

Sau khi đã lưu ảnh, có thể chạy `archive` để sẵn sàng cho lần sau. Toàn bộ log PowerShell ở thư mục `logs` trên Windows; dữ liệu công khai/log mock được giữ trong `history` trên VM. Không sao chép config backup hay private key ra ngoài.

## 5. Nếu lỡ đóng PowerShell hoặc lỗi giữa chừng

Mở lại PowerShell tại thư mục bài và chạy:

```powershell
.\Demo.ps1 -Step restore
```

Nếu script báo `Config changed outside demo; STOP`, không chép đè config bằng tay. Giữ log và báo lại vì có thay đổi ngoài bài; cần đối chiếu trước khi phục hồi. Không dùng snapshot/BE để tự hoàn tác cả máy.

Không bấm các bước đổi phiên bản nhiều lần liên tiếp trong cùng vòng vì chúng được thiết kế chạy theo thứ tự. Muốn làm lại: restore → archive → start → publish → pull.

## 6. Nói gì khi được hỏi “đã thông đến đâu?”

“Em đã mô phỏng đưa bốn file vào kho trung tâm, thiết bị tải qua mTLS bằng bộ tải native Suricata và URL Table. Đổi phiên bản từng nguồn có hiệu lực độc lập; file sai hash hoặc danh sách IP lỗi không thay dữ liệu tốt đang có. Đây là lab local, chưa phải OTSD production; đầu upload OTSD thật chưa được nối. Bài này chưa bật IDS để chứng minh cảnh báo/chặn, chưa chạy lại nâng gói hoặc sets.”

Chưa có cơ sở nói “toàn bộ luồng production đã đạt”, “Wazuh mTLS đã đạt” hoặc “ba hook thật trên .36 đã xử lý xong”. Kịch bản local không thay thế điểm còn thiếu trên .36.
