# Hiện trạng và cách tiếp tục đồ án

## Shutdown, backup và xuất bản — 01/11/2026 16:08 UTC+7

- **Trạng thái mới nhất: MON01/SRV01/CLI01 đều poweroff**, shutdown qua ACPI theo yêu cầu người dùng. Ghi nhận running ở mục tối ưu phía dưới là trước lần shutdown này.
- Backup lạnh mới đầy đủ 45.83 GB / 56 tệp / 28 đĩa, SHA256 khớp: `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261101T090139460860Z`. Chưa boot thử phục hồi; không khởi động lại VM chỉ để đọc báo cáo.
- [Chi tiết backup/xuất bản](../SAO_LUU_VA_GITHUB_20261101.md). Nhánh đích GitHub `feature/ml-research-v2`; đọc receipt workspace `github-push-latest.json` để xác minh commit/remote sau push. Source backup cuối xem `workflow-after-backup-latest.json`.
- Git giữ raw byte evidence ML và pin LF/CRLF của frozen source đúng bản gốc; source/model/nhãn và điểm thực nghiệm không đổi. Khi clone sang thư mục khác vẫn phải lưu ý absolute paths của historical manifests; không sửa freeze để né kiểm tra.

## Tối ưu workflow/runtime — 01/11/2026

- [Quy trình và kết quả tối ưu](../TOI_UU_QUY_TRINH_20261101.md): `tools/lab.py status|verify|replay|demo`, CandidateRuntime nạp SQLite một lần/phiên; DemoPilot đã dùng runtime mới. Giữ nguyên code/model đã đóng băng, feature/gate/nhãn và 0 rule active.
- 74 tests đạt; 88 observation lịch sử có đầu ra đầy đủ khớp bản cũ. Warm median so sánh expert+ML 1.05285 → 0.18910 ms (5.57 lần); không phải độ trễ SSH/API/phát hiện lỗi hoặc accuracy mới. Bằng chứng `evidence/workflow-optimization/workflow-final-20261101T084339911460Z`.
- **Trạng thái đọc trực tiếp ngày 01/11: MON01/SRV01/CLI01 đều running**. Phiên tối ưu chỉ kiểm offline, không start/stop VM, không SSH/fault; trạng thái poweroff ngày 31/10 bên dưới là lịch sử. Wrapper mới chưa được chạy lại fault live.
- Machine-local `tools/lab.local.json` trỏ đúng workspace giữ khóa coordinator và dependency paths; chỉ chứa đường dẫn, Git ignore. Xem backup before/after trong workspace; working-project.zip mới chứa thay đổi chưa commit, bundle chỉ chứa lịch sử commit. Backup lạnh VM 31/10 giữ riêng.

## Tài liệu tổng hợp và shutdown/backup — 31/10/2026

- Đã hoàn thành [bộ báo cáo và hướng dẫn](../TONG_HOP_VA_HUONG_DAN_20261031/README.md): báo cáo 15 trang, hướng dẫn 11 trang, cả Word và Markdown. Số liệu lấy từ release chốt phía dưới; chỉ bổ sung tài liệu, không đổi predictor hoặc evidence đã khóa. `DOCUMENTS_QA.json` ghi kiểm tra nguồn, render và xem đủ 26 trang.
- **Trạng thái tại mốc backup 31/10: MON01, SRV01, CLI01 đều poweroff**, shutdown qua ACPI theo yêu cầu người dùng. Không còn chiến dịch thu dữ liệu đang chạy. Các ghi nhận dịch vụ tốt bên dưới là postflight trước khi shutdown, không phải dịch vụ đang chạy hiện tại.
- Backup lạnh đầy đủ đã đối chiếu SHA256: `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261031T142959433223Z` (56 tệp, 28 hard disk, 45,704,094,798 byte). Đọc `VERIFICATION.json`, `FILES_SHA256.json`, `DISK_CHAINS.json`, `RESTORE.md`; chưa boot thử bản phục hồi. Receipt workspace: `cold-vm-backup-latest.json`.
- Chỉ xem báo cáo không cần bật VM hoặc chạy lại `full_ml_session.py`. Nếu demo live, dùng hướng dẫn mới; kiểm tra máy thức, thứ tự bật VM và điều kiện nền trước khi can thiệp.

