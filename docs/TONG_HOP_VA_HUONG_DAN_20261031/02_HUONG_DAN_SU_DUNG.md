# Hướng dẫn sử dụng hệ thống giám sát và học luật

Áp dụng cho lab MON01 SRV01 CLI01 và bản ML chốt ngày 31 tháng 10 năm 2026

## 1 Chọn đúng tác vụ

Tài liệu này giúp mở kết quả đã chốt, chạy lại demo có kiểm soát, dùng engine baseline, xem luật SQLite và chuẩn bị một đợt nghiên cứu mới. Đọc báo cáo hoặc suy luận từ observation đã lưu không cần bật VM. Chỉ bật VM khi cần xem Zabbix hiện tại, thu probe live hoặc chạy demo gây lỗi.

| Nhu cầu | Công cụ | Có tạo lỗi không |
|---|---|---|
| Đọc kết quả chốt | Báo cáo, CSV, JSON và ảnh trong evaluation | Không |
| Xem gợi ý trên evidence cũ | demo_v2.py | Không, suy luận offline |
| Demo healthy và dừng Nginx | Run-ML-Demo.ps1 | Có, trên SRV01 và có rollback |
| Chẩn đoán một problem hiện tại | app.py trên MON01 | Không tự gây lỗi hoặc tự sửa |
| Ghi incident và recovery | app.py --save và recovery.py | Ghi database baseline khi được gọi |
| Thu một observation mới | python -m mlv2 collect | Không tự gây lỗi |
| Train thử bộ nghiên cứu mới | train_v2.py với output mới | Không gọi API hoặc tạo fault |

Ba VM đã được tắt theo yêu cầu sau nghiệm thu và backup lạnh. Hướng dẫn dưới đây là thao tác khi cần sử dụng lại; không có lệnh nào trong tài liệu được coi là đã chạy chỉ vì được viết ở đây.

## 2 Vị trí làm việc và điều kiện chuẩn bị

### 2.1 Các đường dẫn chính

| Tên dùng trong hướng dẫn | Đường dẫn |
|---|---|
| Project chuẩn | C:\Users\Darrys\do-an |
| Mô đun ML | C:\Users\Darrys\do-an\ml-research |
| Evidence ML | C:\Users\Darrys\do-an\evidence\ml-v2 |
| Workspace điều phối | C:\Users\Darrys\Documents\ChatGPT\Đồ án network |
| Engine trên MON01 | /home/phat/do-an/diagnosis-engine |
| File release ML | C:\Users\Darrys\do-an\evidence\ml-v2\ML_RELEASE.json |
| Receipt backup source | ml-final-checkpoint-latest.json trong workspace |
| Receipt backup VM | cold-vm-backup-latest.json trong workspace |

Workspace có một thư mục stage `ml-v2` cũ; không chép đè nó lên source chuẩn. Source đã nghiệm thu ở project `do-an`. Các helper Windows nằm ngoài repo được bảo toàn trong backup workspace; khi chuyển máy cần đọc cả manifest và RESTORE.

### 2.2 Điều kiện chạy live

Máy Windows cần cắm sạc, màn hình được đánh thức và đủ thời gian hoàn tất can thiệp cùng khôi phục. Ba VM cần chạy, đúng IP Host only và không có một coordinator thu lỗi khác đang chiếm lab. Không chạy hai demo song song.

Tài khoản SSH lab là `phat`. Mật khẩu được nhập ẩn khi công cụ yêu cầu; không đưa vào command line, tài liệu hoặc file config. Host key phải được xác minh và lưu trong `C:\Users\Darrys\.ssh\known_hosts`; lỗi host key cần kiểm tra fingerprint từ VM hoặc kênh tin cậy, không tắt RejectPolicy để bỏ qua.

Các fault hiện tại chỉ hỗ trợ SRV01 với địa chỉ 192.168.56.20 và enp0s8. Không sửa IP trong profile rồi dùng nguyên script fault trên một máy khác. Source freeze và scope gate nhằm ngăn việc vô tình áp dụng dữ liệu hay can thiệp sai lab.

### 2.3 Khởi động ba VM khi thật sự cần

Trên PowerShell của Windows:

```powershell
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
& $vbox startvm MON01 --type headless
& $vbox startvm SRV01 --type headless
& $vbox startvm CLI01 --type headless
& $vbox list runningvms
```

