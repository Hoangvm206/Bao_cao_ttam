# Báo cáo tổng hợp phát triển và kiểm thử OTSA


## 1. Mục tiêu và kiến trúc

Xây dựng khả năng quản lý tập trung cho thiết bị OTSA trên nền OPNsense:
thu thập telemetry, tự cấp/gia hạn chứng chỉ thiết bị, nhận luật phát hiện và
tường lửa từ OTSD, kiểm tra bộ phát hành có chữ ký và cập nhật phần mềm có kiểm soát.

OTSA chủ động hỏi và tải dữ liệu từ OTSD qua HTTPS mTLS; quản trị OTSD quyết
định nội dung, đối tượng và thời điểm giao. OTSA kiểm tính toàn vẹn trước khi
áp dụng, giữ chính sách của nhà máy và có cơ chế phục hồi khi áp dụng thất bại.
Mã nguồn được chia thành bốn plugin: `otsa-telemetry`, `otsa-enroll`,
`otsa-policy`, `otsa-update`, kết hợp các điểm tích hợp trong OTSA-Core.

## 2. Yêu cầu, vấn đề và kết quả từng việc

Số thứ tự theo giao việc OTSD/OTSA ngày21–22/10, khác bảng chín việc lịch sử.
Các kết quả dưới đây tổng hợp hồ sơ đã có; lượt viết báo cáo không đo lại máy.

### Việc1 — Thu thập telemetry

**Yêu cầu:** ghi chỉ số hệ thống, interface, kết nối và cổng lắng nghe để Wazuh
thu thập; tài nguyên thấp, log có giới hạn, tự chạy sau reboot.

**Khó khăn:** cần phân biệt số đo CPU toàn máy với chi phí riêng collector,
không đếm trùng socket/interface và không ghi snapshot rỗng khi lệnh đo lỗi.
Bản đầu start tay được nhưng không tự chạy sau boot do enable file sai vị trí.

**Xử lý:** xây collector JSON Lines, dùng thông tin FreeBSD/libxo; gom chủ sở
hữu socket, xoay log bằng newsyslog, tích hợp localfile Wazuh. Chuyển template
khởi động về đúng `/etc/rc.conf.d/otsd_telemetry`, dùng daemon supervisor.

**Kiểm thử/kết quả:** bài đo3.600,18s/120mẫu, CPU riêng collector trung bình
0,3594%, max0,7976%; log tối đa975.160byte. Reboot thật chứng minh telemetry
và Wazuh tự chạy. Trên `.36` ngày23/10 service còn chạy và có metrics mới.

**Trạng thái/giới hạn:** đạt các bài đo và boot; nhật ký ghi Dương xác nhận
ingest. Không coi kết quả ingest ở một mốc là chứng minh mọi Manager/agent
hiện đều kết nối; không coi CPU trong record metrics là CPU riêng collector.

### Việc2 — Tự cấp/gia hạn chứng chỉ thiết bị

**Yêu cầu:** OTSA tự xin chứng chỉ theo danh tính agent, dùng mTLS tải nội dung,
giữ private key và gia hạn mà không làm hỏng lựa chọn System Trust.

**Khó khăn:** lần đầu phải có cơ sở tin CA; phản hồi cần gắn đúng yêu cầu để
tránh replay; cert/client key phải khớp, danh tính/CA/hostname đúng. Nếu gia
hạn tạo refid mới thì GUI có thể vẫn chọn cert cũ.

**Xử lý:** CSR/HMAC v2 ràng buộc identity/timestamp/nonce/CSR hash; kiểm MAC
nguyên byte phản hồi rồi mới nhận vật liệu chứng chỉ, kiểm cert/key/chain.
Lưu generation root-only, đồng bộ Trust giữ refid, giữ khóa khi gia hạn.
Bổ sung pin SHA256 của CA và chuẩn hóa URL để không lặp `/otsa`.

**Kiểm thử/kết quả:** các ca MAC sai, CN/key sai, TLS không tin, HTTP lỗi,
gia hạn và giữ khóa/refid đã kiểm trên mock; có bài boot không gọi mạng khi
cert chưa tới hạn. Bổ sung pin/path có12unit và15ca/nhóm integration đạt.

