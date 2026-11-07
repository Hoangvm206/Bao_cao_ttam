# Luồng firewall v2 hiện tại 

## 1. Làm rõ chữ “đối chiếu”

**Hiện đã có phép so sánh để tính thao tác thêm/sửa/xóa luật OTSD.**
**Phép so sánh này không phải cơ chế giữ thay đổi local theo yêu cầu mới của thầy.**

Trong `otsa_pf_delta.php::plan()`, luật nhận về là tập mong muốn (`wanted`).
Planner ghép slot với UUID hiện có, so các trường; nếu khác thì lập thao tác
update theo dữ liệu nhận về. Luật OTSD còn dư trong phạm vi quản lý có thể
được đưa vào danh sách delete. Vì vậy, khi một lần apply chạy, trường đã sửa
local của luật thuộc OTSD có thể bị thay bằng dữ liệu server. Không kết luận
mọi lượt poll đều ghi đè: còn điều kiện reconcile/no-delta của luồng bên ngoài.

Không có cơ sở để báo đã đáp ứng chính sách “server giao bản cũ thì giữ bản
local đã sửa”. Lời mô tả “đối chiếu luật” trước đây chỉ nói tới delta planner;
không có nghĩa tính năng xử lý xung đột đó đã hoàn thành.

## 2. Luồng hiện tại đã có trong mã

```text
OTSD: state có entry type=firewall/pf
  category, version, order, file.path, size, sha256
                   ↓
OTSA: nhận state → tải rules.json qua v2/files → kiểm file/nội dung
                   ↓
Chuẩn bị luật PF theo danh mục và thứ tự; gắn [OTSD:<category>]
                   ↓
Kiểm hợp lệ từng danh mục/interface/alias
                   ↓
Planner hiện tại: đọc luật đang có + tập nhận về → tính add/update/delete
                   ↓
Ghi thay đổi vào model Firewall Filter trong bộ nhớ, validate
                   ↓
Backup/journal → serialize model → lưu cấu hình
                   ↓
Bảng Firewall: Rules đọc model/cấu hình và hiển thị luật khi tải lại
                   ↓
Reload PF → kiểm kernel/probe → commit hoặc pending/rollback
                   ↓
Report kết quả về OTSD qua outbox/FIFO/ACK
```

Không cần nhập file thủ công trên web hoặc đổi JSON thành CSV để đi vào
model. CSV có thể là đầu vào của công cụ phía người phối hợp; hai bên chỉ
cần chốt cách nối, không dựng thêm một bộ ghi/Apply song song.

“Hiện trên bảng” và “đã có hiệu lực chặn/cho phép lưu lượng” là hai mốc khác
nhau. Luồng hiện tại có cả ghi model và Apply; nếu nhóm phối hợp muốn xử lý
trước khi Apply thì phải nối trước bước ghi, không đợi reload xong.

## 3. Chỗ cần phối hợp cho yêu cầu của thầy

Ví dụ: OTSD giao luật A; người dùng sửa A trên OPNsense; OTSD giao lại A cũ.
Kết quả yêu cầu: bảng giữ A đã sửa local, không khôi phục A cũ từ server.

```text
Luật đã nhận/kiểm + luật hiện có trên OPNsense
                   ↓
[PHẦN CẦN BỔ SUNG: nhận diện cùng luật, phát hiện sửa local,
 quyết định giữ/ghép/cập nhật theo chính sách đã thống nhất]
                   ↓
Tập luật cuối được phép ghi → planner/mutation → lưu → Apply
```

Điểm đọc mã đầu tiên là `otsa_pf_delta.php::plan()` và chỗ gọi trong
`stage()`, trước `mutate()`. Bên điều phối là `otsa_pf_sync.php::runSync()`.
Có thể chọn sửa planner hoặc thêm bước trước planner; đây là điểm tích hợp
đề xuất, chưa phải thiết kế đã chốt. Không chỉ thêm xử lý ở callback Save:
ở thời điểm đó kế hoạch cập nhật và model trong bộ nhớ đã được tạo.

Người phối hợp cần chốt ba điều để nối đúng:

1. Nhận diện cùng một luật bằng gì? Hiện có slot/UUID local, chưa phải
   hợp đồng rule ID bền vững giữa hai phía. Không mặc định mô tả hay số
   thứ tự là ID ổn định khi người dùng/server thay đổi thứ tự.
2. Làm sao biết local đã sửa so với bản từng nhận? Chỉ so server và local
   đang khác nhau chưa đủ kết luận phía nào cũ. Chốt dữ liệu mốc cần giữ.
3. Khi server giao bản mới thật hoặc thu hồi luật đang sửa local thì xử lý
   thế nào? Yêu cầu ví dụ “giao lại bản cũ” chưa tự quyết định các tình huống này.

Hoàng phụ trách nhận/kiểm dữ liệu OTSD và nối vào điểm xử lý thống nhất.
Người phối hợp phụ trách chính sách đối chiếu/giữ thay đổi local trước ghi.
Chỉ dùng một đường ghi model/Apply sau khi hai phần đã thống nhất kết quả.

## 4. File và hàm cần xem

Các đường dẫn bên dưới tính từ
`C:/work/opnsense/otsa-plugins/otsa/otsd/`.

| File | Vai trò / điểm đọc |
|---|---|
| U/src/opnsense/scripts/otsa-update/v2_sync.py | Nhận state, điều phối nhận file/reconcile/report. |
| P/src/opnsense/scripts/otsa-policy/v2_rules.py | `pf_payload()`, `NativeRules.apply_categories()` chuẩn bị/kiểm danh mục trước loader. |
| P/src/opnsense/scripts/otsa-policy/otsa_pf_delta.php | `owned()`, `plan()`, `stage()`, `mutate()`: quyền quản lý, delta và ghi model. Điểm chính cần phối hợp. |
| P/src/opnsense/scripts/otsa-policy/otsa_pf_sync.php | `runSync()`: đọc model, gọi stage, journal/backup và Save. Adapter native, không gọi HTTP API ở bước ghi local. |
| P/src/opnsense/scripts/otsa-policy/otsa-pf-loader.py | `run()`, `reload_filter()`: giao dịch, reload/verify/probe/rollback. |

U=otsa-update; P=otsa-policy. Không sửa nhầm bản legacy hoặc worktree khác.
`owned()` bảo vệ luật ngoài phạm vi OTSD và guard [OTSA-policy]; điều này
khác giữ sửa local của chính luật OTSD. Planner có thể điều chỉnh sequence
luật ngoài OTSD để sắp thứ tự, nên không hứa mọi trường/priority luôn bất biến.


Chức năng tự ghi/Apply có trong nguồn; .56 bật rules consumer ở lần đọc07/11.
Chưa nghiệm thu PF assignment thật .25→.56 trong đợt này và chưa triển khai
cơ chế giữ sửa local nói trên. Không lấy blacklist có sẵn trên ảnh để chứng
minh PF JSON category đã được server giao/ACK. Không tạo rule nguy hiểm hoặc
report failed giả để kiểm. Tiến độ chung xem [báo cáo xuyên suốt](BAO_CAO_TIEN_DO_OTSA.md).
