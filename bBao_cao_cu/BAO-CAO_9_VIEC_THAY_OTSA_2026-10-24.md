# Báo cáo chín việc OTSA của Thầy

Hoàng — chuẩn bị báo cáo chiều 24/10/2026, múi giờ Asia/Saigon.

Báo cáo tổng hợp hồ sơ và xác nhận hiện có, gồm các kết quả mới ngày23/10.
Lượt lập báo cáo này chỉ đọc tài liệu local, không khảo sát lại hoặc thay máy.
Sáu việc Dương là nhóm tích hợp liên quan, có số thứ tự khác chín việc Thầy.

## Tổng hợp để báo Thầy

| Mục | Nội dung | Trạng thái có thể báo |
| --- | --- | --- |
| 1 | VPN local–OTSD | Hoàng cho bỏ qua đợt này |
| 2 | Trusted Keys | Có inventory GUI/API; Hoàng đã kiểm và đồng ý tạm giữ |
| 3 | Rollback Points | Hoàn thành phạm vi GUI/API, demo khôi phục file trên lab và tài liệu |
| 4 | Lọc Software Update theo OTSD | Đã code và kiểm lab ba tab; chưa nghiệm thu catalog OTSD thật |
| 5 | Suricata và phần chứng chỉ/System Trust liên quan | Có source/tích hợp và kết quả lab; Hoàng xác nhận phản hồi Dương đã xử lý; chưa nghiệm thu production |
| 6 | Tự hỏi cập nhật, xác nhận upgrade | Dương xác nhận “Việc6 ổn rồi”; có kiểm cài thật lab và bổ sung lịch đã cài .36; vẫn còn giới hạn sets/production |
| 7 | Wrapper Wazuh FreeBSD và mTLS | Khảo sát/native test đạt; phần nối chứng chỉ trong wrapper chưa sửa, chờ Hoàng hỏi ý kiến Thầy |
| 8 | Tách Software Update thành plugin | Đã có plugin riêng, build/cài và kiểm GUI/API; tái sử dụng nền Core/pkg/ZFS |
| 9 | Kịch bản truyền file | Có luồng và bằng chứng tải lab trước đây; chưa diễn tập mới bài nhỏ theo yêu cầu gần nhất |

## 1 VPN local với OTSD

**Quyết định:** Hoàng cho bỏ qua trong đợt này. Không triển khai thêm peer,
routing hoặc VPN riêng trên thiết bị để hoàn thành các mục còn lại.

**Chưa làm:** nghiệm thu VPN cho triển khai thực tế. Không gọi mục này là đã
hoàn thành kỹ thuật; đây là mục được loại khỏi phạm vi đợt báo cáo.

## 2 Trusted Keys

**Đã làm:** giao diện và API inventory khóa/fingerprint của kho OTSA; có kiểm
hiển thị, tìm kiếm, làm mới và lỗi/phục hồi trên lab. Hoàng vừa kiểm lại và
đồng ý giữ tạm hiện trạng.

**Chưa làm:** màn quản trị đầy đủ nhập/đổi/thu hồi khóa nếu sau này cần.
Inventory chỉ cho biết khóa đang có, không tự chứng minh chữ ký của một bộ
phát hành đã được xác minh. Chữ ký bộ, khóa tin cậy repo pkg và cert mTLS có
vai trò khác nhau.

**Cách chốt:** tạm ổn theo phạm vi đã thống nhất, chưa mở rộng tính năng.

## 3 Giao diện Rollback Points kiểm thử và tài liệu

**Đã làm:** tích hợp đường dẫn trong System → Software Update → Rollback Points,
dùng trang `/ui/core/snapshots`, API/configd và ZFS Boot Environments của Core.
Đã rà đường đi từ GUI/API tới native; không viết lại trình khôi phục VM.

**Bài demo mới ngày23/10 trên dev192.168.56.56:**

1. Tạo BE riêng qua API trong phiên GUI, danh sách tăng8→9.
2. Activate, kiểm đúng trạng thái BE hiện chạy và BE cho lần boot sau.
3. Dùng boot thử một lần, reboot vào BE mới; root dataset đúng, file dấu mốc
   trở về `before` và hash khớp.
