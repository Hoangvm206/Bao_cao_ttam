# Hướng dẫn Rollback Points trên OTSA

## Chức năng và nơi mở

Mở **System → Software Update → Rollback Points**, URL `/ui/core/snapshots`.
OTSA tích hợp menu/nút dẫn tới giao diện và API Core có sẵn, dùng ZFS Boot
Environments (BE). Không phải cơ chế khôi phục toàn VM mới được viết riêng.

Trang có tên BE, trạng thái, mountpoint, dung lượng, ngày tạo và các nút thao
tác. Created trên web hiển thị theo múi giờ trình duyệt; không so trực tiếp với
chuỗi UTC/native mà bỏ qua chênh lệch múi giờ.

| Trạng thái | Ý nghĩa |
| --- | --- |
| N | BE đang chạy |
| R | BE mặc định cho lần boot sau |
| NR | BE đang chạy và cũng là mặc định cho lần boot sau |
| T | BE được chọn cho một lần boot thử bằng công cụ native; không phải nút GUI đã thêm |
| - | BE không active |

**Activate chỉ chọn BE cho lần boot sau, không lập tức khôi phục hệ thống đang
chạy.** Cần reboot theo kế hoạch để chuyển môi trường.

## Phạm vi dữ liệu

Trong VM dev đã khảo sát, `/`, `/conf`, `/usr/local`, DB pkg và `/var/ossec`
thuộc BE gốc. `/home`, `/tmp`, `/var/log` và một số dataset khác nằm ngoài BE.
BE không phục hồi toàn ổ đĩa và không thay thế backup ngoài thiết bị. Image
khác phải khảo sát lại layout dataset trước khi kết luận.

Không dùng rollback trên máy đang giữ receipt/giao dịch cập nhật, chứng chỉ hoặc
thay đổi cấu hình quan trọng nếu chưa đánh giá chúng sẽ quay về trạng thái nào.
Với `.36`, mặc định chỉ demo xem danh sách; bài boot dùng dev `.56`.

## Quyền truy cập

Core dùng quyền **System: Snapshots** cho cả trang và các API snapshot. Quyền
inventory chỉ đọc của plugin OTSA không tự cấp quyền quản trị BE của Core.
Lượt demo ngày23/10 dùng root; chưa kiểm E2E tài khoản quyền hạn chế. Không coi
ẩn nút/menu là đã kiểm phân quyền backend.

## Kịch bản demo có kiểm soát

Chỉ thực hiện trên máy lab có đường quản trị và console sẵn sàng. Không chạy
lại bằng đúng tên/file đang có từ bài23/10; chọn tên thử riêng cho mỗi lượt.

1. Ghi BE đang chạy và BE mặc định, pool health, dung lượng, inventory và hash
   cấu hình/identity/updater cần bảo vệ. Xác nhận không có tác vụ đang chạy.
2. Tạo một file dấu mốc riêng trong dataset thuộc BE, nội dung `before`.
3. Tạo BE mới qua giao diện/API trong phiên web. Kiểm danh sách có BE đó.
4. Chỉ đổi file dấu mốc thành `after`; không thay package hoặc firewall.
5. Activate BE thử trên GUI. Xác nhận BE thử có `R`, BE hiện hành vẫn có `N`:
   hệ thống chưa đổi cho tới khi reboot.
6. Để thử một lần an toàn: chọn lại BE gốc bằng GUI, rồi dùng native
   `bectl activate -t <BE-thử>` và kiểm `T`. Đây là bước SSH riêng trong lab.
7. Reboot; kiểm root dataset đúng BE thử, file dấu mốc là `before` và hash khớp.
   Mở lại GUI để đối chiếu `N`/mountpoint `/`, pool và inventory.
8. Chọn lại BE gốc bằng GUI, reboot. Kiểm root đã quay về, BE gốc có `NR`,
   file dấu mốc là `after` và hash khớp trước boot.
9. Đối chiếu dữ liệu bảo vệ, chỉ dọn file thử do bài này sở hữu trong BE gốc.
   Giữ BE thử làm bằng chứng nếu đã thống nhất; không xóa BE có sẵn.

Bài23/10 dùng `default`, BE `otsa-rollback-demo-20261023`, marker
`/usr/local/etc/otsa-update/rollback-proof-20261023.json`. Script `dev-demo.py`
chỉ quản lý marker và khảo sát, không tự activate hoặc reboot.

## Luồng code đang dùng

| Lớp | Vị trí trong workspace |
| --- | --- |
| Menu OTSA | otsa-plugins/sysutils/otsa-update/src/opnsense/mvc/app/models/OPNsense/OtsaUpdate/Menu/Menu.php |
| Nút từ Updates | otsa-plugins/sysutils/otsa-update/src/opnsense/mvc/app/views/OPNsense/OtsaUpdate/index.volt |
| Giao diện bảng/form | core/src/opnsense/mvc/app/views/OPNsense/Core/snapshot.volt và controllers/OPNsense/Core/forms/snapshot.xml |
| API vận hành | core/src/opnsense/mvc/app/controllers/OPNsense/Core/Api/SnapshotsController.php |
| Quyền | core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml, page-snapshots |
| Backend | core/src/opnsense/service/conf/actions.d/actions_zfs.conf → scripts/system/bectl.py → bectl |

`/api/otsa_update/service/snapshots` chỉ là inventory rút gọn. Trang Rollback
Points thao tác qua `/api/core/snapshots/*`; không lấy inventory làm bằng chứng
đã tạo/activate BE. Các API mutating yêu cầu POST và phiên/quyền/CSRF phù hợp.

Không phát sinh sửa code sản phẩm chỉ để làm lại giao diện đang có. Nếu cần
đổi UX hoặc sửa lỗi Core/plugin sau khảo sát, trình bày thay đổi để Hoàng xác
nhận trước, không tự mở rộng sang backend restore VM hay updater.

## Những việc chưa được chứng minh bởi demo marker

- Rollback sau một đợt nâng cấp package/base/kernel thật và mọi dependency.
- Dataset nằm ngoài BE, máy `.35/.36` hoặc production khác layout.
- Quyền tài khoản hạn chế, clone/rename/delete BE, phục hồi khi mất ổ/pool.

Tham chiếu:
[FreeBSD bectl](https://man.freebsd.org/cgi/man.cgi?query=bectl&sektion=8&format=html).
Kết quả và ảnh/log cụ thể xem báo cáo cùng thư mục; hướng dẫn này không tự
khẳng định mọi bước được chạy lại ở mọi máy.
