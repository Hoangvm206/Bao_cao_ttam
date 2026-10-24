# Chỉ mục lệnh và chứng cứ demo rollback

Máy duy nhất thao tác: dev qua SSH vagrant@127.0.0.1:2222, GUI
https://192.168.56.56. Không truy cập .36/.35/.25. Lượt này không sửa source
sản phẩm; thêm test harness và tài liệu, dùng UI/API đã tích hợp.

## Trình tự thực hiện

`dev-demo.py` được truyền qua stdin tới `sudo -n /usr/local/bin/python3 - <action>`.
Script không lưu mật khẩu, không tự chạy bectl mutation hoặc reboot. Lệnh BE
vận hành dưới đây đã được Hoàng giao cho bài demo dev, không phải lịch tự chạy.

| Bước | Lệnh/thao tác | Chứng cứ |
| --- | --- | --- |
| Xem trước | ui-check.mjs inspect | 01-gui-before.json/png |
| Baseline | dev-demo.py baseline | 02-dev-baseline.json |
| Marker trước | dev-demo.py prepare | 03-marker-before.json |
| Tạo BE | ajaxCall POST /api/core/snapshots/add, name=otsa-rollback-demo-20261023 | 04-gui-create.json/png |
| Marker sau | dev-demo.py mutate | 05-marker-after.json |
| Chọn BE thử | POST /api/core/snapshots/activate/{uuid-thử} qua phiên GUI | 06-gui-activate-test.json/png |
| Trả default | POST activate/{uuid-default} qua phiên GUI | 07-gui-reset-default.json/png |
| Boot một lần | bectl activate -t otsa-rollback-demo-20261023; bectl list -H | 08-temporary-boot-selection.json |
| Reboot thứ nhất | sudo -n /sbin/shutdown -r now | 09-reboot-test.log và ảnh console09 |
| Kiểm BE thử | dev-demo.py test-boot | 10-verify-test-boot.json |
| Xem GUI sau rollback | ui-check.mjs inspect | 11-gui-in-restored-be.json/png |
| Chọn default | POST activate/{uuid-default} qua phiên GUI | 12-gui-select-return-default.json/png |
| Reboot thứ hai | sudo -n /sbin/shutdown -r now | 13-reboot-return.log, 13-console-return.png |
| Kiểm quay về | dev-demo.py return-boot | 14-verify-return-boot.json |
| Guard API | ui-check.mjs guards | 15-gui-api-guards.json/png |
| Nút Activate | Click button.command-activate_be đúng uuid của BE thử | 16-gui-button-activate-test.json/png |
| Nút trả default | Click nút Activate của default, không reboot thêm | 17-gui-button-return-default.json/png |
| Dọn marker | dev-demo.py cleanup | 18-final-state.json |
| Đóng phiên browser | Thử logout, dừng browser lab, dọn hai profile đúng đường dẫn | 19-browser-logout.json, 20-browser-cleanup.json |

Các file dev-demo.py và ui-check.mjs lưu đầy đủ argv khảo sát và payload API
không nhạy cảm. Bản ghi inventory chỉ gồm các gói OTSA/OPNsense/Wazuh; cấu hình,
identity và cron chỉ ghi hash, không xuất nội dung bí mật. Browser test chỉ lưu
URL/method của API snapshot, không lưu header xác thực, cookie hay mật khẩu.

## Đối chiếu bắt buộc

- Marker before từ03 phải khớp10; marker after từ05 phải khớp14.
- Root ở10 là zroot/ROOT/otsa-rollback-demo-20261023; ở14/18 là zroot/ROOT/default.
- 17 có default NR và test BE `-`; tám BE ban đầu vẫn có UUID cũ.
- Config/identity/plugin source hash ở18 khớp02; inventory, root cron và
  pfctl -sr hash khớp. Riêng /tmp/rules.debug sinh lại khi boot nên đổi hash.
- 15: bốn GET mutation trả HTTP200 với status failed, không phải HTTP405.
  POST không CSRF trả403; trùng tên/sai tên có validations, count9 không đổi.

RESULT.json tổng hợp 20 điều kiện; SHA256SUMS.txt liệt kê các tệp hồ sơ.

## Attempt và giới hạn cần giữ đúng

- Browser mở tương tác ban đầu không giữ được cổng debug; chuyển sang browser
  headless riêng. 00-gui-attempt1.json ghi lỗi chờ trang do self-signed lab;
  sau đó chỉ bỏ qua chứng chỉ cho browser test, không đổi System Trust.
- Chờ boot đầu150s chưa đủ; console tiếp tục khởi động dịch vụ, sau đó SSH
  xác minh root/marker thành công. Không coi hết cửa sổ chờ là rollback thất bại
  hoặc dùng thời gian chờ này làm số đo boot chính xác.
- Một số ảnh chụp sớm như06 còn loading vì harness chờ grid chưa đủ. Đã sửa
  điều kiện đợi hàng thật và kiểm ảnh11/16/17. Dùng các ảnh cuối làm minh họa,
  giữ ảnh sớm/JSON gốc để không làm mất lịch sử.
- Lần gọi logout không xác minh được trang login trong thời hạn (19=false).
  Browser incognito và profile do test sở hữu đã dừng/xóa (20=true); không
  khẳng định đã kiểm invalidation session phía server.
- Chỉ có hai reboot thật; bước boot T là lệnh SSH riêng, không được ghi thành
  chức năng mới trên GUI. Tạo BE ban đầu qua API trong phiên GUI, không khẳng
  định đã kiểm nút Add/form submit. Hai nút Activate thật đã kiểm riêng.
- Không xóa, rename hoặc clone BE; không tạo user hạn chế. Giữ BE thử inactive
  `10.3M` Used theo bectl cuối; đây là CoW Used, không phải dung lượng
  bản sao đầy đủ hoặc dung lượng tiết kiệm có thể suy rộng.
