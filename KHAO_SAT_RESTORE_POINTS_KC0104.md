# Khảo sát Restore Points trong OTSA

Ngày 12/11/2026 · Phạm vi **System → Software Update → Restore Points** trên lab `.56`.

**Kết quả:** Thuyết minh KC.01.04 yêu cầu sao lưu và khôi phục **cấu hình hoạt động** tại Công việc 7.1, trang 38–39. Chưa thấy yêu cầu riêng về màn hình **Restore Points**, điểm khôi phục phiên bản hệ điều hành hay kiểm tra sau khi khởi động lại. Mục Restore Points trên `.56` đang dùng dữ liệu mẫu. Mục **Rollback Points** bên trên đọc boot environment ZFS thật.

## Đối chiếu thuyết minh

Nguồn: [KC0104_TMDT_OT_Security.pdf](<D:/Downsload+/KC0104_TMDT_OT_Security.pdf>). Đã rà văn bản 67 trang theo các nhóm từ sao lưu, khôi phục, phục hồi, snapshot, restore và rollback. Đã xem ảnh các trang 38, 39, 44, 45. Số trang bên dưới là số in trên tài liệu.

| Vị trí | Nội dung liên quan | Đối chiếu OTSA |
| --- | --- | --- |
| **Công việc 7.1, trang 38–39** | Thiết lập, sao lưu và khôi phục cấu hình hoạt động. Gồm phân tích, thiết kế, lập trình và kiểm thử. | Yêu cầu gần với **System → Backup & Restore → Backups** và lịch sử cấu hình. Đây là đối chiếu theo chức năng, vì đề tài không chỉ định đường dẫn GUI. |
| **Công việc 7.3, trang 39** | Bảo vệ mã nguồn, kiểm tra tính toàn vẹn và cập nhật phần mềm trên thiết bị. | Có liên quan tới an toàn khi cập nhật. Phần này chưa nêu tạo điểm khôi phục trước cập nhật hoặc tiêu chí hoàn tác phiên bản. |
| **Công việc 12.4, trang 44–45** | Quản lý và phân phối cập nhật an toàn từ hệ thống trung tâm, bao gồm tập luật và mô hình AI. Trang 44 có nói đến điều phối và lịch cập nhật. | Gắn với luồng OTSD giao bản và OTSA xử lý. Chưa nêu quản lý điểm khôi phục từ OTSD hay kiểm tra sau boot. |

Các đoạn về phục hồi hệ thống ở trang 6–7 thuộc phần tổng quan giải pháp và tiêu chuẩn. Các đoạn này cung cấp bối cảnh chung, chưa mô tả một màn hình Restore Points của OTSA.

## Hiện trạng hai mục trên .56

| Mục | Đường dẫn | Hành vi đã xác minh |
| --- | --- | --- |
| **Restore Points** | `/ui/integrity/restore` | Menu của plugin `otsa-preview`. Bảng hiển thị ba điểm mẫu, phiên bản đang chạy và các kết quả post-boot mẫu. **Create restore point** gọi `/api/otsapreview/integrity_restore/action/create`. Action lấy chuỗi thông báo thành công từ `Pages.php` rồi trả về cho GUI. Mã hiện tại không gọi Core hoặc `bectl` để tạo boot environment. |
| **Rollback Points** | `/ui/core/snapshots` | Màn hình Core. API gọi configd để đọc và thao tác boot environment ZFS. Trên `.56`, `/` là ZFS và `bectl list -H` trả về 9 boot environment thật, gồm `default` đang hoạt động và `otsa-pre-0.1.7-1793194692-f76ff575`. |
| **Backup & Restore → Backups / History** | `/diag_backup.php`, `/ui/core/backup/history/this` | Xuất/nhập cấu hình XML và theo dõi các bản cấu hình đã lưu. Phạm vi là cấu hình, khác với chuyển môi trường khởi động ZFS. |

Đã kiểm menu và mã đã cài trên `.56`, cùng danh sách boot environment bằng lệnh chỉ đọc. Không bấm **Create**, activate, restore hoặc reboot trong lượt khảo sát.

## Điểm cần chốt nếu đưa vào phạm vi triển khai

Nếu yêu cầu là **sao lưu và khôi phục cấu hình** theo 7.1, đối chiếu và nghiệm thu luồng XML của **Backup & Restore**. Nếu yêu cầu là **quay lại môi trường trước cập nhật**, cần xác định phạm vi dữ liệu sẽ phục hồi và nghiệm thu bằng boot environment thật. Core đã có **Rollback Points**, còn mã thực thi cập nhật OTSA có bước tạo và kiểm boot environment trước khi cài. Phần **Restore Points** riêng chỉ có cơ sở triển khai khi nhóm chốt thêm nhu cầu cụ thể, chẳng hạn hiển thị điểm tạo bởi giao dịch cập nhật và kết quả kiểm tra sau boot từ dữ liệu thật.

## Điểm đọc mã

- [Menu Restore Points](../otsa-plugins/otsa/ui/otsa-preview/src/opnsense/mvc/app/models/OPNsense/OtsaPreview/Menu/Menu.xml#L36), [controller preview](../otsa-plugins/otsa/ui/otsa-preview/src/opnsense/mvc/app/controllers/OPNsense/Integrity/RestoreController.php#L34), [dữ liệu mẫu](../otsa-plugins/otsa/ui/otsa-preview/src/opnsense/mvc/app/models/OPNsense/OtsaPreview/Pages.php#L228), [action trả thông báo](../otsa-plugins/otsa/ui/otsa-preview/src/opnsense/mvc/app/controllers/OPNsense/OtsaPreview/Api/PreviewApiBase.php#L238).
- [API Rollback Points](../core/src/opnsense/mvc/app/controllers/OPNsense/Core/Api/SnapshotsController.php#L133), [wrapper `bectl`](../core/src/opnsense/scripts/system/bectl.py#L53), [bước tạo boot environment của updater](../otsa-plugins/otsa/otsd/otsa-update/src/opnsense/scripts/otsa-update/package_runtime.py#L130).
- [Trang sao lưu cấu hình](../core/src/www/diag_backup.php), [API lịch sử cấu hình](../core/src/opnsense/mvc/app/controllers/OPNsense/Core/Api/BackupController.php#L158).