Chỉ chạy startvm cho VM đang tắt. Có thể mở VirtualBox Manager để kiểm tra trạng thái thay vì lặp lệnh khi máy đã chạy. Chờ guest khởi động, dịch vụ và đồng hồ ổn định; lỗi ping ngay sau boot chưa đủ kết luận dịch vụ hỏng.

Kiểm tra kết nối từ Windows:

```powershell
Test-NetConnection 192.168.56.10 -Port 22
Test-NetConnection 192.168.56.20 -Port 22
Test-NetConnection 192.168.56.30 -Port 22
```

Mở trình duyệt tới `http://192.168.56.10:8080/`. Đăng nhập bằng tài khoản Zabbix đã được cấu hình riêng; báo cáo không lưu thông tin đăng nhập.

## 3 Đọc bộ kết quả đã chốt

### 3.1 Mở đúng evaluation

Trong PowerShell, khai báo hai đường dẫn cho phiên làm việc:

```powershell
$project = 'C:\Users\Darrys\do-an'
$work = 'C:\Users\Darrys\Documents\ChatGPT\Đồ án network'
$release = Get-Content -LiteralPath "$project\evidence\ml-v2\ML_RELEASE.json" -Raw | `
    ConvertFrom-Json
$evaluation = $release.evaluation
$presentation = $release.presentation
$release.status
Get-Content -LiteralPath "$presentation\BAO_CAO_NGHIEM_THU.md"
```

Trạng thái release hiện tại là INITIAL_VM_ML_RELEASE_VERIFIED. Nó xác nhận tính nhất quán bằng chứng trong phạm vi nghiên cứu, không có nghĩa production đã được phê duyệt. `release.presentation` trỏ tới bộ hình cuối đã được xem lại, nên dùng nó thay vì chọn thư mục presentation cũ theo mắt.

### 3.2 Tệp nên xem theo thứ tự

| Tệp | Dùng để trả lời |
|---|---|
| BAO_CAO_NGHIEM_THU.md | Kết quả chính, giới hạn và cách bảo vệ |
| LUAT_HOC_DUOC.md | Điều kiện và thống kê train của 7 lá CART và 19 luật FP |
| metrics.json | Accuracy, macro F1, coverage và confusion matrix của bảy đối chứng |
| locked_test_predictions.csv | Nhãn can thiệp và dự đoán từng run |
| locked_test_used.csv | Feature thực tế của cửa sổ cuối từng run |
| family_comparison.csv | TP, FP, FN, coverage và healthy false alarms theo câu hỏi |
| same_input_latency.json | Median và P95 warm offline |
| detection-audit\DETECTION.md | Zabbix có event liên quan trong cửa sổ can thiệp hay chưa |
| manifest.json | Nguồn dữ liệu, split, cấu hình và hash |

Lệnh xem các lần từ chối mà không sửa dataset:

```powershell
Import-Csv -LiteralPath "$evaluation\locked_test_predictions.csv" |
    Where-Object { $_.cart_discrete -eq 'ABSTAIN' } |
    Select-Object session_id,run_id,label,cart_discrete,fp_classifier
```

Kết quả đã chốt có sáu hàng interface_down. Chúng nằm trong mẫu số accuracy, không bị xóa khỏi tập test. Một run có hai cửa sổ raw nhưng bảng điểm chỉ dùng cửa sổ cuối, nên không cộng số file JSON thành số mẫu test.

## 4 Chạy demo ML đã được nghiệm thu

### 4.1 Demo Nginx mặc định

Chuẩn bị ba VM và kết nối SSH như phần 2. Từ PowerShell chạy:

```powershell
pwsh -NoProfile -File "C:\Users\Darrys\Documents\ChatGPT\Đồ án network\Run-ML-Demo.ps1"
```

Nhập mật khẩu SSH khi được hỏi; ký tự không hiện là hành vi bình thường. Wrapper kiểm tra release, giữ khóa lab, đặt yêu cầu display và system thức tạm thời, rồi gọi chương trình demo. Không cần người dùng tự dừng Nginx bằng tay khi đang dùng wrapper này.

Demo lấy observation healthy trước, tạo fault Nginx, lấy hai observation lúc fault, rollback, đợi nền ổn định và lấy observation sau. Output cho mỗi observation có sáu nhận định expert cùng gợi ý CART và FP. Kết thúc hợp lệ có dòng DEMO_VERIFIED và exit code 0.

Không lấy thời gian giữ 40 giây làm thời gian toàn demo. Quá trình đợi item, trigger recovery hoặc mẫu CPU sạch có thể kéo dài thêm. Nếu chưa có DEMO_VERIFIED, không tự coi lượt đó thành công chỉ vì đã thấy nhãn nginx_stopped trên màn hình.

### 4.2 Chọn fault khác

```powershell
pwsh -NoProfile -File "C:\Users\Darrys\Documents\ChatGPT\Đồ án network\Run-ML-Demo.ps1" -Fault `
    agent_stopped
```

