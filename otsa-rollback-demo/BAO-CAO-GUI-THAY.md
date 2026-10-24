# Rollback Points OTSA kết quả kiểm thử

Hoàng — ngày 23/10/2026, VM lab 192.168.56.56.

## Kết quả

Đã rà và kiểm luồng **giao diện OTSA → API Core → configd → ZFS Boot
Environment**. Trang Rollback Points đã được tích hợp trong Software Update,
không cần viết lại cơ chế rollback hoặc sửa thêm code sản phẩm trong lượt này.

Đã demo thực:

1. Tạo BE riêng qua API trong phiên GUI; danh sách tăng từ 8 lên 9.
2. Activate, kiểm BE được chọn cho lần boot sau; hệ thống đang chạy chưa đổi.
3. Boot vào BE thử: root dataset đúng BE, file dấu mốc được khôi phục về bản
   `before`, hash khớp. Web vẫn hoạt động và hiển thị đúng BE đang chạy.
4. Chọn lại `default`, reboot lần hai: file trở lại bản `after`, hash khớp;
   trạng thái cuối `default (NR)`. Nút Activate thật trên GUI cũng đã kiểm.
5. Kiểm GET không thực hiện thay đổi, POST thiếu CSRF bị 403, tên BE trùng/sai
   bị từ chối; danh sách không phát sinh BE ngoài bài thử.

Có 20 đối chiếu tổng hợp đạt trong RESULT.json; đây là kiểm phạm vi GUI/API và
rollback file dấu mốc, không phải 20 ca nâng cấp/khôi phục độc lập.

## Trạng thái cuối và giới hạn

Dev đã về `default`, pool khỏe. Cấu hình, Wazuh identity, phiên bản gói, cron
và luật PF hiệu lực giữ nguyên. `/tmp/rules.debug` đổi hash sau boot; không
gọi toàn bộ filesystem giữ nguyên byte. File dấu mốc trong default đã dọn;
giữ BE thử `otsa-rollback-demo-20261023` ở trạng thái inactive làm chứng cứ.

Không truy cập `.36/.35/.25`, không build/cài package mới. Chưa kiểm tài khoản
quyền hạn chế, clone/rename/delete BE hoặc rollback sau nâng cấp thật. BE không
khôi phục các dataset ngoài phạm vi của nó và không thay thế backup toàn máy.

Đã có hướng dẫn sử dụng, kịch bản demo và bản đồ source trong
HUONG-DAN-ROLLBACK.md; log/API/hash/ảnh và script giữ đầy đủ trong thư mục này.

Ảnh chính:
- 11-gui-in-restored-be.png: đang chạy trong BE khôi phục, N và mountpoint `/`.
- 16-gui-button-activate-test.png: bấm Activate thật, BE thử có R.
- 17-gui-button-return-default.png: trạng thái cuối default NR, BE thử inactive.

**Có thể báo hoàn thành luồng GUI/API Rollback Points và bài demo lab nêu trên;
chưa kết luận nghiệm thu khôi phục sau mọi loại nâng cấp hoặc production.**
