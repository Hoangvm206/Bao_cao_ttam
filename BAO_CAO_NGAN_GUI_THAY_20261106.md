# Báo cáo tiến độ OTSA — 06/11/2026

**Kết nối cuối lượt07/11:** sau ACK thật/idle125s đạt, TCP .56→.25:8443
timeout trở lại; v2 giữ last_error=state_timeout, outbox0, không gửi failed
cho lỗi mạng. Hoàng đang kiểm VPN; chưa xác nhận health mạng cuối hồi phục.

Cập nhật **07/11**: mục1–3 đã sửa và lên .56, kiểm cách ly/native phù hợp đạt. [Bằng chứng mục1–3 ngày07/11](C:/work/opnsense/OTSA_BAN_GIAO/BANG_CHUNG_N07_MUC_1_2_3_20261107.md). Còn các ca phối hợp cert/PF reboot và nghiệm thu đầu-cuối.

## 1. Việc thầy giao — đợt 1

- **GUI Upgrade:** hoàn thành, đã kiểm giao diện.
- **Gộp OTSD Connection và Log Forwarding Agent:** hoàn thành.
- **Đổi cổng Connection:** giữ 8443 theo Dương; long-polling tải nhẹ. Máy trùng cổng thì đổi riêng ở OTSD (DEVICE_PORT) và ô Port phía OTSA.
- **Dùng chung cert OTSD cho Wazuh 1515:** có thể làm nhưng chưa triển khai. Máy mới cần khóa Wazuh để xin cert OTSD; phải chốt bootstrap và cấu hình authd để tránh phụ thuộc vòng.

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
- **Truyền CSV firewall:** Dương xác nhận v2 dùng **rules.json theo danh mục firewall/pf**, không truyền CSV cũ. OTSA đã có chức năng nhận/kiểm/lưu JSON, apply/thu hồi/rollback; chưa kiểm bộ PF thật được giao từ .25. Chưa có bằng chứng lưu nguyên CSV cũ trên thiết bị.
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

## 4. Bổ sung Dương ngày 07/11 — trạng thái sau sửa mục1–3

| Mục mới | Cần làm / trạng thái |
|---|---|
| N07-1 | Đã sửa/lên .56; root640/wazuh640 và reject write/symlink đạt native với file thử. |
| N07-2 | Đã sửa/lên .56; CA pin/IP SAN đạt TLS loopback thật, IPv6 probe còn mock; chưa bootstrap lại agent active. |
| N07-3 | Đã lên .56: trang cũ về Connection, inventory giữ khi selection sai, API/backend cấm Mock files. Chưa HTTP session/GUI mutation thật. |
| N07-4 | Blacklist rỗng, chưa từng có alias/table phải no-op. Chưa kiểm ca này; kết quả IPv6 F trước không bao phủ. |
| N07-5 | PF giữ nguyên nhân gốc và kiểm interface trước nạp, vẫn rollback cả bộ. Cần bổ sung. |
| N07-6 | PF pending cùng payload giữ lý do probe, không reset deadline. Chưa sửa. |
| N07-7 | Activity hiển thị mã/lý do đã lọc bí mật thay vì chỉ Failed. Chưa sửa. |

Dương đã kiểm PF 1.0.1 applied/ACK trên **.35**; đây là bằng chứng của Dương, chưa thay nghiệm thu .56. OTSD .25 theo tin nhắn vẫn 0.3.1; 0.3.2 lưu errors và tự đóng tracking bản chưa applied, chưa xác nhận đã chạy .25. Luật/model nhận bản thấp hơn đã đạt **cách ly**, chưa assignment thật .25.

Chi tiết và nguồn: [Phản hồi Dương 07/11](C:/work/opnsense/OTSA_BAN_GIAO/CAP_NHAT_PHAN_HOI_DUONG_20261107.md).


## 5. Thứ tự làm nốt đã gộp 07/11

1. **Đã sửa/lên .56:** enrollment/cert; còn kiểm active với Dương.
2. **Đã sửa/lên .56:** report contract mới; malformed/rejected còn cách ly.
3. **Đã sửa/lên .56:** Connection/TLS cũ, inventory/Mock files; probe thật đạt.
4. **Việc sửa tiếp theo:** PF/blacklist: empty no-op, giữ lỗi gốc, pending/deadline, retention.
5. Activity: hiện mã/chi tiết lỗi đã lọc; từng gói đạt thì backup/triển khai .56.
6. Phối hợp Dương: kiểm cert/rename/pending/blocked active ổn trước, rồi PF reboot.
7. Kiểm assignment thật còn thiếu: PF, mixed state, IPv6, luật/model bản thấp hơn.
8. Khóa/bundle chính thức và cài bản cao hơn khi có đủ điều kiện/cho phép.

P3 cutover active, Wazuh1515 và các việc thầy còn phụ thuộc được theo dõi riêng;
không chặn sửa lỗi trước. Chi tiết điều kiện và phạm vi tại
[thứ tự làm nốt, mục8](C:/work/opnsense/OTSA_BAN_GIAO/TONG_HOP_VIEC_CAN_LAM_20261105.md).

Đã phục hồi lỗi SQLite hot journal có sẵn trước overlay, giữ queue; bổ sung guard startup. Hồi quy105ca đạt, tập trung cuối51ca đạt; idle125s không POST lặp. Backup chung khoảng100KiB, chỉ restart v2, không đổi cert/gates/reboot.