**Trạng thái/giới hạn:** v2 được Dương xác nhận đạt. Pin-only dựa server gửi
CA được pin trong chain, vẫn kiểm TLS/hostname. Bootstrap lab không tự áp dụng
production; enrollment chứng chỉ OTSD khác cơ chế enrollment Wazuh Manager.

### Việc3 — Tập luật Suricata, alias và policy PF

**Yêu cầu:** tải luật/danh sách IP từ OTSD bằng chứng chỉ, kiểm trước khi nạp,
whitelist trước blacklist và bảo vệ đường quản trị; hook còn sau cập nhật Core.

**Khó khăn:** downloader native chưa có luồng Trust/mTLS/hash OTSD; nội dung
sai không được thay bản tốt. Bốn luật PF từng đặt alias sai phía nguồn/đích.
Default allow đứng trước có thể khớp `quick` khiến luật chặn phía sau vô hiệu.
Chép cả golden cũ sau mọi lần nâng Core lại có thể xóa sửa đổi của Core mới.

**Xử lý:** tích hợp transport và cổng kiểm/staging vào downloader Suricata,
URI alias và installRules; dùng `suricata -T`. Sửa LAN `in` xét alias ở đích,
`out` ở nguồn; bốn `[OTSA-policy]` đi trước, Default allow được dời xuống
`≥100` trong bản dựng thật. Hook đưa vào OTSA-Core; golden chỉ là lưới an toàn
có kiểm baseline/marker phù hợp, Core lạ phải cảnh báo thay vì chép đè mù.

**Kiểm thử/kết quả:** gói thật từ192.168.56.99 tới203.0.113.7 bị chặn, tới
192.0.2.10 qua, có filterlog/counter. Hoàng xác nhận phép cài lại Core tự phục
hồi và B4 đã thực hiện; hồ sơ23/10 còn có unit/fixture kiểm golden sai hash,
stock hợp lệ, Core mới có marker và Core lạ không dấu.

**Trạng thái/giới hạn:** Dương xác nhận PF đạt, Hoàng xác nhận các phản hồi
đã xử lý. Phải phân biệt source/build với runtime: trên `.36`, lần kiểm23/10
ba golden có marker nhưng ba Core thật chưa có marker, được giữ nguyên; bài
fixture không tự chứng minh đã vá/cài lại Core thật trên máy này.

### Việc4 — Nạp firewall đúng thứ tự và tự xác nhận khi chạy lịch

**Yêu cầu:** nhận JSON UTF-8, chỉ đồng bộ luật OTSD, giữ luật nhà máy; bỏ qua
bản không đổi, xóa tập luật chỉ khi có `remove_all:true`. Cả nhóm OTSD phải
được xét sau bốn policy và trước luật nhà máy; cron tự confirm nếu còn đường
mTLS OTSD, mất đường thì watchdog hoàn tác sau deadline180s.

**Khó khăn1 — `≥100` chưa giải quyết được thứ tự nhóm luật:** dời Default allow
xuống100 giúp Việc3, nhưng OTSD gửi12luật sequence10,20,…120 thì luật cuối
vẫn có thể nằm sau Default allow100. Sequence cũng có thể trùng luật tay.
Do `quick`, gói đã được pass trước đó không tới luật block phía sau. Chỉ đẩy
Default allow lên một số lớn hơn nữa không giải quyết tổng quát va chạm và
việc số lượng luật OTSD thay đổi.

**Xử lý thứ tự:** tách **remote sequence** (thứ tự/slot OTSD), **native sequence**
(vị trí trên OPNsense) và **UUID** (danh tính rule). Xếp nhóm OTSD liên tiếp sau
bốn policy; lưu remote slot→UUID trong `slots.json`. Dời sequence luật nhà máy
khi cần, giữ UUID, nội dung và thứ tự tương đối; journal lưu cả mapping/model
trước–sau để undo. Không từ chối chỉ vì remote sequence trùng luật nhà máy.

```text
Ví dụ khi policy là1…4:
  OTSD remote10…120 → native5…16
  luật tay đang native10 → native17, giữ UUID/nội dung
  Default allow100 giữ nguyên nếu đã sau cả nhóm
```