Các giá trị được wrapper chấp nhận là nginx_stopped, agent_stopped, interface_down, remote_http_filtered, dns_egress_blocked và cpu_stress. Agent và CPU cần thời gian dài hơn. Interface làm gián đoạn SSH; gate có thể từ chối khi core probe unknown, đúng với kết quả đã chốt. Một fault khác chưa chạy demo trong phiên hiện tại không được gọi là demo mới đã kiểm chứng chỉ vì wrapper hỗ trợ tên đó.

### 4.3 Cách đọc một đề xuất

`label` là nhãn kịch bản lab. `matched_rule` chỉ ra điều kiện khớp và số run train hỗ trợ. FP hiển thị support, confidence và lift; CART hiển thị phân bố lớp tại lá. `confidence_kind` nhắc rõ đây là thống kê train, chưa hiệu chỉnh xác suất. ABSTAIN nghĩa hệ thống từ chối kết luận theo policy hoặc luật, không có nghĩa healthy.

Nếu expert có một matched và ML có một nhãn khác, giữ nguyên cả hai output và observation để xem xét. Không đổi nhãn can thiệp theo model hay chạy lại tới khi có kết quả mong muốn.

### 4.4 Tìm log của lượt demo

```powershell
$demoRoot = "$project\evidence\ml-v2\demos"
$latestDemo = Get-ChildItem -LiteralPath "$demoRoot\checks" -Directory |
    Sort-Object Name | Select-Object -Last 1
Get-Content -LiteralPath (Join-Path $latestDemo.FullName 'result.json')
Get-ChildItem -LiteralPath "$demoRoot\comparisons\$($latestDemo.Name)" -Recurse -File
```

`checks` chứa preflight và result; `trial-logs` chứa script, log can thiệp, rollback và timeline; `observations` là raw evidence; `comparisons` là expert và ML. Demo đã được chứng minh trong bản chốt có ID demo-20261031T141114556079Z. Các file mới của một lần chạy lỗi phải được giữ lại, không ghi đè lên ID cũ.

## 5 Suy luận offline không cần VM

Suy luận từ observation đã lưu không gây fault, không gọi Zabbix để thu mới và không tự lưu incident. Nó phù hợp để giải thích luật trước hội đồng khi không cần trình diễn live.

```powershell
Set-Location -LiteralPath "$project\ml-research"
$obsRoot = "$project\evidence\ml-v2\demos\observations\demo-20261031T141114556079Z\fault"
$observation = Get-ChildItem -LiteralPath $obsRoot -Filter '*.json' |
    Sort-Object Name | Select-Object -Last 1
python .\demo_v2.py --observation $observation.FullName --candidate-db $release.candidate_db `
    --engine-source "$project\diagnosis-engine"
```

Đây là phép replay trên bằng chứng lịch sử, không chứng minh trạng thái host hiện tại. `demo_v2.py` là công cụ so sánh trực tiếp; `Run-ML-Demo.ps1` mới là wrapper có kiểm tra release, khóa lab và điều phối fault live. Không dùng một ảnh replay để trình bày như một lỗi đang xảy ra.

## 6 Dùng diagnosis engine baseline trên MON01

### 6.1 Liệt kê problem đang mở

Từ Windows đăng nhập MON01 rồi dùng môi trường đã có:

```powershell
ssh phat@192.168.56.10
```

Các lệnh tiếp theo chạy trong shell Ubuntu của MON01:

```bash
cd /home/phat/do-an/diagnosis-engine
.venv/bin/python app.py --host-id 10683
```

Không truyền event ID thì app liệt kê problem đang mở của host. Nếu không có problem, đó không phải lỗi chương trình và không cần tạo event giả. Chọn event thật còn mở, đúng host. Các ví dụ phía dưới dùng EVENT_ID_HIEN_TAI và INCIDENT_ID; thay bằng giá trị từ lần chạy thật, không dùng ID lịch sử đã đóng.

### 6.2 Thu local HTTP đúng observer

Nếu cần giải thích R2 hoặc R5, tạo file HTTP mới ngay trên SRV01. Có thể chuyển probe độc lập từ Windows nếu chưa có bản ở thư mục người dùng:

```powershell
scp "C:\Users\Darrys\do-an\diagnosis-engine\http_probe.py" `
    phat@192.168.56.20:/home/phat/http_probe.py
ssh phat@192.168.56.20
```

