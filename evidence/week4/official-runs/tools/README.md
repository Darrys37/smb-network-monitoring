# Công cụ thu và phân tích bộ thử

Các file trong thư mục này là bản cuối của công cụ thực nghiệm, tách khỏi engine đã freeze. Bản `watch_trial.py`/`review_trials.py` ở thư mục cha là checkpoint công cụ cũ; dùng bản trong `tools` khi đọc cách xử lý cuối phiên, đặc biệt retry R5-03.

## Vai trò

- `watch_trial.py`: kiểm tra preflight/source hash, poll đúng host/trigger, gọi engine một lần, đồng bộ recovery và xuất report.
- `inject_*.sh`: fault và rollback trên đúng VM; có kiểm tra hostname, điều kiện nền và thời hạn/timer. Script giữ marker để từ chối ghi lại fault đã chạy.
- `review_trials.py`: đối chiếu fault/rollback log với timestamp event, observer/freshness, collection và lifecycle; ghi review và bảng từng scenario.
- `export_trial_metrics.py`: xuất numeric history và trigger events trong từng cửa sổ thử, có guard giới hạn API.
- `consolidate_trials.py`: tổng hợp CSV/JSON/Markdown; giữ fault không thành công trong mẫu số, tách lần hủy trước fault.
- `finish_experiment.py`: snapshot cấu hình/source/functions, SELECT macro/link chỉ đọc, SQLite backup API và scan exact current API token trong evidence mà không in token.
- `plot_trials.py`, `write_chapter3.py`, `write_progress.py`: tạo hình và bản thảo từ dữ liệu đã đối chiếu. `verify_experiment.py` kiểm tra joins raw–report–CSV, mẫu số, history uniqueness và SHA256 khi sao chép.

## Chạy lại phần phân tích

Các script thu/SQL dùng đường dẫn và host của lab này. Không chạy script fault vào thư mục evidence hiện có để tạo một bộ thử mới. Chuẩn bị root phiên và Run ID mới, cấu hình tương ứng và đủ rollback; không sửa file raw để né marker.

Ví dụ chạy lại phần tổng hợp trên MON01, sau khi đã có các hồ sơ gốc:

```bash
cd ~/do-an/diagnosis-engine
ROOT="$HOME/do-an/evidence/week4/official-runs"
.venv/bin/python "$ROOT/tools/consolidate_trials.py" "$ROOT"
```

Trên máy có Python và thư viện vẽ riêng:

```text
python -m pip install -r plot-requirements.txt
python plot_trials.py PROJECT_ROOT/evidence/week4/official-runs
python write_chapter3.py PROJECT_ROOT
```

Không cài các thư viện vẽ vào venv engine chỉ để chạy lại hình. Runtime tạo hình của phiên nằm ở workspace Windows ngoài project; `plot-requirements.txt` ghi đúng các version đã dùng. CSV là nguồn dữ liệu cho hình; mỗi chấm là một trial, vạch là median, không có suy diễn khoảng tin cậy từ ba mẫu.

## Checksum và backup

`checksums-final.json` là pathname → SHA256 của toàn bộ cây evidence sau khi hoàn tất, không chứa hash của chính nó. Các manifest checkpoint R1–R2/R1–R3 đại diện trạng thái sớm hơn; bảng dẫn xuất/công cụ đã có phiên bản mới sau checkpoint.

Backup `.db` được giữ tại MON01 và Windows, tách khỏi commit Git theo `.gitignore`; muốn kiểm tra **đầy đủ** manifest sau một lần clone phải khôi phục các file backup đó từ nơi lưu. Các report JSON/CSV/Markdown trong Git vẫn cho phép phân tích kết quả mà không dùng database runtime. `.env`, venv và thông tin xác thực không được đưa vào evidence.

Hai bản trên cùng laptop không thay thế backup ngoài thiết bị. Chưa có chứng nhận diễn tập phục hồi hoặc release cuối chỉ từ một lần checksum pass.