## Hoàn tất nghiệm thu ban đầu phần ML trên ba VM — 31/10/2026 21:13 UTC+7

**COMPLETE_INITIAL_VM_ML_RELEASE_VERIFIED.** Chuỗi thu dữ liệu, huấn luyện, test mới, SQLite/shadow, báo cáo/hình và một demo lỗi thật đã hoàn tất. Đây là phạm vi ba VM hiện có; chưa có máy Ubuntu thật, multi-fault hoặc topology/suppression.

- Train/development: 42 valid; 9 uncertain được giữ riêng. Test mới khóa trước khi thu: 42 valid; 1 uncertain giữ riêng. Mỗi run chỉ dùng cửa sổ cuối; không tính hai cửa sổ của một fault thành hai phép thử độc lập.
- Đã kiểm tra hash nguồn/nhãn/raw, embargo, cùng đầu vào expert/ML, model Python/SQLite và 42 ca shadow lúc fault. Registry có hai model được validated cho nghiên cứu, **không có rule active** trong engine vận hành.
- Báo cáo thật: `evidence/ml-v2/locked-test-v1/evaluation/20261031T140643065544Z/presentation-20261031T141036524152Z/BAO_CAO_NGHIEM_THU.md`. Bảng luật: cùng thư mục `LUAT_HOC_DUOC.md`. CSV/JSON đầy đủ: `evidence/ml-v2/locked-test-v1/evaluation/20261031T140643065544Z`.

| Mô hình | Đúng / tổng test | Macro-F1 | Coverage |
|---|---:|---:|---:|
| cart_numeric | 42/42 | 1.000 | 100.0% |
| cart_discrete | 36/42 | 0.857 | 85.7% |
| fp_classifier | 36/42 | 0.857 | 85.7% |
| majority | 6/42 | 0.036 | 100.0% |
| cart_missingness | 22/42 | 0.432 | 100.0% |

- Expert trả sáu nhận định độc lập; đọc bảng theo diagnostic family, không gán một accuracy bảy lớp cho expert. Confidence/lift và tỷ lệ lớp tại lá là thống kê train, không phải xác suất chẩn đoán đúng đã hiệu chỉnh.
- Demo thật: `evidence/ml-v2/demos/checks/demo-20261031T141114556079Z/result.json`; raw/comparisons ở `evidence/ml-v2/demos`. Chạy lại trên laptop bằng `pwsh -NoProfile -File "C:\Users\Darrys\Documents\ChatGPT\Đồ án network\Run-ML-Demo.ps1"`; nhập SSH ẩn. Wrapper giữ khóa lab và yêu cầu màn hình/system thức tạm thời. Không chạy cùng coordinator thu dữ liệu.
- Postflight sau demo: dịch vụ/HTTP/DNS/control tốt, không còn timer/firewall/stress của lượt; engine source và SQLite runtime vẫn 39 incidents /301 evidence /172 diagnoses /29 recoveries. Bằng chứng `evidence/ml-v2/verification/final-acceptance-20261031T141341675699Z`.
- Từng có Modern Standby làm gián đoạn lab; giữ power-event evidence và các lượt uncertain. Guard hiện tái áp dụng yêu cầu display/system mỗi 15 giây và clear khi kết thúc. Không đổi power plan, lock policy, affinity/priority, CPU/RAM VM. Không quy mọi RCU stall lịch sử về cùng nguyên nhân.
- Kết quả chỉ cho các can thiệp lỗi đơn đã biết trên SRV01, test cân bằng cùng host. Không suy chất lượng production, tỷ lệ lỗi thực tế, chuyển máy thật hoặc suy luận nhân quả từ các điểm số này.
- Hạn chế đã biết từ pilot: che HTTP/DNS thành unknown trên một vector healthy giả định có core probes tốt khiến CART gợi ý interface_down, FP từ chối. Đây là phân tích feature giả định, không phải lượt fault thực; mô hình giữ nguyên, chưa được phê duyệt production. Báo cáo chính giữ vector và SHA gốc.
- Accuracy phân loại và việc Zabbix phát hiện là hai phép đo riêng. Collector được gọi theo lịch; chưa chứng minh tự động event-to-process dispatch. Audit detection đi kèm báo cáo, nêu rõ SRV01 chưa có trigger DNS/ICMP riêng.
- Không cần chạy lại `full_ml_session.py` để xem báo cáo. Source đúng ở repository; workspace stage `ml-v2` cũ không được ghi đè lên đây. Backup chốt xem `ml-final-checkpoint-latest.json` trong workspace và receipt trong thư mục backup C/D.

