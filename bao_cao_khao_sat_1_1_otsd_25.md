# Báo cáo Khảo sát Nguồn dữ liệu Thực tế (Mục 1.1) — Hệ thống OTSD – OTSA – Wazuh

> [!NOTE]
> **Thông tin đợt khảo sát:**

> - **Đối tượng khảo sát trực tiếp:** `KC01.04-OTSD-Dev-CI-Live` (`10.30.20.25`) qua OpenSearch (`:9200`), Wazuh Dashboard (`:443`) và Wazuh Server API (`:55000`) — **100% truy vấn chỉ đọc (`GET` / `_search` không thay đổi dữ liệu)**.
> - **Đối chiếu tài liệu:** Bộ tài liệu `OT-CI` tại [ot-ci-readonly](file:///C:/work/opnsense/OTSA_BAN_GIAO/07_CHUAN_BI_GITLAB/ot-ci-readonly/README.md) (commit `fd98958`, ngày `2026-10-24`).

---

## 1. Xác minh phiên bản & tình trạng hạ tầng lab (Mới nhất `2026-11-26`)

| Thành phần | Tài liệu `OT-CI` (2026-10-24) | Khảo sát LIVE trên `10.30.20.25` (2026-11-26) | Kết luận |
| :--- | :--- | :--- | :--- |
| **Wazuh Manager & API** | `4.14.9` | **`4.14.9`** (`revision: rc2`, `hostname: wazuh.manager`) | **Khớp 100% — Mới nhất** |
| **OpenSearch Dashboards (OSD)** | `2.19.6` | **`2.19.6`** (`build_number: 414902`, `build_hash: 25c7cb0e...`) | **Khớp 100% — Mới nhất** |
| **OpenSearch / Wazuh Indexer** | `wazuh-indexer:4.14.9` | `wazuh-cluster`, Lucene `9.12.3` (`build_date: 2026-10-08`) | Hoạt động bình thường (`green`) |
| **Cổng kết nối `10.30.20.25` (CI-Live)** | 443, 9200, 55000 | **Mở cả 3 cổng** (`200 OK`) | Dùng khảo sát & lấy log thật tốt |
| **Cổng kết nối `10.30.20.26` (Dev-CI)** | 443 | **Không kết nối được** tại thời điểm kiểm tra | Cần hỏi quản trị/nhóm xem máy đang tắt hay chặn mạng |
| **Cổng kết nối `10.30.20.10` (GitLab)** | 80 | **Mở** | Có thể clone `OTSD-Plugins`, `OTSD-Ruleset` |

**Danh sách 12 plugin OTSD + 5 plugin Wazuh đang chạy (`green`, đều phiên bản `@2.19.6`) trên `10.30.20.25`:**
- **Plugin OTSD (`OTSD-Plugins`):** `otsdAlerts`, `otsdAuth`, `otsdDeviceInfo`, `otsdDeviceMonitor`, `otsdHome`, `otsdLogs`, `otsdOrchestration`, `otsdPerformance`, `otsdReporting`, `otsdShared`, `otsdSystemConfig`, `otsdUserActivity`.
- **Plugin Wazuh:** `wazuh`, `wazuhCore`, `wazuhCheckUpdates`, `wazuhFilePush`, `wazuhMvpOverrides`.

> [!TIP]
> Toàn bộ hệ thống CI/CD của lab đã chạy ổn định chuẩn **OSD Plugin `@2.19.6`** trong repo `OTSD-Plugins` (thậm chí có sẵn thư viện dùng chung `otsdShared`). Công cụ của nhóm **nên chốt viết thành 1 plugin mới trong `OTSD-Plugins`** thay vì dựng backend FastAPI + iframe riêng.

---

## 2. Danh sách Index thực tế & khối lượng dữ liệu trên OpenSearch

Bỏ qua các index hệ thống bắt đầu bằng dấu `.` (như `.kibana_1`, `.kibana_otsd_audit`, `.kibana_otsd_dist_drafts`…), hệ thống hiện có các nhóm index nghiệp vụ sau:

| Mẫu Index | Khoảng ngày / Tên cụ thể | Số lượng bản ghi | Vai trò đối với đồ thị & 4 tab |
| :--- | :--- | ---: | :--- |
| **`wazuh-alerts-4.x-*`** | `2026.10.21` → `2026.11.26` *(37 index)* | **2.927** | **Tab Cảnh báo** & nguồn đồ thị chỉ gồm cảnh báo. Tuy nhiên **rất ít log mạng** (xem Mục 3.1). |
| **`wazuh-archives-4.x-*`** | `2026.10.25` → `2026.11.26` *(33 index)* | **6.367.927** | **Nguồn chính chứa log tường lửa OTSA bình thường (`pf`/`filterlog`: 22.506 dòng)!** Đã bật `logall_json`. |
| **`wazuh-states-inventory-packages-wazuh.manager`** | 1 index trạng thái | **1.058** | **Tab Phần mềm** (đọc thẳng OpenSearch hoặc qua Wazuh API `/syscollector/{id}/packages`). |
| **`wazuh-states-inventory-interfaces-wazuh.manager`** | 1 index trạng thái | **26** | Thông tin MAC, card mạng, trạng thái up/down cho khung chi tiết. |
| **`wazuh-states-inventory-networks-wazuh.manager`** | 1 index trạng thái | **10** | Địa chỉ IP từng interface của agent (hữu ích cho máy nhiều NIC). |
| **`wazuh-states-inventory-ports-wazuh.manager`** | 1 index trạng thái | **148** | Cổng đang lắng nghe trên các agent. |
| **`wazuh-states-inventory-system-wazuh.manager`** | 1 index trạng thái | **6** | Thông tin OS / phần cứng tổng quan của agent. |
| **`wazuh-states-vulnerabilities-wazuh.manager`** | 1 index trạng thái | **0** | **Tab Lỗ hổng** — index có sẵn nhưng hiện **trống** (xem Mục 3.6). |
| **`otsd-device-groups`** | 1 index tùy biến OTSD | **2** | Danh sách nhóm thiết bị OTSD (`section-01` "Section 01", `local-dev` "Local Dev"). |
| `wazuh-monitoring-*`, `wazuh-statistics-*` | Tuần `43w` → `48w` | — | Giám sát trạng thái Wazuh, không dùng vẽ đồ thị kết nối. |

---

## 3. Sáu phát hiện kỹ thuật trọng yếu (Ảnh hưởng trực tiếp tới thiết kế & code)

### 3.1. Xác nhận R1: `wazuh-alerts-*` gần như không có lưu lượng mạng, còn `wazuh-archives-*` bị "nhiễu" 92,5% bởi telemetry

Thống kê thực tế từ OpenSearch trên `10.30.20.25`:

| Chỉ số | `wazuh-alerts-4.x-*` (2.927 dòng) | `wazuh-archives-4.x-*` (6.367.927 dòng) |
| :--- | ---: | ---: |
| Có `data.srcip` *(pf / sshd)* | **6** *(0,2%)* | **22.509** *(0,35%)* |
| Có cả `data.srcip` & `data.dstip` *(pf `filterlog`)* | **3** | **22.506** *(22.338 `pass` + 168 `block`)* |
| Có `data.srcip` nhưng **thiếu `data.dstip`** *(sshd)* | **3** | **3** |
| Có `data.src_ip` & `data.dest_ip` *(Suricata `eve.json`)* | **80** | **181** |
| **Không có trường IP mạng** *(nhiễu / host log)* | **2.841** *(rootcheck 2100, sca 370, ossec 309, syscheck 59…)* | **6.345.237** *(riêng `/var/log/otsa/otsd-telemetry.json` chiếm **5.887.683 dòng = 92,5%**, `syscollector` 344.736 dòng)* |

> [!WARNING]
> **Hệ quả bắt buộc phải áp dụng ngay:**
> 1. Nếu demo GĐ1 chỉ mở `wazuh-alerts-*`, đồ thị hầu như trống trơn (chỉ có 3 bản ghi `pf` + 3 bản ghi `sshd` + 80 Suricata). **Nguồn đồ thị lưu lượng thực tế phải hỗ trợ `wazuh-archives-4.x-*`**!
> 2. Vì `wazuh-archives-*` chứa tới **5,89 triệu dòng `otsd-telemetry.json`**, mọi truy vấn đồ thị **bắt buộc** giữ điều kiện lọc `exists` trên trường IP nguồn (đã thêm ở lần sửa trước) hoặc lọc theo `decoder.name: pf` để không quét nhầm telemetry.

---

### 3.2. Phát hiện bất ngờ: Cùng trong 1 index tồn tại HAI bộ tên trường IP khác nhau

Trong cả `wazuh-alerts-*` và `wazuh-archives-*`, hai nguồn log mạng quan trọng nhất của OTSA lại dùng **hai schema hoàn toàn khác nhau**:

| Nguồn log trên OTSA | `location` | `decoder.name` | Trường IP nguồn / đích | Trường cổng đích | Trường hành động / mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tường lửa OPNsense (`filterlog`)** | `/var/ossec/logs/opnsense_syslog.log` | `pf` | `data.srcip` / `data.dstip` | `data.dstport` | `data.action` = **`"pass"`** hoặc **`"block"`** *(KHÔNG phải `allow`/`deny`!)* |
| **SSH (`sshd`)** | `/var/ossec/logs/opnsense_syslog.log` | `sshd` | `data.srcip` / *(thiếu `dstip` → dùng `agent.ip`)* | — | `rule.level` (`5`), `data.dstuser` |
| **IDS Suricata (luật OT)** | `/var/log/suricata/eve.json` | `json` | **`data.src_ip`** / **`data.dest_ip`** | `data.dest_port` *(nếu TCP/UDP)* | `data.alert.action` = `"allowed"`, `data.alert.severity` = `"1".."4"`, `rule.level` = `3` |

> [!IMPORTANT]
> **Tác động tới file `field mapping` & Query DSL:**
> - Nếu chỉ khai báo 1 cặp `srcIp: "data.srcip"` / `dstIp: "data.dstip"` cho `wazuh-alerts-*`, toàn bộ **80 cảnh báo IDS Suricata OT** (như `OTSA-SEV-1 attempted-admin`, `OTSA-SEV-4 tcp-connection`) sẽ **bị bỏ sót hoàn toàn**!
> - **Đề xuất xử lý (chọn 1 trong 2 cách khi làm Mục 1.2):**
>   - *Cách 1 (Khuyến nghị ở GĐ1):* Trong file cấu hình của từng index, cho phép `srcIp`/`dstIp` hỗ trợ **tách profile nguồn** hoặc danh sách cặp trường (`["data.srcip", "data.src_ip"]`), backend chạy nhánh phụ cho Suricata rồi gộp ở `transform`.
>   - *Cách 2 (Triệt để ở phía OTSD-Ruleset/Pipeline):* Dùng OpenSearch Ingest Pipeline chuẩn hóa `data.src_ip` → `data.srcip` lúc ghi index (cần phối hợp nhóm hạ tầng).
> - Đồng thời cập nhật bảng thang cảnh báo tường lửa từ `allow`/`deny` sang giá trị thật của `pf`: **`pass`** (`low`) và **`block`** (`medium`, nâng lên `high` ở cấp cạnh khi vượt ngưỡng).

---

### 3.3. Kiểu dữ liệu (`_mapping`) thực tế: Mọi trường IP đều là `keyword` (KHÔNG phải `ip`)

Kết quả kiểm tra trực tiếp `GET /wazuh-alerts-4.x-*/_mapping` và `GET /wazuh-archives-4.x-*/_mapping`:

| Tên trường | Kiểu thực tế trong OpenSearch | Hệ quả kỹ thuật |
| :--- | :--- | :--- |
| `timestamp`, `@timestamp` | `date` | Dùng `timestamp` hoặc `@timestamp` đều ổn định (cả hai đều có mặt trên mọi bản ghi). |
| `data.srcip`, `data.dstip`, `agent.ip` | **`keyword`** | Aggregation `terms` chạy trực tiếp (không cần `.keyword`). **NHƯNG không dùng được truy vấn lọc CIDR gốc của OpenSearch ở GĐ2!** |
| `data.src_ip`, `data.dest_ip` *(Suricata)* | **`keyword`** | Tương tự trên — không lọc CIDR trực tiếp được trên OpenSearch. |
| `data.dstport`, `data.srcport`, `data.protocol`, `data.action` | `keyword` | Aggregation `terms` hoạt động tốt. |
| `rule.level` | `long` | Dùng `range` và `max` aggregation chuẩn xác. |
| `data.flow.pkts_toserver`, `data.flow.bytes_toserver` *(Suricata)* | **`keyword`** *(không phải `long`!)* | **Không chạy `sum` aggregation trực tiếp được** nếu không sửa index template sang `long`. Với log `pf`, không có trường `packets`, chỉ có `data.length` (kiểu chuỗi). |
| `data.alert.severity` *(Suricata)* | `keyword` | Giá trị chuỗi `"1"` đến `"4"` (lưu ý Suricata `severity: 1` là cao nhất, ngược chiều `rule.level`!). |

> [!CAUTION]
> **Cảnh báo cho GĐ2 (Lọc theo CIDR OTSA):** Vì `data.srcip`/`data.dstip` đang là kiểu `keyword`, truy vấn kiểu `{"term": {"data.srcip": "10.0.2.0/24"}}` sẽ **trả về 0 kết quả**. Ở GĐ2, nhóm cần chọn một trong ba hướng:
> 1. Dùng `prefix` query cho các dải mạng chia hết theo octet `/8`, `/16`, `/24` (ví dụ `"10.0.2."`), hoặc
> 2. Lọc bằng `terms` theo danh sách IP đã biết thuộc OTSA đó, hoặc
> 3. Đề xuất bổ sung multi-field kiểu `ip` vào index template của OTSD.

---

### 3.4. Danh sách Agent thực tế, kiểm tra R2 (Log của OTSD) & R7 (NAT)

Kết quả gọi `GET /agents` từ Wazuh Server API (`https://10.30.20.25:55000`):

| Agent ID | Tên Agent | IP (`ip`) | Trạng thái | OS | Phiên bản Wazuh | Nhóm (`group`) | Số log `pf` trong `archives` |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | ---: |
| `000` | `wazuh.manager` | `127.0.0.1` | `active` | Amazon Linux | `v4.14.9` | `null` | 0 |
| `044` | `otsa-sa01` | `10.30.20.35` | `active` | FreeBSD | `v4.14.9` | `default` | **8.997** |
| `025` | `otsa-sa02` | `10.30.20.36` | `active` | BSD | `v4.14.8` | `section-01` | 0 |
| `026` | `otsa-sa03` | `10.30.20.37` | `active` | BSD | `v4.14.8` | `section-01` | 0 |
| `027` | `otsa-sa04` | `10.30.20.38` | `active` | BSD | `v4.14.8` | `section-01` | 0 |
| `010` | `OTSA.internal` | `10.0.2.15` | `disconnected` | BSD | `v4.14.8` | `local-dev` | **13.509** |
| `020` | `otsa-lab56-692449e3` | `10.0.2.15` | `disconnected` | BSD | `v4.14.7` | `default` | 0 |

**Các điểm phát hiện quan trọng về R2, R7 và Agent:**
1. **Về R2 (Log kết nối của OTSD `10.30.20.25`):**
   - Agent `000` (`wazuh.manager`) trong bản ghi log **không có trường `agent.ip`** và **không sinh log kết nối mạng** (392 alert của `000` toàn bộ là `ossec`, `wazuh-monitord`, `df -P`).
   - Tuy nhiên, IP **`10.30.20.25`** **CÓ xuất hiện** trong `wazuh-archives-*` ở chiều **`otsa-sa01 (10.30.20.35) → OTSD (10.30.20.25)`** với **64 bản ghi `pf`** (50 log cổng `1514`, 14 log cổng `1515`) và **11 bản ghi Suricata** (`data.src_ip: "10.30.20.25"`).
   - Các máy `otsa-sa02`, `otsa-sa03`, `otsa-sa04` hiện chỉ gửi telemetry, **chưa gửi `filterlog` (`pf`)** vào `archives` (chỉ có `otsa-sa01` và `OTSA.internal` có `pf`).
2. **Về hiện tượng trùng tên agent / đổi `agent.id` trên máy CI-Live:**
   - Trong lịch sử `wazuh-alerts-*`, riêng `otsa-sa01` xuất hiện dưới nhiều `agent.id` cũ khác nhau (`044`, `040`, `042`, `008`, `030`…) vì máy CI-Live revert snapshot và đăng ký lại.
   - **Khuyến nghị code:** Khi tra cứu **Tab Cảnh báo** trên lịch sử nhiều ngày, lọc theo **`agent.ip`** hoặc **`agent.name`** (thay vì chỉ cứng `agent.id` mới nhất) sẽ không bị mất cảnh báo cũ của máy đó; còn Tab Phần mềm/Lỗ hổng dùng `agent.id` hiện tại từ `/agents`.
3. **Về R7 (NAT) & R17 (IPv6):**
   - **IPv6:** Hiện có **`0` bản ghi IPv6** trong cả `alerts` và `archives`.
   - **NAT:** Trên `.25`, các máy `SA01–SA04` chỉ có 1 card mạng `vmx0` (chưa gắn máy nội bộ phía sau LAN), còn log của `OTSA.internal` (`10.0.2.15`) chủ yếu là lưu lượng lab VirtualBox (`192.168.56.1 ↔ 192.168.56.56`, `30.1.1.x`). Do đó **chưa đủ dữ liệu trên `.25` để khẳng định NAT ở topo mạng OT thật** — cần xác nhận trực tiếp với giảng viên / nhóm OTSA (hoặc kiểm tra trên máy `Dev-IDS` có `Sim-01` đứng sau `PG-OTSA-LAN`).

---

### 3.5. Xác nhận thực tế R5 (`sshd` thiếu `dstip`)

Trên `10.30.20.25`, có đúng **3 bản ghi `sshd`** (`rule.id: 5710`, `level: 5`) chứa `data.srcip: "30.1.1.20"`, `data.dstuser: "vagrant"`, **hoàn toàn thiếu `data.dstip`**, và `agent.ip: "10.30.20.35"` (`otsa-sa01`). Điều này xác nhận 100% thiết kế nhánh `no_dst` + `dstIpFallback = agent.ip` và điều kiện `exists: data.srcip` là chính xác.

---

### 3.6. Xác nhận thực tế cho Tab Lỗ hổng, Tab Phần mềm và Khung chi tiết (MAC)

- **Wazuh API `:55000` (JWT) hoạt động đầy đủ:** Đã test thực tế thành công `/security/user/authenticate`, `/agents`, `/syscollector/010/netiface` (trả về đủ tên card `vtnet0`, MAC `08:00:27:c5:f4:3d`, `rx`/`tx`), `/syscollector/010/netaddr`, và `/syscollector/010/packages`.
- **Index `wazuh-states-inventory-*` có sẵn dữ liệu đồng bộ:** `packages` (1.058 bản ghi), `interfaces` (26), `networks` (10), `ports` (148), `system` (6) — nhóm có thể đọc thẳng từ OpenSearch mà **không nhất thiết phải gọi nhiều request `/syscollector` sang Wazuh API**!
- **Tab Lỗ hổng (`wazuh-states-vulnerabilities-wazuh.manager`):** Index **tồn tại** (đúng chuẩn Wazuh 4.14.9), nhưng hiện tại đang có **`0` bản ghi** vì toàn bộ 6 agent đang kết nối đều là OTSA chạy **FreeBSD/BSD** (chưa có agent Linux/Windows thuộc phạm vi quét CVE mặc định). Cần lưu ý điểm này khi chuẩn bị dữ liệu demo Tab Lỗ hổng với thầy (có thể gắn thêm 1 agent Ubuntu/Windows mẫu vào lab để có dữ liệu CVE thật).

---

## 4. Log JSON mẫu thực tế thu thập từ `10.30.20.25`

### Mẫu 1: Log tường lửa OTSA (`pf` / `filterlog` — `pass`, hướng `otsa-sa01 → OTSD`) trong `wazuh-archives-*`
```json
{
  "timestamp": "2026-11-26T08:58:40.000+0000",
  "agent": { "id": "044", "name": "otsa-sa01", "ip": "10.30.20.35" },
  "decoder": { "name": "pf" },
  "location": "/var/ossec/logs/opnsense_syslog.log",
  "predecoder": { "hostname": "otsa-sa01.internal", "program_name": "filterlog" },
  "data": {
    "action": "pass",
    "protocol": "tcp",
    "srcip": "10.30.20.35",
    "srcport": "25779",
    "dstip": "10.30.20.25",
    "dstport": "1514",
    "length": "0"
  }
}
```

### Mẫu 2: Cảnh báo tường lửa OTSA (`pf` — `block` lặp lại) trong `wazuh-alerts-*`
```json
{
  "agent": { "id": "010", "name": "OTSA.internal", "ip": "10.0.2.15" },
  "decoder": { "name": "pf" },
  "rule": {
    "id": "87702",
    "level": 10,
    "description": "Multiple pfSense firewall blocks events from same source.",
    "groups": ["pfsense", "multiple_blocks"]
  },
  "data": {
    "action": "block",
    "protocol": "tcp",
    "srcip": "192.168.56.1",
    "srcport": "51902",
    "dstip": "192.168.56.56",
    "dstport": "8081",
    "length": "0"
  }
}
```

### Mẫu 3: Cảnh báo IDS Suricata OT trong `wazuh-alerts-*` *(chú ý tên trường `src_ip` / `dest_ip`)*
```json
{
  "agent": { "id": "010", "name": "OTSA.internal", "ip": "10.0.2.15" },
  "decoder": { "name": "json" },
  "location": "/var/log/suricata/eve.json",
  "rule": {
    "id": "86601",
    "level": 3,
    "description": "Suricata: Alert - OTSA-SEV-1 attempted-admin",
    "groups": ["ids", "suricata"]
  },
  "data": {
    "event_type": "alert",
    "in_iface": "vtnet0",
    "proto": "ICMP",
    "src_ip": "10.0.2.15",
    "dest_ip": "198.51.100.131",
    "alert": {
      "action": "allowed",
      "severity": "1",
      "signature_id": "9100001",
      "signature": "OTSA-SEV-1 attempted-admin"
    },
    "flow": {
      "pkts_toserver": "1",
      "bytes_toserver": "98"
    }
  }
}
```

### Mẫu 4: Log SSH thiếu `dstip` trong `wazuh-alerts-*` *(xác nhận cần `dstIpFallback = agent.ip`)*
```json
{
  "agent": { "id": "044", "name": "otsa-sa01", "ip": "10.30.20.35" },
  "decoder": { "name": "sshd" },
  "rule": {
    "id": "5710",
    "level": 5,
    "description": "sshd: Attempt to login using a non-existent user",
    "groups": ["syslog", "sshd", "authentication_failed", "invalid_login"]
  },
  "data": {
    "srcip": "30.1.1.20",
    "srcport": "51074",
    "dstuser": "vagrant"
  }
}
```

### Mẫu 5: Log rác telemetry trong `wazuh-archives-*` *(chiếm 92,5% — phải lọc bỏ)*
```json
{
  "agent": { "id": "025", "name": "otsa-sa02", "ip": "10.30.20.36" },
  "decoder": { "name": "json" },
  "location": "/var/log/otsa/otsd-telemetry.json",
  "data": {
    "otsd": "telemetry",
    "kind": "ifstat",
    "name": "pfsync0",
    "rx_pkts": "0",
    "tx_pkts": "0"
  }
}
```

---

## 5. Đề xuất cập nhật File cấu hình THẬT cho Mục 1.2 (Dựa trên dữ liệu `.25`)

```json
{
  "otsd": {
    "ip": "10.30.20.25",
    "name": "OTSD-Dev-CI-Live"
  },
  "zones": [
    { "cidr": "10.30.20.0/24", "name": "Mạng quản trị Lab OTSD-OTSA" }
  ],
  "otsaNodes": [
    { "ip": "10.30.20.35", "name": "otsa-sa01", "group": "default" },
    { "ip": "10.30.20.36", "name": "otsa-sa02", "group": "section-01" },
    { "ip": "10.30.20.37", "name": "otsa-sa03", "group": "section-01" },
    { "ip": "10.30.20.38", "name": "otsa-sa04", "group": "section-01" }
  ],
  "defaults": {
    "timeRange": "24h",
    "timeZone": "+07:00",
    "topN": 50,
    "groupingThreshold": 25,
    "groupingTopN": 500,
    "queryTimeoutSec": 10
  },
  "edgeSeverityRules": {
    "repeatBlockThreshold": 20,
    "otPorts": [502, 102]
  },
  "indices": {
    "wazuh-alerts-4.x-*": {
      "timestamp": "timestamp",
      "srcIp": "data.srcip",
      "dstIp": "data.dstip",
      "altSrcIp": "data.src_ip",
      "altDstIp": "data.dest_ip",
      "dstIpFallback": "agent.ip",
      "dstPort": "data.dstport",
      "altDstPort": "data.dest_port",
      "username": "data.dstuser",
      "agentName": "agent.name",
      "agentId": "agent.id",
      "severityMode": "numeric_level",
      "levelField": "rule.level",
      "actionField": "data.action",
      "packetsField": null,
      "bytesField": null
    },
    "wazuh-archives-4.x-*": {
      "timestamp": "timestamp",
      "srcIp": "data.srcip",
      "dstIp": "data.dstip",
      "altSrcIp": "data.src_ip",
      "altDstIp": "data.dest_ip",
      "dstIpFallback": "agent.ip",
      "dstPort": "data.dstport",
      "altDstPort": "data.dest_port",
      "username": "data.dstuser",
      "agentName": "agent.name",
      "agentId": "agent.id",
      "severityMode": "pf_action_or_level",
      "levelField": "rule.level",
      "actionField": "data.action",
      "actionValues": { "pass": "low", "block": "medium" },
      "packetsField": null,
      "bytesField": null
    }
  }
}
```

---

## 6. Việc cần xác nhận tiếp với thầy / nhóm sau khảo sát Mục 1.1

1. **Tình trạng máy `10.30.20.26` (`OTSD-Dev-CI`):** Hiện cổng 443 không phản hồi; cần kiểm tra xem nhóm sẽ khảo sát/demo trên `.25` hay `.26`, và liệu `.26` có bật `wazuh-archives-*` giống `.25` không.
2. **Dữ liệu tường lửa cho `sa02–sa04` & kiểm tra NAT thật:** Trên `.25` hiện chỉ có `otsa-sa01` gửi `pf` (`filterlog`), còn `sa02–sa04` chưa gửi; đồng thời các máy SA chưa có máy khách đứng sau LAN nên cần xác nhận với thầy/nhóm OTSA về **cấu hình NAT** và **dải CIDR phía sau từng OTSA** khi demo.
3. **Chốt hướng xử lý 2 bộ tên trường (`data.srcip` của `pf`/`sshd` vs `data.src_ip` của Suricata):** Nhóm có gom cả Suricata vào đồ thị GĐ1 (query thêm nhánh `altSrcIp`/`altDstIp`) hay chỉ vẽ `pf` + `sshd` trước?
4. **Dữ liệu test cho Tab Lỗ hổng (`CVE`):** Do `wazuh-states-vulnerabilities-wazuh.manager` đang có `0` bản ghi trên các agent FreeBSD, cần thống nhất với thầy xem có gắn thêm 1 máy agent Linux/Windows (ví dụ máy `Sim-01` hoặc 1 VM thử nghiệm) để demo Tab Lỗ hổng hay không.
5. **Chốt giải pháp lọc CIDR cho GĐ2 khi trường IP là `keyword`:** Dùng `prefix` query (cho `/16`, `/24`), lọc `terms` theo danh sách IP, hay sửa index template bổ sung kiểu `ip`.