4. Chọn `default`, reboot lần hai; file `after` và hash đúng, cuối lượt default NR.
5. Kiểm thêm nút Activate thật trên GUI; GET không gây thay đổi, thiếu CSRF bị403,
   tên trùng/sai bị từ chối, không tạo BE ngoài bài thử.

Có20 điều kiện đối chiếu tổng hợp đạt, lưu hồ sơ gồm13 ảnh cùng JSON,
log, script và checksum. Đây không phải20 ca nâng cấp độc lập. Đã viết báo cáo,
hướng dẫn sử dụng, kịch bản và bản đồ source.

**Cuối lượt:** dev về default, pool khỏe; cấu hình/identity/inventory/cron/PF
hiệu lực giữ nguyên. File marker default đã dọn, giữ BE thử inactive làm chứng
cứ. rules.debug đổi hash sau boot; không khẳng định mọi file giữ nguyên byte.

**Chưa kiểm:** user hạn chế, clone/rename/delete, rollback sau nâng package/
base/kernel thật hoặc trên .36. BE không bao phủ dataset ngoài BE và không thay
thế backup toàn máy.

**Cách chốt:** tạm hoàn thành đúng phạm vi Thầy giao về GUI/API, kiểm thử demo
lab và tài liệu. Không gọi đây là nghiệm thu khôi phục mọi loại sự cố.

Hồ sơ: [báo cáo Rollback](C:/work/opnsense/otsa-rollback-demo-20261023/BAO-CAO-GUI-THAY.md),
[hướng dẫn](C:/work/opnsense/otsa-rollback-demo-20261023/HUONG-DAN-ROLLBACK.md),
[chỉ mục lệnh và bằng chứng](C:/work/opnsense/otsa-rollback-demo-20261023/LENH-VA-LOG.md).

## 4 Lọc Software Update theo repo OTSD

**Đã làm:** backend và ba tab Updates/Plugins/Packages lọc theo repo OTSD, có
kiểm catalog/cache, hiển thị và tình huống lỗi trong lab. Không lấy toàn bộ
repo OPNsense thông thường làm catalog OTSD.

**Chưa làm:** nghiệm thu E2E với catalog/assignment của OTSD thật tại .25.
Kết quả fixture hoặc repo lab không thay thế bước đó.

**Cách chốt:** phần OTSA đã có và đã kiểm lab; giữ nguyên, gom bước server thật
vào buổi tích hợp khi được phép.

## 5 Suricata và phần chứng chỉ liên quan

**Đã làm:** tận dụng kết quả Việc3 Dương: bộ tải rules/IP có hỗ trợ cert client
và kiểm server cho URL OTSD, nguồn firewall/detection riêng, alias/PF và các
Core hooks liên quan. Có bằng chứng lab; Hoàng xác nhận các phản hồi Dương về
chiều policy, hooks và việc giữ hooks đã được xử lý.

System Trust đã có lựa chọn CA/client cert theo refid, kiểm các điều kiện cert/
key và phục vụ luồng mTLS lab; dữ liệu bí mật không được trả qua API metadata.
Không đồng nhất cert web GUI với cert client dùng để tải từ OTSD.

**Giới hạn theo mốc .36 mới:** policy0.1_10 có golden/restorer đã kiểm9unit và
4fixture. Ba golden có marker/hash đúng, nhưng ba Core thật trên .36 chưa có
marker và được giữ nguyên trong lượt triển khai. Không suy việc cài policy là
đã thay Core thật hoặc đã nạp rules production.

**Chưa nghiệm thu:** endpoint/cert/chain và tải–áp dụng trên OTSD production.
Không mở lại các phản hồi đã xác nhận chỉ vì bước production chưa diễn ra.

## 6 Tự query cập nhật và xác nhận upgrade

Phần này do chat Việc6 Dương thực hiện; báo cáo này chỉ đối chiếu kết quả.

**Đã làm và được xác nhận:** Dương phản hồi “Việc6 ổn rồi”. OTSA tự hỏi định kỳ,
tải đủ bộ, kiểm hash, tải tiếp khi đứt và hỏi lại assignment trước khi cài.
`kind=update` theo confirm/auto được giao; `kind=upgrade` luôn qua xác nhận.