Các ghi chú tiến độ cũ được giữ trong [lịch sử trước nghiệm thu](../../evidence/ml-v2/verification/final-acceptance-20261031T141341675699Z/handoff-status-before-final.md).

## Bản bàn giao nền ngày 17/10/2026

Bản bàn giao ngày **17/10/2026, UTC+7**. Công việc gần nhất về chương trình là tối ưu đọc Zabbix; sau đó đã lưu Git/GitHub, sao lưu và shutdown lab. Phiên sắp xếp tài liệu chỉ thay tài liệu/công cụ đóng gói, không khởi động VM.

## 1. Source nào là đúng?

| Nội dung | Vị trí / phiên bản |
|---|---|
| Repository chính trên laptop | `C:\Users\Darrys\do-an` |
| Engine Python | `C:\Users\Darrys\do-an\diagnosis-engine` |
| GitHub | [Darrys37/smb-network-monitoring](https://github.com/Darrys37/smb-network-monitoring) |
| Commit chương trình gần nhất đã kiểm thử và triển khai | [`34bf592cf83e0fa39d36a1fecf8a836d3dc25eab`](https://github.com/Darrys37/smb-network-monitoring/commit/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab) |
| Mốc cleanup trước đó | `7d32be7` |
| Mốc kỹ thuật kết thúc tuần 5 | `26b581e`, tag `week5-technical-20261017` |
| Mốc nghiệm thu tuần 4 | tag `week4-complete-20261017` |
| Nhật ký trên D: | `D:\Study\network-monitoring-project\docs\bangiao` |
| Engine chạy trên MON01 | `/home/phat/do-an/diagnosis-engine` |

Các commit tiếp theo có thể chỉ cập nhật tài liệu. Đối chiếu `MANIFEST.json` và cây `diagnosis-engine` trước khi kết luận chương trình đã đổi. Nhánh GitHub `main` có thể tiếp tục phát triển sau ngày bàn giao; các liên kết ghim trong gói mô tả đúng phiên bản đã gửi.

**Không dùng bản tiến độ cũ trên D: để ghi đè trạng thái hiện tại.** Trước khi sắp xếp, file `BAO_CAO_TIEN_DO_20261017.md` ở D: khác và cũ hơn file cùng tên trong project. Các báo cáo tiến độ vẫn là nhật ký lịch sử; file này mới là bản chốt tiếp nhận tại ngày nêu trên.

## 2. Đã đi đến đâu theo roadmap?

- Tuần 1–3: dựng lab, Zabbix/Agent, API và engine Python; tài liệu bàn giao cũ chỉ cần khi truy lịch sử.
- Tuần 4: có 18 lượt fault hợp lệ thuộc sáu nhóm, mỗi nhóm ba; một attempt bị hủy trước fault được giữ riêng. Baseline theo lựa chọn phiên ngắn dài **30 phút 06 giây**, không đạt mục tiêu bốn giờ nếu có thể trong roadmap.
- Tuần 5: phần kỹ thuật ngày 29–35 đã hoàn tất: đối chiếu dữ liệu, bảng/hình, Chương 2/3, báo cáo, hướng dẫn, slide, demo và backup. Đây là mốc hoàn thành kỹ thuật; chưa đồng nghĩa giảng viên đã duyệt hoặc bài đã nộp.
- Sau tuần 5: cleanup thống nhất logic và làm code dễ giải thích, rồi tối ưu các lần đọc Zabbix. Người dùng đã chủ động yêu cầu các công việc sau mốc đóng băng; kết quả không được nhập ngược vào bộ thực nghiệm tuần 4.
- Công việc tối ưu trước đó đã hoàn tất và được lưu. Không có fault/baseline đang chạy hay một tính năng mới đang triển khai dở được giao tiếp trong bản bàn giao này.

Việc còn cần chủ đồ án xác nhận trước nộp: định dạng theo mẫu trường, tự trình bày/bảo vệ, bản sao lưu ngoài laptop. Các mở rộng như profile host hoặc giao diện cần một yêu cầu mới và phạm vi cụ thể.

## 3. Các thay đổi mới nhất cần biết

Cleanup `7d32be7`:

- CLI và hàm Python cùng mặc định HTTP scope `unknown`; máy có web cần `expected`, máy không có HTTP dùng `absent`.
- Tách rõ orchestration, collection/import, rule và repository; gom ngưỡng roadmap trong `policy.py`.
- HTTP/DNS kiểm tra file ngoài qua validation chung; DNS có đối chiếu query/control/observer và tương thích probe cũ hợp lệ.

Tối ưu `34bf592`:

- `collect_roadmap_metrics(host_id)` gộp ba lần `item.get` thành một lần lấy sáu key của cùng host.
- Bốn metric ngữ cảnh, agent_metric và cpu_history dùng mốc nhận cùng phản hồi item; `lastclock` mẫu giữ nguyên. History CPU vẫn đọc riêng.
- Một lượt roadmap thành công có CPU history giảm **8 xuống 6 request API**; vẫn xác minh event trước và sau collection.
- Không có cache qua các lượt. Thứ tự evidence thay đổi, rule chọn theo loại/target/port/thời gian, không theo chỉ số list.
- Giữ điều kiện R1–R6 và cấu trúc SQLite/report/probe. Chưa có benchmark trước/sau để công bố phần trăm tăng tốc.

Đọc mục 17 file 03 trước khi sửa collection; đọc mục 16 để hiểu đợt cleanup. Các chương báo cáo cũ mô tả mốc tuần 5, vì vậy không dùng chúng thay source hiện hành khi phát triển tiếp.

## 4. Đã kiểm chứng được gì?

| Mốc | Kiểm chứng đã thực hiện |
|---|---|
| Tuần 5 (`26b581e`) | 280 tests Windows và 280 tests MON01; ba demo HTTP sau reboot có problem → incident → recovery |
| Cleanup (`7d32be7`) | 355 tests ở hai môi trường; đối chiếu 576 tổ hợp tổng hợp; 108 kết luận của 18 hồ sơ cũ giữ nguyên |
| Tối ưu (`34bf592`) | 369 tests ở hai môi trường; 15 tình huống collector khớp bản trước; 108 kết luận lịch sử giữ nguyên; Ruff lint/format đạt |
| Thu thử thật sau tối ưu | Một item.get và một history.get, 10 evidence với host đối chứng; các phép đo bình thường, R4 thiếu DNS probe nên insufficient |
| Khi triển khai tối ưu | Source MON01 đối chiếu hash; DB/.env không đổi; SQLite integrity=ok, không lỗi foreign key |

Các số test là kết quả của những lần chạy đã ghi nhận, không phải cam kết lần chạy mới chắc chắn đạt. 18/18 là tỷ lệ mục tiêu khớp trong bộ thử nhỏ, **không phải accuracy tổng quát 100%**; chưa có tập âm độc lập. Engine có thể trả nhiều matched/insufficient cùng lúc; chưa có xếp hạng nguyên nhân gốc.

## 5. Lab và trạng thái kết thúc phiên

| VM | SSH / IP | Vai trò | Host ID Zabbix |
|---|---|---|---|
| MON01 | `ssh phat@192.168.56.10` | Zabbix, MySQL, frontend 8080, Agent2, engine và SQLite | `10084` |
| SRV01 | `ssh phat@192.168.56.20` | Nginx 80, Agent2, local HTTP observer | `10683` |
| CLI01 | `ssh phat@192.168.56.30` | Agent2, DNS observer và host đối chứng | `10684` |

**Trạng thái được xác nhận lúc 19:52:44 ngày 17/10/2026 (UTC+7): cả ba VM đã `PowerOff` bằng shutdown an toàn.** Đây là kết quả cuối phiên trước, không phải kiểm tra live ở mỗi lần mở tài liệu. Khi người dùng yêu cầu làm tiếp trên VM, kiểm tra VirtualBox và kết nối thực tế; VM đang tắt sẽ không phản hồi SSH.

Trước khi shutdown, cả ba phản hồi SSH, các dịch vụ liên quan active và không có problem mở trên ba host. SQLite runtime có 39 incidents, 301 evidence, 172 diagnoses, 29 recoveries. Số hàng này gồm các giai đoạn trước và demo, không phải chỉ 18 lượt chính thức tuần 4.

MON01 từng mất phản hồi trong quá trình làm việc, đã được người dùng reset rồi kiểm tra lại trước khi triển khai. Nguyên nhân sự cố VM chưa được kết luận; không coi tối ưu Python là đã sửa lỗi VirtualBox.

Ba IP dùng Host-only cùng subnet; không có router trung gian chung. R5 dùng phương án firewall TCP80. Live collector dùng `ping`, `dig`, `ip` trên Linux; tests đạt trên Windows không chứng minh live collector chạy native Windows. Host ID và target IP còn truyền riêng, chưa tự đối chiếu mapping.

Gói tài liệu không chứa mật khẩu, API token, `.env` hoặc database. Nếu cần truy cập, lấy quyền và thông tin xác thực từ chủ đồ án hoặc môi trường đã được chủ đồ án cấu hình.

## 6. Sao lưu và phục hồi ở đâu?

- Source/docs/evidence của mốc tối ưu: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\deliverables\engine-optimization-20261017T125023Z` và `D:\Study\network-monitoring-project\backups\engine-optimization-20261017T125023Z`.
- Có Git bundle, ZIP và biên bản đã thử khôi phục bundle/fsck. Gói này **không chứa `.env` hay SQLite runtime**.
- Source MON01 trước tối ưu: `/home/phat/diagnosis-before-optimization-20261017T124751Z`.
- Bộ backup cuối tuần 5 có SQLite nhất quán nằm riêng tại các thư mục `week5-20261017T025017Z` trong hai gốc backup trên. Đối chiếu manifest/commit/thời điểm trước khi phục hồi; đó là mốc tuần 5, không tự chứa code tối ưu mới.
- GitHub lưu tracked source/docs/evidence; không thay backup VM/MySQL/SQLite hay các secret. Hai ổ C:/D: vẫn thuộc cùng laptop.

## 7. Cách tiếp tục một phiên mới

1. Xác nhận yêu cầu mới của người dùng. Những đề xuất dưới đây chưa phải nhiệm vụ tự động thực hiện.
2. Nếu có source: kiểm tra `git status`, nhánh, HEAD và remote; giữ các sửa đổi chưa commit của người dùng. Đọc file 03 và những module liên quan.
3. Nếu nhiệm vụ cần VM: kiểm tra VM thực tế, dịch vụ và problem nền trước khi chạy. Việc đọc tài liệu không cần bật lab.
4. Khi sửa: collector thu bằng chứng, rule chỉ đánh giá, repository ghi SQLite. Giữ ba trạng thái, scope/observer/freshness và kiểm tra event trước/sau.
5. Chạy kiểm tra phù hợp, dùng dữ liệu lịch sử để kiểm tra hồi quy khi đổi logic. Không ghi đè hồ sơ/tag thực nghiệm cũ. Nếu thay schema/ý nghĩa chẩn đoán hoặc gặp vấn đề quan trọng, nêu tác động và hỏi người dùng.
6. Cập nhật tài liệu và trạng thái cuối phiên theo kết quả thật, rồi lưu Git/backup theo phạm vi được giao.

Các hướng có căn cứ để cân nhắc: cấu hình theo host và xác minh host→IP; version hóa rule/assessment trước khi hỗ trợ chẩn đoán lại; bổ sung dữ liệu âm/nhiều lỗi để đánh giá. Chưa có lý do đã được kiểm chứng để tự thay engine bằng AI/ML, thêm confidence score hoặc tự khắc phục.

## 8. Chỉ mở thêm khi cần

Các liên kết dưới ghim tại mốc chương trình `34bf592` để gói vẫn dùng được ngoài laptop:

- [Source engine](https://github.com/Darrys37/smb-network-monitoring/tree/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/diagnosis-engine).
- [Hướng dẫn cài/chạy/khôi phục](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md).
- [Tổng hợp tuần 5](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/TONG_HOP_TUAN_5.markdown).
- [Bộ 18 lượt thực nghiệm](https://github.com/Darrys37/smb-network-monitoring/tree/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/evidence/week4/official-runs).
- [Báo cáo tổng hợp](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/BAO_CAO_DO_AN_HOAN_THIEN.markdown).

Nếu tài khoản khác không truy cập được repository, cung cấp source hoặc artifact đúng phạm vi cần sửa qua kênh người dùng cho phép. Không suy đoán các file chưa đọc từ nội dung nhật ký.