**Điều kiện bài đo thực tế:** Default allow của VM đã là50000/50001 từ trạng
thái thử trước. Đã chủ động tạo luật tay native10 trùng remote slot10 để chứng
minh xử lý va chạm: nhóm OTSD thành5…16, luật tay thành17. Không gọi đây là
bài đo trực tiếp với Default allow100, cũng không lấy việc Default allow đã
nằm rất xa làm bằng chứng duy nhất.

**Khó khăn2 — reload thành công chưa chứng minh còn đường điều khiển:** PF
state cũ có thể cho kết nối đã mở tiếp tục sống dù luật mới chặn kết nối mới;
probe có thể kết thúc sau deadline hoặc cấu hình bị sửa khi đang chờ mạng.

**Xử lý giao dịch:** arm watchdog trước khi PHP save; backup/journal rồi áp
delta, kiểm thứ tự PF kernel. Pending→probe `/whoami` bằng kết nối mTLS mới,
không dùng lại state; kiểm identity, boot/deadline và fingerprint XML/PF/mapping
trước commit. Confirm tay và auto dùng chung guard. Lỗi thì không gia hạn
deadline, không ghi hash thành công; watchdog undo/reload đúng giao dịch.

**Khó khăn môi trường:** còn trạng thái pending cũ, timer VM/SSH chậm, Model
cache/reference, guard chặn cả legacy SSH và mock mất sau reboot. Đã xử lý
baseline/clock, tạo lại Model đúng vòng đời, thu hẹp ngoại lệ SSH bằng điều
kiện thực của rule và phục hồi fixture mTLS. Có lỗi observer/harness được giữ
trong hồ sơ; không bỏ bước gói thật hoặc gọi confirm tay thay cron để lấy PASS.

**Kiểm thử/kết quả:**

- Có listener thật trước thử; luật thứ12 chặn502 và Firewall Log khớp UUID/IP/
  cổng. Đổi502→503: UUID giữ nguyên, delta sửa1;502 qua,503 bị chặn.
- Native cron gọi configctl/configd, không gọi loader/confirm tay; luật an toàn
  tự committed, giữ qua deadline và bản không đổi trả no-op.
- Bài chặn đường OTSD đi qua WAN/PF tới10.0.2.2:8444 rồi tunnel về mock, tránh
  loopback bị skip. Probe mới thất bại, có log chặn, watchdog undo rồi mTLS mới
  phục hồi trong khi mock vẫn chạy. Không lấy server tắt làm lỗi firewall.
- Watchdog hẹn180s; hoàn tất khoảng186,2s gồm native save/reload, không tuyên
  bố hoàn tất chính xác180,000s. Local82Python/25PHP, FreeBSD25PHP và pkg check đạt.

**Trạng thái/giới hạn:** hai bổ sung đạt dev với policy0.1_6, Hoàng xác nhận
xử lý xong. Sau thử đã dọn luật/fixture và phục hồi baseline. Hỗ trợ priority
nhóm một interface; floating/group chưa tổng quát. Watchdog không sống qua
reboot; probe đúng chỉ chứng minh đường OTSD tại thời điểm kiểm, không chứng
minh mọi lưu lượng nhà máy. Việc6 sau đó bổ sung scheduler tự bật khi đủ cấu hình.

Nguồn giải thích thiết kế/khó khăn:
[Ghi chú học tập Việc4](C:/work/opnsense/otsa-viec4-fix-20261022/GHI-CHU-HOC-TAP-VIEC4_ThuTu_AutoConfirm.md).

### Việc5 — Bộ phát hành mẫu và khóa ký

**Yêu cầu:** bộ tar không nén đúng cấu trúc, repo pkg có gói mới hơn bản nền;
manifest/SHA256SUMS có chữ ký để OTSD nhập, hash phủ đủ payload.

**Khó khăn:** thiếu private key khớp repo trust cũ; phải tách khóa ký bộ với
khóa repo và khóa mTLS. Có symlink catalog nội bộ, lỗi CRLF build và trường
hợp pkg update báo exit0 dù xác thực catalog thất bại.