Đã có cài telemetry thật trên .36 từ0.1_2→0.1_3→0.1_4, repo local có chữ ký,
tạo BE trước cài, receipt, chặn assignment thay đổi và cửa sổ offline600giây.
Có kiểm GUI tiến độ tải1GiB, Range/416, cron/mTLS và các ca lỗi cô lập.

**Bổ sung mới đã triển khai .36:** update0.9_5, policy0.1_10, enroll0.1_1;
telemetry giữ0.1_4. Có BE trước cài và pkg checks đạt. Hai worker hiện tắt vì
chưa provision endpoint/chứng chỉ OTSD; supervisor cục bộ kiểm điều kiện mỗi
5phút. Không gọi đây là đang hỏi OTSD thật mỗi5phút.

**Còn giới hạn:** cài/boot sets base/kernel thật chưa nghiệm thu; adapter đã có
nhưng khóa mặc định tắt. User hạn chế, renewal production và OTSD thật chưa đủ
bằng chứng. Các fault tests không chứng minh mất điện/đĩa đầy vật lý thật.

**Cách chốt:** ghi nhận xác nhận của Dương và các bổ sung đã triển khai; tách
riêng giới hạn production, không phủ nhận toàn bộ kết quả hoặc nói mọi nhánh
đều đã nghiệm thu.

Nguồn: [bổ sung lịch và kiểm thử](C:/work/opnsense/BanGiao_Duong_2026-10-23/Viec6_BoSung_Lich/BAO-CAO-BO-SUNG.md),
[triển khai .36](C:/work/opnsense/BanGiao_Duong_2026-10-23/TrienKhai_Lich36/KET-QUA-TRIEN-KHAI.md).

## 7 Wrapper Wazuh agent FreeBSD và mTLS

**Phạm vi Thầy đã xác nhận:** xem bộ CA, cert thiết bị và private key dùng với
OTSD có thể đi qua wrapper OPNsense để Wazuh agent FreeBSD dùng khi đăng ký
mTLS với Manager hay không.

**Đã làm:** rà form/model/API/template/rc của wrapper và native4.14.7. Có25
check, gồm6ca parser native; sửa source hai maxport65536→65535, chưa build/cài
bản sửa đó. Makefile1.4 có từ trước không chứng minh mTLS mới đã phát hành.

Kiểm tiếp bằng cert/key OTSD lab hiện hữu:
- 8ca công cụ agent-auth đạt theo kỳ vọng.
- 4ca daemon wazuh-agentd đọc XML đạt; hai bộ cert hợp lệ bắt tay TLS1.3, trình
  đúng fingerprint và nhận phản hồi đăng ký giả lập.
- Sai CA, thiếu cert, key không khớp hoặc không có quyền đọc bị từ chối trong
  các nhóm kiểm tương ứng.
- Daemon chạy user wazuh không đọc được private key gốc root0600. Staging riêng
  với quyền phù hợp đã cho daemon đọc và dùng được.

Native binary và TLS là thật; phía Manager là Python TLS/protocol double,
không phải Wazuh Manager thật. Hai bộ auto-enroll và System Trust có CA khác
fingerprint; không được mặc định là cùng một bộ vì trùng tên.

**Chưa làm:** phần cấu hình CA/cert và materialize trong wrapper, sinh các đường
dẫn enrollment, xử lý refresh khi gia hạn; chưa có Apply GUI→daemon E2E hoặc
nghiệm thu Manager thật. Chưa build/cài wrapper có tính năng mới. Không dùng
enrollment mTLS để kết luận kênh sự kiện1514 cũng dùng TLS.

**Đề xuất xin Thầy:** nếu tiếp tục, bổ sung lựa chọn CA/cert trên form, chuẩn
bị file riêng đúng quyền, kiểm hợp lệ và sinh cấu hình cho daemon. Phạm vi là
model/form/template/helper của plugin, không cần sửa mã C Wazuh hoặc luồng
download của Dương. Theo Hoàng, đang dừng ở khảo sát/báo cáo để hỏi Thầy trước.

Hồ sơ: [báo cáo Wazuh và đề xuất](C:/work/opnsense/otsa-wazuh-mtls-survey-20261023/BAO-CAO-GUI-THAY-20261024.md).

## 8 Tách Software Update thành plugin