Trên SRV01:

```bash
python3 /home/phat/http_probe.py --target-ip 192.168.56.20 --observer srv01 --output \
    /home/phat/http-demo-moi.json
```

Tên output phải chưa tồn tại. Trở lại PowerShell Windows, chuyển file qua máy điều phối rồi tới MON01:

```powershell
scp phat@192.168.56.20:/home/phat/http-demo-moi.json "$work\http-demo-moi.json"
scp "$work\http-demo-moi.json" phat@192.168.56.10:/home/phat/http-demo-moi.json
```

Probe cần được chuyển và sử dụng kịp thời. Nếu đã cũ hoặc lỗi đã phục hồi, tạo probe mới và chọn đúng event, không sửa timestamp JSON để vượt freshness gate. Các lệnh minh họa cần filename mới cho từng lượt; không dùng đi dùng lại một file cũ.

### 6.3 Chẩn đoán và lưu incident

Trên MON01, xem kết quả trước khi thêm `--save`:

```bash
.venv/bin/python app.py --event-id EVENT_ID_HIEN_TAI --host-id 10683 --target-ip 192.168.56.20 \
    --ruleset roadmap --control-ip 192.168.56.30 --http-service expected --http-observer srv01 \
    --http-evidence /home/phat/http-demo-moi.json
```

Muốn lưu incident, gọi cùng tập tham số với `--save` khi event vẫn còn mở. Lệnh lưu sẽ thu và kiểm tra lại bằng chứng theo chương trình; không mặc định hai lần gọi là một snapshot giống hệt. Event đã có bundle không được ghi ghép bằng chứng khác tùy ý. `--save` yêu cầu event ID; không có cờ này thì việc in assessment không ghi diagnosis.db.

### 6.4 DNS observer của baseline

Baseline thường dùng CLI01 làm observer DNS, khác profile ML dùng SRV01 cho mọi nhãn. Nếu chạy dns_probe.py trên CLI01, cần cả evidence.py và models.py cùng thư mục, có ping và dig. Chuyển source chuẩn từ Windows vào một thư mục người dùng riêng rồi chạy tại đó.

```powershell
ssh phat@192.168.56.30 'mkdir -p /home/phat/demo-dns'
scp "$project\diagnosis-engine\dns_probe.py" "$project\diagnosis-engine\evidence.py" `
    "$project\diagnosis-engine\models.py" phat@192.168.56.30:/home/phat/demo-dns/
ssh phat@192.168.56.30
```

Trên CLI01:

```bash
cd /home/phat/demo-dns
python3 dns_probe.py --name example.com --control-ip 1.1.1.1 --output dns-demo-moi.json
```

Sau khi chuyển JSON mới về MON01, bổ sung vào lệnh app các tham số `--dns-name example.com --dns-control-ip 1.1.1.1 --dns-observer cli01 --dns-evidence /duong/dan/dns-demo-moi.json`. Chỉ rõ observer thực tế; không gán observer khác để làm file hợp lệ. Không có DNS evidence thì R4 có thể giữ insufficient_evidence, thay vì tự coi DNS khỏe.

### 6.5 Ghi recovery và xuất report

Sau khi dịch vụ đã phục hồi và Zabbix có recovery thật, trên MON01:

```bash
.venv/bin/python recovery.py --event-id EVENT_ID_HIEN_TAI
.venv/bin/python report.py --incident-id INCIDENT_ID --format md --output \
    /home/phat/incident-demo.md
