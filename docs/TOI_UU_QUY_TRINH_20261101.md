# Tối ưu quy trình và code — 01/11/2026

Đợt này tối ưu phần so sánh expert/ML và thao tác vận hành. Kết quả học máy ngày 31/10 được giữ nguyên; đây không phải đợt train hoặc thu fault mới. Bản Word/Markdown tổng hợp ngày 31/10 vẫn là tài liệu nghiệm thu lịch sử; tài liệu này bổ sung quy trình mới.

## 1. Thay đổi và nguyên nhân

| Trước | Sau | Tệp |
|---|---|---|
| Mỗi observation mở lại SQLite, parse lại toàn bộ candidate và chèn đường dẫn engine vào sys.path | Nạp một snapshot candidate đã kiểm SHA256 cho cả phiên; vẫn tính features, expert và ML lại với từng observation | `ml-research/shadow_runtime.py` |
| Import theo tên có thể dùng nhầm module engine đã nạp từ nơi khác | Kiểm tra nguồn của models/policy/roadmap_rules trước khi dùng và khôi phục sys.path sau import | Cùng runtime |
| Wrapper demo gọi hàm so sánh nạp lại DB mỗi lần | DemoPilot dùng cùng CandidateRuntime cho các snapshot trước/trong/sau fault; vẫn lưu hash observation | `ml-research/run_demo_v2.py` |
| Xem trạng thái, kiểm tra checksum, replay và demo dùng các đường gọi khác nhau | Một CLI với bốn lệnh status/verify/replay/demo; đường dẫn project suy từ vị trí script, không phụ thuộc thư mục đang đứng | `tools/lab.py` |
| Nguy cơ tạo demo song song hoặc nhả khóa khi tiến trình con chưa dọn xong | Dùng đúng hai byte lock của coordinator hiện có; giữ khóa qua Ctrl+C tới khi child kết thúc; wake request tạm thời được dọn trong finally | `tools/lab_session.py` |

Runtime chỉ cache dữ liệu model, không cache observation hoặc kết luận chẩn đoán. Trả bản sao của luật đã khớp để bên gọi không sửa được cache qua kết quả. Candidate được kiểm hash trước/sau nạp; sau đó snapshot trong RAM giữ nguyên cho phiên đó. Nếu thay model trên đĩa, phải mở runtime/tiến trình mới để dùng phiên bản mới; không tự hot reload giữa một lượt fault.

Các file workflow mới dùng LF qua .gitattributes; evidence tối ưu và bộ báo cáo có checksum được giữ nguyên byte khi Git checkout. Không đổi quy tắc xuống dòng của source đã khóa.

Giữ nguyên `candidate_v2.py`, `demo_v2.py`, `train_v2.py`, feature contract, thuật toán, ngưỡng và toàn bộ source đã ghi trong development-freeze. Runtime tái sử dụng các hàm predict/extract hiện hữu, không viết lại thuật toán. Registry vẫn có 0 rule active. Không rút ngắn thời gian CPU/history hoặc timeout thu dữ liệu để làm số đo đẹp hơn.

## 2. Quy trình sử dụng

Từ thư mục project, dùng Python đã chọn. Cũng có thể gọi đường dẫn đầy đủ tới tools/lab.py từ nơi khác.

```powershell
Set-Location -LiteralPath 'C:\Users\Darrys\do-an'
python .\tools\lab.py status
python .\tools\lab.py verify
```

`status` chỉ đọc release và VirtualBox; trường `hashes_checked=false` nhắc rằng đây chưa phải bước kiểm tra toàn vẹn. Nếu không đọc được VirtualBox, `vm_diagnostics` ghi loại lỗi thay vì gán VM là poweroff. `verify` kiểm 23 hash nguồn/artifact được release khai báo và 84 observation train/test được khóa. Đây là kiểm nhất quán byte với manifest hiện có, không phải chữ ký số hay phép chứng minh nhãn đúng.

Replay một hoặc nhiều observation có sẵn, không cần bật VM, SSH, Zabbix hoặc cài scikit-learn:

```powershell
$observation = Get-ChildItem -LiteralPath '.\evidence\ml-v2\demos\observations' -Filter '*.json' -Recurse |
    Select-Object -First 1 -ExpandProperty FullName
python .\tools\lab.py replay --observation "$observation"
```

Có thể thêm `--output 'C:\duong-dan-moi\replay.json'` để lưu JSON mới. Nếu file tồn tại, CLI trả exit code 2 và không ghi đè. Không dùng đường dẫn ví dụ này trước khi chọn nơi lưu thật. Không có --output thì chỉ in kết quả. Replay dùng decision_time và bằng chứng lịch sử của observation; kết quả không mô tả sức khỏe hiện tại của VM.

Chỉ khi chủ động muốn tạo lỗi thật, dùng:

```powershell
python .\tools\lab.py demo --fault nginx_stopped
```

Demo yêu cầu cả ba VM đang running, Paramiko trong đúng môi trường và workspace khóa dùng chung đã cấu hình. Nó giữ nguyên Pilot cũ để chờ nền tốt, tạo fault có timer rollback và kiểm tra hồi phục. Mật khẩu được nhập ẩn trong child, không đưa vào CLI/config/output. Các fault khác: agent_stopped, interface_down, remote_http_filtered, dns_egress_blocked, cpu_stress.

Trên máy hiện tại, `tools/lab.local.json` đã trỏ tới workspace coordinator cũ và `.ssh-deps` của workspace. File này được Git ignore, chỉ chứa đường dẫn. Máy khác dùng `lab-settings.example.json` làm mẫu; chọn **đúng workspace đang giữ ml-supervisor.lock/ml-acceptance.lock** và dependency paths, hoặc truyền `--coordination-root`. Không tạo một bộ lock khác để né trạng thái busy. Bản local config có trong ZIP backup đợt tối ưu, không chứa thông tin đăng nhập.

CLI không tự bật/tắt VM. Khi VM chưa chạy, làm theo mục bật VM của hướng dẫn tổng hợp rồi kiểm tra lại status/verify. Wrapper PowerShell `Run-ML-Demo.ps1` cũ vẫn dùng được; nó gọi wrapper Python đã dùng runtime mới. Đường khuyến nghị cho lần demo tới là CLI mới.

Khi Ctrl+C, parent chờ child kết thúc trước khi nhả khóa lab. Đây không phải lệnh xác nhận rollback thành công: sau gián đoạn vẫn phải đọc log và result, kiểm tra postflight, giữ ca uncertain nếu thiếu bằng chứng. Wake request không mở khóa Windows hoặc thay power plan, và không bảo đảm vượt qua mọi trạng thái ngủ của thiết bị.

## 3. Kiểm chứng đã chạy

- **74 tests đạt, 0 failure/error/skip**, gồm 57 tests ML cũ và 17 tests mới. Test mới kiểm cache không nạp DB lặp, không tăng sys.path, không nhầm engine, không lộ mutable cache, giữ nguyên gate/đầu ra, SHA mismatch, hai snapshot demo có provenance, CLI từ chối VM chưa chạy, lỗi config, byte lock giữa hai tiến trình, cleanup khi lỗi và Ctrl+C. Các nhánh fault/Windows wake được dùng mock; không tạo lỗi thật trong test.
- **88 observation cho đầu ra giống toàn bộ với `demo_v2.assess`**: 42 pilot + 42 test giữ riêng + 4 snapshot demo đã lưu. Đối chiếu cả features, expert reasoning, luật khớp, confidence_kind, scope gate và ABSTAIN. Bốn snapshot demo không được gọi là bốn fault độc lập. Đây là regression replay, không phải 88 ca test khoa học mới.
- CLI thực chạy từ workspace ngoài project: status, verify, replay healthy/nginx_stopped/interface_down; lần replay interface_down vẫn ABSTAIN. Đã thử lưu output, từ chối ghi đè và từ chối observation sai schema. Candidate/source đã khóa và release hash không đổi.
- Bộ sinh báo cáo Word cũ và các file nghiệm thu chốt không bị sửa để cập nhật lại điểm số.