**Xử lý:** dùng hai khóa lab được duyệt, private key giữ trên dev; ký catalog
và hai tệp gốc. Neo manifest→SHA256SUMS→payload, kiểm tập đường dẫn và symlink;
build riêng, chuẩn LF trong staging. Test repo bằng DB/cache/trust riêng, kiểm
stderr cùng catalog/rquery usable, không chỉ tin exitcode.

**Kiểm thử/kết quả:** OTSD nhập `otsa-1.2.0.tar` thành công, hai chữ ký Verified,
hash8/8 và chuỗi băm khớp; tải mTLS cả hai symlink `.tzst`, Range đạt.

**Trạng thái/giới hạn:** Dương xác nhận đạt. Khóa ký bộ công khai gửi OTSD;
tin catalog pkg là việc OTSA. Lab key không mặc nhiên thành khóa production;
không sửa bộ đã ký chỉ để cập nhật câu trạng thái.

### Việc6 — Tải đủ rồi cài từ kho local

**Yêu cầu:** poll5phút bằng mTLS; tải/kiểm cả bộ trước cài, hỗ trợ tải tiếp,
confirm/auto; hỏi lại assignment ngay trước cài; offline chỉ trong600s; tạo
ZFS BE, kiểm bản sau cài và ghi receipt. Upgrade sets luôn qua xác nhận.

**Khó khăn:** assignment có thể bị đổi/hủy khi đang tải hoặc trước confirm;
TLS/503 không được giả thành offline hợp lệ. Worker, GUI, cron và native
firmware có thể chạy đồng thời; pkg exit/solver khác giữa2.3.1 và2.8.4.
Bật lịch cứng trên máy chưa có OTSD/chứng chỉ gây gọi lỗi không cần thiết.

**Xử lý:** worker chia download→ready→review→preflight→install, kiểm lại hash,
inventory và plan_id, giữ khóa worker/firmware. Repo file:// duy nhất với trust
riêng, allowlist gói; BE trước cài, kiểm version thực rồi mới ghi receipt.
Scheduler tính điều kiện endpoint/System Trust cục bộ, tự bật hai job PF/package
khi đủ và tắt trước mạng khi thiếu; không tự bật execution. Sets dùng adapter
native riêng, confirm, verify và trạng thái reboot_pending/kiểm sau boot.

**Kiểm thử/kết quả:** cài thật telemetry0.1_2→0.1_3(confirm)→0.1_4(auto) trên
`.36`; đổi assignment thì hủy, chờ681,893s thì không cài, BE/receipt đối chiếu.
Range206/416, tải1GiB và GUI tiến độ đạt; cron thật đo chu kỳ khoảng300s,
mất cert thì dừng trước mạng. Hồi quy bổ sung182Python update/91Python policy,
57PHP update/controller+8TLS/schedule; có9ca fault injection I/O/space/journal.

**Trạng thái/giới hạn:** Hoàng xác nhận hoàn thành24/10; hồ sơ23/10 ghi Dương
“Việc6 ổn rồi”. Đã triển khai update0.9_5, policy0.1_10, enroll0.1_1 lên `.36`.
Sets có code/test cô lập, chưa cài base/kernel/reboot thật; chưa coi các ca
production renewal, GUI user hạn chế hay đĩa đầy vật lý là đã nghiệm thu.

### Công việc nền đã làm trước sáu việc

- Khảo sát Task11 dẫn tới tách kênh log/điều khiển Wazuh và artifact HTTPS;
  báo cáo F8/F9 ghi sửa timeout On-demand/khép vòng phản hồi trong lab cũ.
- Đối chiếu Core/menu/theme, tích hợp các trang Updates/Plugins/Packages,
  Trusted Keys, TLS và OT Rules, kiểm GUI/API/CSRF.
- Rollback Points tái sử dụng native: tạo/activate BE, boot thử và về default
  với file dấu mốc. Không suy thành phục hồi mọi workload sau nâng cấp thật.
- Ghi nhận đường Windows WireGuard/VM NAT; không coi là đã có peer VPN riêng
  trong VM. Trạng thái từng đợt nằm ở hồ sơ nguồn, không gộp mọi lab thành
  một lần nghiệm thu production.

## 3. Kiểm thử và kiểm soát an toàn đáng chú ý

- Chứng chỉ sai/không được tin, hash sai, nội dung không hợp lệ và quyền không
  đủ bị từ chối; không bỏ kiểm TLS/chữ ký để vượt bài thử.