```

Có thể chọn format json hoặc csv. Incident ID được lấy từ output lưu bundle hoặc database, không phải event ID. Có thể đọc database bằng SQLite CLI ở chế độ chỉ đọc:

```bash
sqlite3 -readonly diagnosis.db '.schema incidents'
sqlite3 -readonly diagnosis.db 'SELECT * FROM incidents ORDER BY id DESC LIMIT 5;'
```

Report CSV là một dòng mỗi diagnosis; dataset ML là một dòng mỗi run. Không trộn hai loại CSV để tính số thí nghiệm. Dùng `--db` khi làm với bản sao database; không chỉnh dữ liệu gốc để hợp thức hóa một report.

## 7 Xem luật SQLite và chứng minh provenance

Candidate hiện tại có 7 lá CART và 19 luật FP. Có thể xem bằng SQLite CLI nếu đã cài hoặc công cụ SQLite mở file ở chế độ chỉ đọc. Ví dụ trên môi trường có sqlite3:

```sql
SELECT algorithm, COUNT(*) AS rule_count
FROM candidates GROUP BY algorithm;

SELECT rule_id, algorithm, label, conditions_json,
       training_runs, statistics_json, status
FROM candidates ORDER BY algorithm, rule_id;

PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

Các câu SELECT trên chạy với candidate_rules.sqlite. Với research_registry.sqlite, dùng schema và các truy vấn riêng:

```sql
SELECT name FROM sqlite_master WHERE type='table';
SELECT model_id, state, at FROM rule_lifecycle ORDER BY sequence;
SELECT COUNT(*) FROM rule_lifecycle WHERE state='active';
```

Số record active đã nghiệm thu là 0. Không chạy UPDATE để đổi validated thành active như một thao tác bật tính năng: engine chưa có quy trình production integration được nghiệm thu. Mỗi artifact và registry là phiên bản nghiên cứu cần giữ bất biến.

Đối chiếu checksum một file trên Windows bằng Get-FileHash. Ví dụ:

```powershell
(Get-FileHash -LiteralPath $release.candidate_db -Algorithm SHA256).Hash.ToLower()
$release.candidate_sha256
```

Hai dòng phải khớp. SHA không xác nhận nhãn đúng về mặt mạng; nó xác nhận file đang xem là đúng artifact đã ghi nhận. Manifest và QA receipt giúp truy từ chỉ số đến raw observation, review và log can thiệp.

## 8 Thu dữ liệu hoặc train một phiên mới

### 8.1 Chuẩn bị môi trường nghiên cứu

Môi trường ML chốt được kiểm chứng trên Python 3.14. Dependency thu live nằm trong requirements.txt, dependency nghiên cứu offline trong requirements-ml.txt. Nếu cần dựng môi trường riêng trên máy khác, có thể tạo venv mới:

```powershell
Set-Location -LiteralPath "$project\ml-research"
py -3.14 -m venv .venv-ml
& .\.venv-ml\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ml.txt
```

Trong phiên PowerShell hiện tại, kích hoạt bằng `& .\.venv-ml\Scripts\Activate.ps1` trước khi dùng các lệnh `python` phía dưới. Nếu không chạy script kích hoạt, thay `python` bằng `& .\.venv-ml\Scripts\python.exe` để gọi đúng môi trường; không cần đổi ExecutionPolicy để dùng cách gọi trực tiếp.

Lệnh cài đặt này là quy trình dựng môi trường, không phải bằng chứng đã test trên mọi máy Windows. Requirements hiện khóa NumPy, pandas, scikit learn và mlxtend theo bản chốt. Không dùng pip upgrade trong môi trường đang chạy bộ test đã khóa. VM engine dùng venv riêng trên MON01, không thay bằng venv ML Windows.

### 8.2 Thu một observation không tạo fault

Chọn một data root mới ngoài evidence đã nghiệm thu. Đăng ký nhãn dự kiến trước; nhãn đó không tự trở thành ground truth hợp lệ:

```powershell
$data = Join-Path $work 'research-new-session'
python -m mlv2 --data-root $data register --session new-session-01 --run run-001 --labels `
    healthy
python -m mlv2 --data-root $data collect --session new-session-01 --run run-001 --profile `
    config/srv01.json --engine-source "$project\diagnosis-engine"
```

Các lệnh trên chạy từ thư mục ml-research bằng Python đã có dependencies phù hợp. Collector gọi cùng probes, lưu observation ngay cả khi có source error; exit 2 nghĩa cần xem lỗi nguồn, không tự đổi thành nhãn fault.

Review chỉ được đánh valid sau khi xem bằng chứng độc lập. Tham số `--evidence` phải trỏ tới log preflight, can thiệp và khôi phục phù hợp với lượt thật, không phải một file rỗng cho đủ cú pháp:

```powershell
python -m mlv2 --data-root $data review --session new-session-01 --run run-001 --validity valid `
    --labels healthy --evidence DUONG_DAN_LOG_DA_KIEM_TRA
```

Một observation mới không đủ điều kiện cho benchmark 42 run. Không truyền data root mới chỉ có một hàng vào trainer rồi gọi kết quả là nghiên cứu đã nghiệm thu.

### 8.3 Ranh giới của công cụ điều phối

Có thể train và validation lại trên pilot đã có, ghi vào output mới, không cần bật VM:

```powershell
Set-Location -LiteralPath "$project\ml-research"
python .\train_v2.py --project-root $project --data-root "$project\evidence\ml-v2" --output-root `
    "$work\benchmark-offline-moi"
```

Trainer này yêu cầu đầy đủ lịch pilot v2, review và source hợp lệ; không phải công cụ nhận một CSV tùy ý. Kết quả lệnh trên vẫn là validation lại dữ liệu phát triển đã biết, không phải bộ test độc lập mới. Không ghi đè output đã nghiệm thu, không thay $release.candidate_db bằng artifact mới chỉ vì train chạy xong. Các metadata thời gian và raw manifest mới là căn cứ về phiên dữ liệu, không suy từ một dòng prose tóm tắt.

run_pilot.py và các helper full_ml_session.py, ml_supervisor.py, ml_acceptance.py có thể tự tạo nhiều fault và chờ khôi phục trong thời gian dài. Chúng là công cụ của protocol, không phải nút mở báo cáo. Không chạy lại full_ml_session.py trên bộ đã hoàn tất chỉ để xem kết quả; một số bước hậu xử lý tạo file bất biến và không được thiết kế để ghi đè tùy ý.

Muốn thay feature, ngưỡng hoặc serving gate sau khi đã xem điểm, cần phiên bản nghiên cứu mới, output và manifest mới, cùng bộ test mới. Không sửa development-freeze.json hoặc xóa các ca ABSTAIN để làm bản cũ đạt 100 phần trăm.

### 8.4 Kiểm tra code khi có thay đổi thật

```powershell
Set-Location -LiteralPath "$project\ml-research"
python -m unittest discover -s tests -v
```

Kết quả chốt đã có 57 tests đạt. Sau khi sửa code hoặc chuyển môi trường, phải đọc kết quả thực tế; con số trong tài liệu không bảo đảm lần chạy mới đạt. Không cần chạy lại cả chiến dịch fault để chỉ đọc report hoặc xem luật.

## 9 Xử lý lỗi thường gặp

### 9.1 Baseline not restored

Không hạ gate để chạy tiếp. Kiểm tra Nginx, Agent, HTTP local, DNS, IP control, NTPSynchronized, CPU history và problem còn mở. Trong VM có thể dùng các lệnh chỉ đọc sau:

```bash
systemctl is-active nginx zabbix-agent2
timedatectl show -p NTPSynchronized --value
uptime
pgrep -a stress-ng
systemctl list-timers 'mlv2-*' --no-legend --no-pager
```

Không ép đóng problem Zabbix chỉ để có nền sạch. CPU cần chờ dữ liệu cũ hết cửa sổ; Agent cần chờ availability và sample cập nhật. Nếu có lỗi hạ tầng ngoài can thiệp, giữ run uncertain và xem log trước khi retry ID mới.

### 9.2 SSH timeout hoặc host key khác

Kiểm tra VM đang chạy, IP Host only, cổng 22 và trạng thái ngủ của Windows. Với interface_down, SSH bị ngắt có thể là tác động đã dự kiến; chờ timer rollback độc lập và xem log. Không tạo thêm một fault trong khi chưa xác nhận lần trước đã rollback.

Host key khác với known_hosts là một vấn đề danh tính máy, không giải quyết bằng cách bật AutoAddPolicy hoặc tắt kiểm tra fingerprint. Sai tài khoản hoặc mật khẩu cũng không được che thành lỗi đo mạng.

### 9.3 Windows vào Modern Standby

Đánh thức máy bằng thao tác thực tế, cắm sạc, giữ máy mở trong phiên. Các wrapper có yêu cầu giữ thức tạm thời nhưng không mở khóa Windows hoặc thay mọi chính sách ngủ của thiết bị. Log đã ghi một số lần hệ thống ngủ khi màn hình tắt; không kết luận mọi RCU stall đều do cùng nguyên nhân.

