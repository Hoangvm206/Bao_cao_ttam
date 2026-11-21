# Báo cáo: luồng chuyển luật Firewall/PF phía OTSA

## 1. Vòng đời `rule_id` của luật firewall/PF

Luồng đã chốt với anh Dương.

1. **OTSD cấp và lưu ID.** Mỗi luật có một `rule_id` dạng UUID v4 trong `rules.json`.
   - Giữ ID: sửa luật, đổi thứ tự, giao lại, quay về phiên bản còn lưu.
   - Cấp ID mới: tạo mới, nhân bản, xóa rồi tạo lại, chuyển danh mục.
   - Ngoại lệ: dán lại nguyên luật cũ kèm ID vào cùng danh mục thì giữ ID.
   - `sequence` chỉ dùng để xếp thứ tự.
2. **OTSA nhận và đối chiếu.**
   - SA lưu ánh xạ `rule_id` với UUID luật trên OPNsense và ghi marker `[OTSD:<rule_id>]` vào description.
   - Nếu người dùng xóa marker, SA vẫn tìm được luật qua UUID đã lưu.
   - SA so nội dung và thứ tự riêng.
   - Với bản cũ thiếu ID, SA giữ UUID và marker nếu tìm được đúng một luật có nội dung khớp trong cùng danh mục.
3. **OTSA xử lý lỗi theo danh mục.**
   - ID trùng giữa hai danh mục: báo `rule_id_duplicate` cho cả hai.
   - Ghép lần đầu không chắc chắn: báo `rule_id_match_ambiguous`.
   - Luật đã bị sửa tay: SA giữ nguyên và báo `local_rule_modified` kèm ID.
   - Các danh mục hợp lệ vẫn có thể tiếp tục khi áp PF an toàn.
4. **Quản trị viên xử lý trên Firewall → Rules.**
   - **Giữ luật hiện tại** cho lần giao đang xét, hoặc **Dùng bản OTSD**.
   - Lần giao mới được kiểm tra lại.
   - Nếu chọn bản OTSD, SA sao lưu trước khi ghi đè và kiểm PF sau khi áp.

## 2. Hạng mục đã hoàn thành

| Hạng mục | Kết quả |
|---|---|
| Nhận `rule_id` | OTSA nhận trường `rule_id` (UUID v4) từ OTSD trong `rules.json` |
| Ánh xạ định danh | Lưu ánh xạ `rule_id` ↔ UUID luật local của OPNsense. Đổi thứ tự thì luật vẫn giữ UUID local |
| Marker nhận diện | Ghi `[OTSD:<rule_id>]` vào description để lọc luật do OTSD giao. Marker bị xóa vẫn nhận ra luật qua UUID đã lưu |
| Phát hiện sửa tay | Luật OTSD bị sửa hoặc xóa marker thì giữ bản local, không ghi đè, báo `local_rule_modified` kèm `rule_id` |
| Giao diện xử lý | Firewall → Rules: chọn danh mục để xem các trường khác nhau, rồi chọn Giữ luật hiện tại hoặc Dùng bản OTSD |
| Ghi đè an toàn | Dùng bản OTSD thì sao lưu trước khi áp, kiểm PF sau khi áp |
| Giao bản mới | OTSD giao bản mới, hạ phiên bản hoặc thu hồi danh mục thì OTSA xét lại xung đột từ đầu |

## 4. Quy tắc xử lý trong luồng

- **Giữ luật hiện tại:** chỉ có hiệu lực cho lần giao đang xét. Quản trị viên vẫn đổi sang Dùng bản OTSD được cho tới khi có lần giao mới.
- **Dùng bản OTSD:** thực hiện sau khi quản trị viên xác nhận, có sao lưu trước và kiểm PF sau.
- **Luật không có marker và không có trong ánh xạ:** coi là luật người dùng tự tạo, luồng này không tác động.

## 5. Điểm tiếp giáp

1. Sửa nội dung, đổi vị trí hoặc xóa luật OTSD trên máy sẽ được luồng coi là sửa tay và đi qua quy trình xung đột ở mục 4.
2. Nhận diện luật dựa trên `rule_id` và UUID local đã lưu. Nên tránh xóa rồi thêm mới luật OTSD vì UUID local sẽ đổi.
3. Thao tác nội bộ trên luật thuộc phía local. Nếu có thao tác nào làm thay đổi luật OTSD ngoài các trường hợp trên, báo để đưa vào luồng.