- Luật OTSD có nhận diện sở hữu, bảo vệ luật nhà máy. Bài cron Việc 4 giữ luật
  khi xác nhận thành công; khi luật chặn đường OTSD thì watchdog hẹn 180 giây
  hoàn tác. Lượt đo hoàn tất khoảng 186,2 giây gồm thời gian reload native.
- Việc 6 đã kiểm đứt tải, assignment đổi trước cài, mất kết nối trong hạn và
  quá hạn 600 giây; có ảnh GUI và ghi nhận phiên bản sau cài thật.
- Bổ sung Việc6: Range206/416 và tải1GiB qua mTLS có hash đúng; GUI cập nhật
  tiến độ khi worker tải nền, chưa đủ thì nút cài khóa. Native cron PF/package
  đo khoảng300,444s/299,250s. Hồi quy gói bổ sung: **182 ca Python update,
  91 ca Python policy**, 57 kiểm tra PHP update/controller và8 TLS/schedule đạt.
  Các số này thuộc từng lượt kiểm, không phải số lần cài runtime. Lượt unit
  `.36` ngày22/10 là115Python/52PHP, được giữ như bằng chứng lịch sử.
- Repo lab được tin trong phạm vi kiểm thử riêng từng lệnh; không thay trust
  repo runtime toàn cục. Khóa riêng ký bộ/repo được giữ trên VM dev, không
  nằm trong bộ phát hành bàn giao.

## 4. Môi trường và trạng thái hiện tại

| Môi trường | Vai trò và trạng thái đã ghi nhận |
|---|---|
| Dev `192.168.56.56` | Phát triển mã nguồn, build và kiểm thử trước; không phải bản sao toàn bộ máy thật |
| Kiểm thử `10.30.20.36` | Hồ sơ triển khai23/10 ghi update `0.9_5`, policy `0.1_10`, enroll `0.1_1`; telemetry giữ `0.1_4`, receipt bộ `1.2.1`; checksum các gói triển khai đạt, có BE trước cài |
| OTSA `.35` / OTSD `.25` | Đích tích hợp thực tế theo giao việc; không tự triển khai vào các máy này trong đợt Việc 5–6 |

Máy chủ giả và fixture thử đã dọn. Sau triển khai lịch mới, `.36` chưa
provision OTSD: hai worker PF/package tắt với `schedule_endpoint_missing`;
**supervisor cục bộ vẫn chạy5phút/lần**, không hỏi mạng, chờ cấu hình/chứng chỉ.
Supervisor không tự bật quyền cài package/sets hay đổi confirm/auto. Chưa nâng
Core/base/kernel, activate/restore BE hoặc reboot `.36` trong các lượt Việc6.
Đây là trạng thái theo hồ sơ23/10, không phải khảo sát máy mới ngày24/10.

## 5. Phần sau nghiệm thu và giới hạn triển khai

**Việc6 được ghi nhận đã hoàn thành theo xác nhận Hoàng**, không còn đặt việc
hoàn thiện nhánh update/lịch thành đầu việc chưa xong. Những phần sau thuộc
kiểm chứng production hoặc mở rộng có điều kiện:

1. `kind=upgrade` đã nối `package_sets.py`: yêu cầu confirm và profile native,
   kiểm sets/chữ ký, giữ trạng thái chờ reboot, xác minh sau boot rồi ghi receipt.
   Đã code/build/test cô lập; chưa có bằng chứng cài sets ký hợp lệ và reboot
   thật. Không dùng nghiệm thu update để khẳng định base/kernel đã được thử.
2. Tích hợp endpoint/assignment, identity, Trust và khóa chính thức của OTSD;
   kiểm renewal production và tài khoản GUI hạn chế. Tải1GiB thử dùng dữ liệu
   nén tốt, chưa thay thế mọi bộ production hoặc bài đĩa đầy vật lý.
3. Phát hành đúng source/gói đã đối chiếu, vận hành theo lịch quản lý mới;
   tạm dừng lâu dài bằng `schedule.json` với `paused:true` và đồng bộ lịch,
   không chỉ sửa `enabled` rồi cho rằng supervisor sẽ giữ nguyên.