Khi quay lại sau thời gian ngủ, chờ đồng hồ và tải nền ổn định rồi mới thử lại. Tài liệu này không yêu cầu đổi power plan, affinity hoặc cấu hình CPU và RAM để làm đẹp điểm số.

### 9.4 JSON RPC lỗi nội bộ hoặc package đang cập nhật

Một lỗi API nội bộ không tự chứng minh token sai. Kiểm tra tình trạng MySQL, Zabbix và job package qua kênh quản trị thích hợp; không đổi token hoặc giết apt theo suy đoán. Episode đã ghi nhận của lab có backup database trước phục hồi và log thứ tự service riêng.

Nếu fingerprint package không khớp bản trước test, dừng bộ giữ riêng và xem lại protocol. Không sửa file freeze để hợp thức hóa môi trường mới. Việc phục hồi hạ tầng là thao tác quản trị riêng, không phải huấn luyện lại model.

### 9.5 ML trả ABSTAIN hoặc báo scope khác

Kiểm tra profile có đúng SRV01 và 12 feature contract, core probe nào unknown, dữ liệu có cũ hay sai observer không. Với bản chốt, sáu ca interface_down đều bị gate từ chối vì TCP80 unknown. Đó là kết quả thực nghiệm cần báo, không phải mặc định lỗi cài đặt.

Ngoài scope hoặc khi nghi nhiều lỗi đồng thời, giữ kết quả từ chối và điều tra thêm. Không chọn model khác chỉ vì nó đưa ra nhãn mong muốn trên một ca lẻ sau khi xem điểm test.

### 9.6 Database locked hoặc file output đã tồn tại

Đóng công cụ SQLite đang giữ transaction ghi và dùng bản read only để xem. Không xóa journal hoặc sửa DB vận hành đang mở. Các artifact nghiên cứu từ chối ghi đè là thiết kế bảo toàn provenance; tạo output hoặc run ID mới sau khi hiểu nguyên nhân.

## 10 Dừng phiên và backup

### 10.1 Kết thúc demo đúng cách

Chờ DEMO_VERIFIED và kiểm tra result valid. Xác nhận dịch vụ đã phục hồi, không còn stress, timer hoặc table mang token của lượt. Nếu buộc phải ngắt coordinator, giữ nguyên file đang dở và xem control.json để phục hồi đúng tài nguyên sở hữu; không gọi lượt đó thành valid chỉ từ một screenshot.

Không có một lệnh cleanup chung xóa mọi table nft hoặc giết mọi stress process được khuyến nghị ở đây. Khi chưa rõ token và trạng thái, đọc log trước để tránh tác động nhầm công việc khác.

### 10.2 Tắt ba VM

Sau khi không còn thí nghiệm đang chạy, có thể gửi ACPI shutdown từ Windows:

```powershell
& $vbox controlvm CLI01 acpipowerbutton
& $vbox controlvm SRV01 acpipowerbutton
& $vbox controlvm MON01 acpipowerbutton
& $vbox list runningvms
```

ACPI là yêu cầu guest shutdown; lệnh gửi thành công chưa có nghĩa guest đã tắt xong. Kiểm tra từng trạng thái tới poweroff trước khi copy đĩa. Không dùng controlvm poweroff để thay thế mặc định cho shutdown sạch.

```powershell
& $vbox showvminfo MON01 --machinereadable | Select-String '^VMState='
& $vbox showvminfo SRV01 --machinereadable | Select-String '^VMState='
& $vbox showvminfo CLI01 --machinereadable | Select-String '^VMState='
```

### 10.3 Backup source và VM khác nhau thế nào

Bản source và evidence chốt ML có Git bundle, raw working bytes, dataset, luật, báo cáo và helper. Đã thử clone bundle, fsck và đối chiếu HEAD; đã kiểm tra CRC cùng SHA. Nó không chứa đầy đủ đĩa của ba VM.

Backup lạnh VM được tạo sau khi cả ba đã poweroff, copy toàn bộ thư mục mỗi VM gồm base disk, tất cả snapshot disk, cấu hình và saved state của snapshot. Không chỉ chép file snapshot mới nhất. Các disk có quan hệ cha con; mất parent disk có thể làm mất khả năng mở cả chuỗi.