Đo **thời gian so sánh expert + CART discrete + FP**, 880 calls cho mỗi cách, cùng các observation đã nạp. Thứ tự hai cách được đảo giữa các vòng để giảm thiên lệch thứ tự:

| Cách chạy | Median (ms/call) | P95 (ms/call) |
|---|---:|---:|
| Hàm cũ mở lại SQLite mỗi call | 1.05285 | 1.59700 |
| Runtime tái sử dụng model | 0.18910 | 0.28740 |

Tỷ lệ median đo được: **5.57 lần**. Đây là phép đo tuần tự cuối sau khi tests kết thúc trên máy hiện tại; cả ba VM đang chạy nền. Không kiểm soát mọi tải Windows/VM nên không coi tỷ lệ này là bảo đảm cho máy khác. Startup gồm kiểm hash release và nạp runtime đo riêng là 54.49 ms; không trộn startup vào warm latency.

Latency này gồm feature extraction, gate, expert và luật ML; không gồm CLI startup, đọc observation, SSH/API, thời gian giữ fault hoặc phát hiện của Zabbix. Nó không so sánh với bảng latency từng thuật toán ngày 31/10 vì phạm vi đo khác. Tối ưu cache không làm mô hình chính xác hơn, không sửa sáu ca ABSTAIN và không giải quyết giới hạn máy thật/multi-fault/topology.

## 4. Bằng chứng, backup và trạng thái VM

- Bằng chứng đợt này: [workflow-final-20261101T084339911460Z](../evidence/workflow-optimization/workflow-final-20261101T084339911460Z/VERIFICATION.json); cùng thư mục có unit-tests.json, benchmark.json, replay-three-states.json, SOURCE_BEFORE_SHA256.json và FILES_SHA256.json.
- Backup **trước sửa**, có working bytes kể cả tài liệu chưa commit và Git bundle đã clone/fsck: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\deliverables\workflow-before-20261101T083315278374Z`; bản thứ hai `D:\Study\network-monitoring-project\backups\workflow-before-20261101T083315278374Z`. CRC và SHA256 mọi member ZIP được kiểm trên cả hai bản.
- Backup sau sửa xem `workflow-after-backup-latest.json` trong workspace. Git bundle chứa lịch sử commit; **working-project.zip mới chứa các thay đổi chưa commit**. Chỉ clone bundle sẽ chưa có code mới. Đọc RESTORE.md và đối chiếu checksum trước khi phục hồi.
- Backup lạnh VM ngày 31/10 vẫn được giữ riêng; gói source này không phải bản sao đầy đủ đĩa VM và không xác nhận dữ liệu VM ở thời điểm 01/11. C/D cùng laptop không thay thế bản sao trên thiết bị khác.
- VirtualBox đọc trực tiếp ngày 01/11 cho thấy MON01/SRV01/CLI01 đều running trước và sau phép đo. Phiên này không gửi start/stop, không SSH và không tạo fault. Ghi nhận poweroff ngày 31/10 là mốc lịch sử.
- **Chưa chạy lại demo lỗi thật sau khi đổi wrapper/runtime.** Đã kiểm unit/mock và replay toàn bộ đầu ra; chưa tuyên bố nghiệm thu live cho bản wrapper mới. Không dùng kết quả demo cũ như bằng chứng wrapper mới đã chạy fault thật.

## 5. Tự kiểm tra khi thay code về sau

```powershell
Set-Location -LiteralPath 'C:\Users\Darrys\do-an'
python .\tools\lab.py verify
python .\tools\verify_workflow.py --output '.\outputs\workflow-check-moi.json'
Set-Location -LiteralPath '.\ml-research'
python -m unittest discover -s tests -v
```

`outputs` là ví dụ vị trí JSON mới; chọn tên mới nếu đã tồn tại. Tests đầy đủ cần dependency từ requirements.txt/requirements-ml.txt trong môi trường ML. Hai lệnh verify/replay và verify_workflow dùng thư viện chuẩn và source hiện hữu, không cần nạp thư viện train. Nếu đổi ngưỡng/feature/model, cần protocol và test mới; regression khớp bản cũ chỉ bảo vệ hành vi, không chứng minh tính đúng đắn ngoài phạm vi đã đo.
