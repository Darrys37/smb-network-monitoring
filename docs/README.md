# Tài liệu hệ thống giám sát và chẩn đoán mạng

Trang này phân biệt hướng dẫn **Worker V3** với các báo cáo và nhật ký của phiên bản trước. Để hiểu hệ thống đang dùng cho demo, bắt đầu bằng ba liên kết đầu tiên dưới đây.

## Đọc theo nhu cầu

| Nhu cầu | Tài liệu |
|---|---|
| Hiểu bài toán, kiến trúc và 8 luật | [Giới thiệu ở README chính](../README.md) |
| Chạy worker, xem kết quả, tạo lỗi và phục hồi | [Hướng dẫn vận hành V3](../system-monitor/README.md) |
| Triển khai lại mạng và thành phần V3 | [Hướng dẫn triển khai](../system-monitor/deployment/README.md) |
| Xem kết quả thử gateway, Nginx, multi-fault và storm | [Báo cáo kiểm chứng hệ thống](HOAN_THIEN_HE_THONG_20261103.md) |
| Xem bằng chứng nghiệm thu có cấu trúc | [VERIFICATION.json](../evidence/system-v3/acceptance-20261103/VERIFICATION.json) |
| Xem mã nguồn điều kiện các luật | [expert_seed.json](../system-monitor/config/expert_seed.json) |

Báo cáo kiểm chứng ghi nhận kết quả ở ngày tạo tài liệu. Một số mục trong báo cáo thuộc hướng nghiên cứu riêng; phạm vi giới thiệu và demo hiện tại là worker chuyên gia V3. Không dùng số liệu của một nhánh nghiên cứu để thay cho kết quả V3.

## Bản đồ đọc mã nguồn V3

```text
monitor.py
  → monitoring/worker.py        đọc sự kiện, điều phối và xử lý hàng đợi
  → monitoring/collector.py     lấy dữ liệu Zabbix và probe
  → monitoring/facts.py         kiểm tra dữ liệu, độ mới, lịch sử CPU
  → monitoring/catalog.py       đọc và thực thi bảng quyết định SQLite
  → monitoring/correlation.py   gom cảnh báo theo topology
  → monitoring/store.py         lưu sự kiện và kết quả
  → report.py                   xem trạng thái đã xử lý
```

Đường dẫn trong sơ đồ nằm dưới [`system-monitor/`](../system-monitor). Bảy nhóm đặc trưng và 8 luật thuộc luồng này. Engine CLI gốc trong `diagnosis-engine` có luồng sử dụng riêng.

## Báo cáo và tài liệu phiên bản trước

Các file sau được giữ để tham khảo kiến trúc nền, phép thử cũ và quá trình phát triển. Đọc đúng mốc phiên bản: có tài liệu mô tả R1–R6 hoặc gọi CLI thủ công, khác với worker tự động V3 và mạng dịch vụ qua gateway hiện tại.

| Tài liệu | Nội dung |
|---|---|
| [Báo cáo tổng hợp baseline](BAO_CAO_DO_AN_HOAN_THIEN.markdown) | Báo cáo ở mốc hoàn thành engine gốc |
| [Kiến trúc và triển khai baseline](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md) | Nền tảng Zabbix và mô hình ban đầu |
| [Thực nghiệm baseline](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md) | Phương pháp và dữ liệu thử phiên bản trước |
| [Giải thích engine CLI gốc](GIOI_THIEU_VA_GIAI_THICH_DO_AN.md) | Cơ chế engine gốc và các mốc cập nhật của nó |
| [Logic và phát triển engine CLI](DIAGNOSIS_ENGINE_LOGIC_VA_PHAT_TRIEN.md) | Hợp đồng dữ liệu và logic R1–R6 |
| [Kịch bản demo CLI trước V3](KICH_BAN_DEMO_10_PHUT.md) | Thao tác gọi `app.py` thủ công; không dùng để mô tả worker tự động |
| [Cài đặt và khôi phục baseline](HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md) | Triển khai thành phần nền và phục hồi bản cũ |
| [Câu hỏi bảo vệ bản gốc](CAU_HOI_BAO_VE.md) | Tham khảo và đối chiếu lại với phạm vi V3 |

## Lịch sử và bàn giao

- [Bộ tài liệu AI_HANDOFF](AI_HANDOFF/00_BAT_DAU_O_DAY.md): hỗ trợ tiếp nhận ngữ cảnh. Các snapshot có ngày/phiên bản riêng; kiểm tra source trước khi tiếp tục sửa.
- [Hồ sơ thử hệ thống V3](../evidence/system-v3): kết quả từng lượt thử và demo.
- [Hồ sơ thực nghiệm baseline](../evidence/week4/official-runs): dữ liệu và log của các phép thử cũ.
- [Nhật ký tổng hợp giai đoạn nền](TONG_HOP_TUAN_4.markdown) và [mốc bàn giao cũ](TONG_HOP_TUAN_5.markdown): lịch sử triển khai, không phải danh sách việc còn thiếu hiện tại.

Các nhật ký ngày/tuần được giữ nguyên để truy vết. Người mới không cần đọc toàn bộ chúng để chạy hoặc hiểu Worker V3.