**Đã làm:** có plugin os-otsa-update riêng cho phần OTSA: menu, GUI/API, catalog,
download/hash/progress, chính sách xác nhận và worker/adapters. Đã build/cài
trên lab và .36 theo các phiên bản trong hồ sơ. Tái sử dụng pkg, System Trust,
Core snapshots/ZFS; các trang bảo trì Core giữ liên kết có sẵn.

**Chưa làm:** không có kết quả triển khai production .35 hoặc tích hợp server
thật. Các giới hạn từng chức năng ghi tại mục2/3/4/6/9; không tính chúng thành
yêu cầu phải viết lại toàn bộ plugin/nền Core.

**Cách chốt:** yêu cầu tách plugin đã thực hiện; hoàn thiện tiếp theo là các
tính năng cụ thể hoặc đóng gói/phát hành khi được giao.

## 9 Kịch bản truyền file

**Luồng đã thống nhất:** quản trị đưa file/bộ lên OTSD; OTSD giao bản cho thiết
bị; OTSA tự hỏi/tải qua HTTPS mTLS, kiểm tra rồi lưu/áp dụng bằng thành phần
phù hợp. Không xây upload quản trị lên OTSA. File lớn không bắt buộc truyền
xuyên Wazuh agent.

**Đã có:** File Transfers tải rules từ mock qua mTLS, kiểm SHA256, lưu vùng chờ
và hiển thị tên/byte/hash/các bước. Có kiểm cert/hash sai từ các lượt trước.
Luồng package riêng đã có tải/GUI/cài lab ở mục6. Hai dòng thông báo thử mà
Hoàng yêu cầu bỏ đã được bỏ trong source và từng vá .36.

**Chưa làm trong chat này:** chưa chạy mới một bài demo nhỏ File Transfers theo
yêu cầu gần nhất của Thầy sau khi làm rõ phạm vi. Không lấy demo Rollback hoặc
test enrollment Wazuh thay cho bài demo tải file này. Chưa nghiệm thu OTSD thật.

**Bài demo nhỏ có thể chuẩn bị:** một rules mẫu và manifest trên mock riêng →
Query → tải → kiểm hash → đối chiếu file thực và trạng thái web → lưu ảnh/log.
Chỉ lưu vùng chờ, không cần nạp PF/Suricata hoặc nâng cấp để chứng minh tải.
Chưa triển khai bài này chỉ vì đang viết báo cáo.

## Những ý cần chốt với Thầy chiều nay

1. Rollback tạm chốt phạm vi GUI/API, demo lab và tài liệu; Trusted Keys giữ tạm.
2. Wazuh đã chứng minh khả năng native bằng cert OTSD lab; xin ý kiến có bổ sung
   phần nối trong wrapper không. Chưa tự sửa phần code này.
3. Xác nhận phạm vi bài truyền file nhỏ: tải/kiểm/hiển thị trên web bằng mock,
   tách khỏi nghiệm thu OTSD production.
4. Các phần đã được Dương xác nhận tiếp tục giữ kết quả; không tự chạy lại hoặc
   thay đổi máy chỉ để có thêm báo cáo. GitLab/push/merge chưa thực hiện trong chat này.

## Trạng thái máy theo hồ sơ gần nhất

| Máy | Mốc đã biết, không phải khảo sát mới ngày24/10 |
| --- | --- |
| Dev192.168.56.56 | Update0.9_2, policy0.1_8, telemetry0.1_2, enroll0.1; wrapperWazuh1.3_1/native4.14.7. Bài rollback cuối defaultNR, BE thử inactive |
| 10.30.20.36 | Update0.9_5, policy0.1_10, enroll0.1_1, telemetry0.1_4; worker tắt do chưa provision, supervisor cục bộ5phút |
| 10.30.20.25 | Endpoint OTSD dự kiến; theo Hoàng chưa được phép thử thật, không tự truy cập |
| 10.30.20.35 | Live; không thao tác trong các lượt Wazuh/Rollback này |

Nguồn mốc mới: CAP-NHAT_OTSA_Viec3-6_2026-10-22.md, TienDo_9_Viec_OTSA_2026-10-18.md,
các báo cáo/RESULT được dẫn ở trên. Bảng và nhật ký phiên bản cũ ở phần lịch
sử không thay thế mốc triển khai mới nhất.
