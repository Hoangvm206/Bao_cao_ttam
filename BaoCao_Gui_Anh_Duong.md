# Kết quả Việc 1–2 theo giao việc OTSD ngày 21/10/2026

**Môi trường: VM dev OTSA `192.168.56.56`, Core `26.7.6_31 / 8b9be25e3`. Đã code và kiểm thử mock; chưa thử OTSD thật `.25`, chưa thay `.35/.36`.**

## Việc 1 — Đã đạt bài đo một giờ và reboot trên VM

- Bài đo ngày 20/10, 21:59:30–22:59:31 giờ Việt Nam: **3.600,18 giây, 120 mẫu**, CPU riêng collector tính cả helper đã thoát trung bình **0,3594%**, cao nhất **0,7976%**, tất cả dưới 1%. Log active + archive tối đa **975.160 byte**, dưới 20 MB. CPU trong từng dòng `metrics` là CPU toàn máy, khác số đo riêng collector.
- Khi reboot kiểm chứng phát hiện bản `0.1_1` đặt enable config sai thư mục. Đã sửa bằng template OPNsense vào `/etc/rc.conf.d`, build/cài **`os-otsa-telemetry-0.1_2`**, giữ nguyên code collector. Reboot 09:17 và 09:44 ngày 21/10 đã xác nhận telemetry/Wazuh tự chạy, có dữ liệu mới; không start tay. Bài CPU một giờ thuộc collector ngày 20/10, không phải bài đo lại sau reboot.
- Wazuh đọc `/var/log/otsa/otsd-telemetry.json`; giữ tên tiến trình thực `sshd-session`. Chưa xác nhận ingest hay dashboard trên OTSD.
- Kèm [otsd-telemetry.json](otsd-telemetry.json): **2.374 dòng JSON gốc / 389.979 byte**, gồm 120 metrics, 720 ifstat, 59 snap, 1.475 listen. Trong giờ audit các snapshot có **conn=0**; không bổ sung kết nối giả vào bài đo.
- Kèm riêng [otsd-telemetry-conn-sample.json](otsd-telemetry-conn-sample.json): một snapshot kết nối quản trị thật ngoài giờ audit, đầy đủ marker/conn/listen để thử phần phiên quản trị. Hai tệp đã lưu local để Hoàng tự gửi, chưa upload.

![Việc 1 — audit một giờ và tệp dữ liệu](bang-chung/viec-1-one-hour.png)

## Việc 2 — Auto-enroll đạt trên mock, đã kiểm boot

- Đã build/cài **`os-otsa-enroll-0.1`**, mặc định tắt; cấu hình bật trên VM chỉ trỏ **`https://127.0.0.1:8445/otsa`**. Agent thực của VM là **`001 / OPNsense.internal`**; không đổi thành `otsa-dev-ci-live` hoặc thay identity `.35`.
- Đọc khóa agent tại máy, giữ `agent_id` dạng chuỗi; gửi CSR + HMAC theo Phụ lục F. **Kiểm HMAC trên nguyên byte phản hồi trước khi nhận CA/cert**, kiểm CN, thời hạn, clientAuth, cert/key và chuỗi ký. Khóa agent và private key không ra khỏi VM.
- **8 unit test và 19 ca integration đạt**: bootstrap hợp lệ/sai MAC, không nhận CA khi MAC sai, chưa đến hạn không gọi mạng, CN/key/cert/khóa agent sai, clock lệch/400, replay/409, 403/429/503, TLS sai CA không fallback, cert hết hạn tự xin lại và giữ nguyên private key.
- Cert/CA/chain được lưu theo generation root-only. Adapter dùng model System Trust, giữ refid qua lần cấp lại; không nhập CA private key hoặc mặc định CA kiểm server là CA ký client. Đã dùng **exporter mTLS sẵn có → `/otsa/whoami` HTTP 200**, sau đó trả lại profile GUI cũ. Cert mới có trong Trust, không tự thay lựa chọn hiện tại của quản trị viên.
- Gói đã cài thật xin cert thành công. Reboot **09:44:16**: boot hook tự chạy **09:46:09**, trả `certificate_not_due`, `network_contacted=false`, key/cert không đổi, Trust không ghi lại. Telemetry/Wazuh tiếp tục tự chạy; hash hai downloader Core không đổi.
- Daily cron **03:17 giờ thiết bị** đã cài; chưa chờ đúng lịch daily để nghiệm thu. Chưa có tín hiệu thu hồi đã xác thực nối từ downloader; không coi mọi HTTP 403 là thu hồi. Chưa có GUI health cho lỗi enrollment định kỳ.

![Việc 1–2 — reboot thực và quyền file](bang-chung/viec-1-2-reboot.png)

![Việc 2 — auto-enroll và các ca kiểm thử](bang-chung/viec-2-enrollment.png)

## Còn cần thống nhất / cung cấp

1. Anh Dương báo khi **`.25:8443/otsa`** sẵn sàng, kèm phản hồi/headers thực của `enroll`, `whoami`, manifest và thông tin chain/SAN. Hiện chưa có bằng chứng với server thật; `401` trang quản trị không được dùng làm bằng chứng mTLS.
2. **Chống phát lại phản hồi:** Phụ lục F hiện MAC toàn phản hồi nhưng chưa ràng buộc CSR hash/ts/nonce của yêu cầu. Nhờ anh xác nhận bổ sung `csr_sha256` + `request_ts` hoặc nonce được MAC bảo vệ. Lịch sử generation tại máy chỉ chặn bản từng thấy, chưa bảo vệ đầy đủ sau reset/rollback. Cũng cần xác định tín hiệu thu hồi riêng, phân biệt quyền giao bản bị từ chối.
3. Về phía OTSA, ngoại lệ TLS bootstrap mới được Hoàng duyệt **cho mock VM loopback**; gia hạn và mTLS/download vẫn verify TLS. Bootstrap production, dùng lại key đang có trên `.35`, chain thật và phục hồi lỗi Trust cần được rà trước khi triển khai. Không còn chờ ký tay CSR cũ, nhưng chưa tạo lại/ghi đè key/CSR production. Cổng quản trị `.35/.36` chưa khảo sát trong vòng thử VM này.

Các trả lời về version firewall/detection độc lập, `min_from` phía OTSD, `core_pkg` tùy chọn, RSA/SHA-256 `.sig` nhị phân và giữ tên `sshd-session` đã được ghi nhận; không hỏi lại. Việc 3–6 chưa triển khai trong vòng này; executor cập nhật vẫn khóa, chưa nạp/bật luật hoặc IPS.

Ảnh là **phiếu kết quả dựng từ output SSH/JSON thật**, không phải ảnh dashboard OTSD. Bằng chứng gốc nằm trong thư mục `bang-chung`; tệp `SHA256SUMS.txt` dùng đối chiếu bản bàn giao. Bản bàn giao không chứa key, `client.keys`, config.xml, token hay profile trình duyệt.
