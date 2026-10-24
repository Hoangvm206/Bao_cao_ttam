# Khảo sát mTLS của Wazuh agent FreeBSD


## Đã kiểm được

Wazuh agent FreeBSD 4.14.7 dùng được chứng chỉ thiết bị và khóa riêng của luồng mTLS OTSD lab để xác thực khi đăng ký. Đã kiểm cả công cụ enrollment và daemon đọc cấu hình XML, bắt tay TLS 1.3 và trình đúng chứng chỉ.

- 8 ca kiểm công cụ enrollment và 4 ca kiểm daemon đạt theo kỳ vọng.
- Các ca sai CA, thiếu chứng chỉ, khóa không khớp hoặc không đủ quyền đọc đều bị từ chối.
- Agent là binary thật; phía Manager là máy chủ giả lập trong môi trường cô lập. Chưa nghiệm thu với Manager thật hoặc qua thao tác Apply trên web.

## Phần còn thiếu

Plugin Wazuh trên OPNsense hiện chưa có đầy đủ phần chọn và đưa CA/cert/key xuống agent. Khóa OTSD gốc có quyền root 0600 nên daemon chạy bằng user wazuh không đọc được. Thử chuẩn bị bộ file riêng với quyền phù hợp thì daemon dùng được.

Vì vậy, agent native đã có khả năng; phần cần bổ sung nằm ở plugin quản lý phía OPNsense.

## Đề xuất xin ý kiến Thầy

Nếu tiếp tục,đề xuất bổ sung trong plugin Wazuh:

1. Cho chọn CA và chứng chỉ thiết bị trên giao diện.
2. Chuẩn bị cert/key ở vùng riêng với quyền agent đọc được, kiểm hợp lệ trước khi áp dụng.
3. Sinh các đường dẫn vào cấu hình enrollment và cập nhật khi chứng chỉ được gia hạn.

Phạm vi dự kiến là model/form, template ossec.conf và script chuẩn bị chứng chỉ của plugin; không sửa mã C Wazuh hoặc luồng tải file đang làm với anh Dương.
