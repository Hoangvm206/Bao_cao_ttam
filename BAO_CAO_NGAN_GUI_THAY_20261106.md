# Báo cáo tiến độ OTSA — 06/11/2026


## 1. Việc thầy giao — đợt 1

- **GUI Upgrade:** hoàn thành, đã kiểm giao diện.
- **Gộp OTSD Connection và Log Forwarding Agent:** hoàn thành.
- **Đổi cổng Connection:** giữ 8443 theo a Dương, long-polling tải rất nhẹ (mỗi thiết bị 1 kết nối chờ, khoảng 1 phút 1 phản hồi rỗng; dữ liệu chỉ chạy khi có phát hành), đổi cổng cũng không nhanh hơn. Máy nào trùng cổng thì đổi riêng: OTSD đặt DEVICE_PORT, OTSA sửa ô Port
- **Dùng chung cert OTSD cho Wazuh 1515:** Wazuh làm được, nhưng hiện thiết bị xin chứng chỉ OTSD bằng khoá agent Wazuh, nên phải đăng ký Wazuh trước. Nếu đăng ký Wazuh lại cần chứng chỉ OTSD thì máy mới bị kẹt vòng, chưa kể phải sửa cấu hình authd của manager.

## 2. Việc anh Dương — kênh mTLS v2

**Việc 6–11 đã triển khai và kiểm theo phạm vi lab:**

| Việc | Nội dung |
|---|---|
|6| Gói phần mềm qua v2, tải đủ/kiểm hash rồi cài hai bước |
|7| Báo phiên bản thực đang chạy qua X-OTSA-Running |
|8| Daemon đồng bộ state/file/report, tự chạy sau boot |
|9| Luật theo danh mục: PF, Suricata, blacklist |
|10| Chu kỳ telemetry theo cấu hình OTSD |
|11| Nhận/lưu model theo danh mục; chưa có AI loader |

Suricata đã nhận/nạp/thu hồi thật từ .25 và ACK. **Chưa nghiệm thu toàn bộ:** còn kiểm bộ PF/model thật và cài bundle cao hơn qua v2.

## 3. Việc thầy giao — thứ Năm

- **Mặc định 30 phút, người dùng được chỉnh:** chờ anh Dương trao đổi lại.
- **Truyền CSV firewall:** Dương xác nhận v2 dùng **rules.json theo danh mục firewall/pf**, không truyền CSV cũ. OTSA đã có chức năng nhận/kiểm/lưu JSON, apply/thu hồi/rollback; chưa kiểm bộ PF thật được giao từ .25.
- **Sửa theo báo cáo thầy và yêu cầu Dương ngày 05/11:** tiến độ các đợt như sau.

| Đợt | Nội dung | Đã hoàn thành đến đâu | Chưa làm / chưa nghiệm thu |
|---|---|---|---|
| P0 | Báo lỗi thật | Đã sửa, kiểm và lên .56; giữ lỗi nhiều dòng, lọc bí mật, tối đa 2000 ký tự; giữ FIFO/retry, không POST lặp. | Chưa kiểm failed report thật được .25 ACK. |
| P1 (A/B) | Chứng chỉ/định danh và phục hồi PF | Đã lên .56; kiểm cách ly đổi cert, pending/blocked/clock, rename; có PF recovery/quarantine/retention và Connection chung.07/11 sửa owner Wazuh, bootstrap IP, retry300s/tự phục hồi và TLS legacy, đã lên .56. | Dương đã đồng ý kiểm phối hợp cert/rename/pending/blocked active và PF reboot, chưa hẹn lịch. Còn kiểm cert_revoked→tự xin, retry5phút và tự nạp cert trên agent active với Dương. |
| P2 (C/D) | Cô lập lỗi và package retry | Đã lên .56; giữ mục lỗi đúng phạm vi, mục tốt tiếp tục; sửa version legacy/backoff; hồi quy và state/ACK thật đạt.07/11 đã lên .56 contract version nguyên văn/rỗng và errors snapshot; FIFO/retry đạt. | Malformed failed/errors mới kiểm cách ly; còn mixed PF thật .25, rejected0.3.2 thật và cài bundle cao hơn. |
| P3 (E) | Đổi endpoint, legacy→v2 | Công cụ review/confirm, archive outbox, quyền full-admin và guard writer legacy đã lên .56; kiểm cách ly đạt. | Chưa chuyển endpoint/cutover trên agent active hoặc kiểm API mutation qua phiên thật. |
| F | IPv6 và bản luật/model thấp hơn | IPv6 quản trị và policy /128 đã có; apply IPv6/mixed, packet in/out, giữ quản trị, rollback/thu hồi thật trên lab đạt. Đã sửa lỗi alias/NDP; 80 ca hồi quy sau sửa đạt, cleanup sạch. Luật/model 2.0.0→1.0.0 đạt cách ly. | Chưa assignment/report IPv6 đầu-cuối từ .25, reboot persistence và kiểm riêng RA/NDP packet. Model vẫn files-only, chưa AI loader. |
| G | Khóa ký và bộ phát hành | Đã có bộ mẫu/khóa thử lab. Tài liệu xác định OTSA/CI giữ khóa riêng, gửi public PEM cho OTSD kiểm chữ ký lúc nhập bundle. | Chưa có khóa chính thức/bundle hợp lệ để nghiệm thu phát hành; giữ các guard client hiện có. |

Các đợt P0/P1/P2/P3/F chưa commit/push. Kết quả lab không thay nghiệm thu production hoặc xác nhận của thầy/anh Dương.

## 4. Bổ sung a Dương ngày 07/11 — trạng thái sau sửa mục1–3

| Mục mới | Cần làm / trạng thái |
|---|---|
| N07-1 | Đã sửa/lên .56; root640/wazuh640 và reject write/symlink đạt native với file thử. |
| N07-2 | Đã sửa/lên .56; CA pin/IP SAN đạt TLS loopback thật, IPv6 probe còn mock; chưa bootstrap lại agent active. |
| N07-3 | Đã lên .56: trang cũ về Connection, inventory giữ khi selection sai, API/backend cấm Mock files. Chưa HTTP session/GUI mutation thật. |
| N07-4 | Blacklist rỗng, chưa từng có alias/table phải no-op. Chưa kiểm ca này; kết quả IPv6 F trước không bao phủ. |
| N07-5 | PF giữ nguyên nhân gốc và kiểm interface trước nạp, vẫn rollback cả bộ. Cần bổ sung. |
| N07-6 | PF pending cùng payload giữ lý do probe, không reset deadline. Chưa sửa. |
| N07-7 | Activity hiển thị mã/lý do đã lọc bí mật thay vì chỉ Failed. Chưa sửa. |


## 5. Thứ tự làm nốt đã gộp 07/11

1. **Đã sửa/lên .56:** enrollment/cert; còn kiểm active với Dương.
2. **Đã sửa/lên .56:** report contract mới; malformed/rejected còn cách ly.
3. **Đã sửa/lên .56:** Connection/TLS cũ, inventory/Mock files; probe thật đạt.
4. **Việc sửa tiếp theo:** PF/blacklist: empty no-op, giữ lỗi gốc, pending/deadline, retention.
5. Activity: hiện mã/chi tiết lỗi đã lọc; từng gói đạt thì backup/triển khai .56.
6. Phối hợp a Dương: kiểm cert/rename/pending/blocked active ổn trước, rồi PF reboot.
7. Kiểm assignment thật còn thiếu: PF, mixed state, IPv6, luật/model bản thấp hơn.
8. Khóa/bundle chính thức và cài bản cao hơn khi có đủ điều kiện/cho phép.


