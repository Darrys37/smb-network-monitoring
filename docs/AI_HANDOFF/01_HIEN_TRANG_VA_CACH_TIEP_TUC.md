# Hiện trạng và cách tiếp tục đồ án

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