Backup lạnh được tạo sau khi cả ba VM đã poweroff, hoàn tất lúc 2026-10-31T21:33:45.685316+07:00. Có 56 tệp, 28 hard disk trong chuỗi cấu hình, tổng 45,704,094,798 byte, xấp xỉ 45.70 GB. Mọi file nguồn và bản sao có SHA256 khớp, source giữ nguyên trong lúc copy; chưa boot thử từ bản phục hồi.

Đường dẫn backup lạnh là `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261031T142959433223Z`. Các tệp VERIFICATION.json, FILES_SHA256.json, DISK_CHAINS.json và RESTORE.md ghi trạng thái, hash và cách phục hồi. Receipt tra cứu ở `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\cold-vm-backup-latest.json`. Cả MON01, SRV01 và CLI01 được giữ tắt sau thao tác.

### 10.4 Khôi phục khi cần

Đối với source, đọc RESTORE trong backup và giải nén vào thư mục riêng. Git bundle giữ lịch sử, còn tracked-project-raw.zip giữ byte thực dùng cho manifest. Các đường dẫn tuyệt đối trong freeze không tự thích ứng khi đổi thư mục; không tuyên bố replay byte identical sau khi tự sửa đường dẫn.

Đối với VM, giữ toàn bộ cây thư mục và kiểm tra FILES_SHA256.json. Nên diễn tập ở máy hoặc registry VirtualBox tách biệt. Backup giữ UUID gốc; không đăng ký đồng thời bản gốc và bản sao cùng UUID trong một registry. Kiểm tra tên adapter Host only và tham chiếu ISO ngoài thư mục trước khi boot. Không chép đè VM đang chạy hoặc khởi động cả hai bản có cùng IP trong mạng lab.

Bản lạnh đã đối chiếu byte nhưng chưa được boot như một bản phục hồi độc lập. Hai phân vùng C và D của cùng laptop không bảo vệ khỏi mất máy; khi cần dự phòng thiết bị phải có thêm bản sao trên phương tiện khác, do người dùng lựa chọn.

## 11 Trình tự demo gợi ý khi bảo vệ

Đầu tiên mở bảng kiến trúc và nêu ba vai trò Zabbix, expert và ML. Tiếp theo cho xem 42 pilot, 42 test giữ riêng, bảy trạng thái và manifest. Trình bày bảng điểm với sáu lần từ chối còn trong mẫu số và giải thích gate.

Sau đó chạy demo Nginx bằng wrapper, chỉ ra local HTTP, TCP80, kết quả expert và điều kiện hai luật ML đã khớp. Chờ phần healthy sau phục hồi và mở result valid. Nếu không chạy live, nói rõ đang replay evidence lịch sử.

Cuối cùng mở audit detection để trình bày giới hạn Agent, CPU và DNS; cho xem candidate có 26 luật, registry không có active và backup receipt. Không đổi bảng điểm hoặc tự kích hoạt luật ngay trong buổi trình bày.

## 12 Mốc kết quả và tài liệu liên quan

- Bản chốt code dùng thực nghiệm: `8ba97a7bab5debb24f6eeb852fd59f49c66462d7`.

- Evaluation chốt: `C:\Users\Darrys\do-an\evidence\ml-v2\locked-test-v1\evaluation\20261031T140643065544Z`.

- Report và bộ luật hiện hành: `C:\Users\Darrys\do-an\evidence\ml-v2\locked-test-v1\evaluation\20261031T140643065544Z\presentation-20261031T141036524152Z`.

- Source và evidence backup chính: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\deliverables\initial-vm-ml-complete-20261031T141344679255Z`.

- Source và evidence backup thứ hai: `D:\Study\network-monitoring-project\backups\initial-vm-ml-complete-20261031T141344679255Z`.

- Backup lạnh VM: `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261031T142959433223Z`.

- Đọc báo cáo tổng hợp kèm theo để hiểu phương pháp, đối chứng, kết quả và ranh giới kết luận.

Lệnh trong tài liệu đã được đối chiếu với tham số CLI của source chốt. Các lệnh tạo môi trường, thu mới hoặc khôi phục trên máy khác là hướng dẫn sử dụng, chưa phải một phiên thực nghiệm mới. Kết quả nghiệm thu đã chạy được phân biệt bằng report, result, QA và receipt có đường dẫn cụ thể.
