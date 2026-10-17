# Câu hỏi ôn bảo vệ

Tự trả lời và chỉ vào source/evidence trước khi trình bày; bộ câu trả lời này không chứng nhận người trình bày đã hiểu hoặc diễn đạt được toàn bộ luồng.

1. **Zabbix và module khác nhau ở đâu?** Zabbix thu metric, đánh giá trigger và lưu MySQL. Python đọc problem, thu evidence hiện tại, chạy luật và lưu SQLite. app.py không phải daemon hoặc auto-remediation.
2. **Có sáu trigger cho sáu luật không?** Không. R1/R2/R5 dùng HTTP trigger25334; ping/TCP/local HTTP giúp luật phân biệt giả thuyết. Xem trigger-scenario-map ngày31.
3. **R2 và R5 khác nhau thế nào?** Ping tốt, remote TCP thất bại; local HTTP200 phản bác service-down và hỗ trợ nghi đường truy cập. TCP refused vẫn chưa chứng minh Nginx dừng. R5 không tự đọc firewall.
4. **Tại sao phải đo từ CLI01?** DNS và IP control phải cùng observer. DNS của MON01 không đại diện DNS của máy khách. IP đối chứng thành công chỉ hỗ trợ cô lập, không chứng minh toàn Internet khỏe.
5. **Vì sao có insufficient_evidence?** Dữ liệu thiếu/cũ/lỗi không đủ để kết luận. Ví dụ R5-02 có CPU span239s thay240s. Không chuyển thiếu dữ liệu thành true negative.
6. **CPU trigger và R6 có giống nhau không?** Trigger min>90% trong5m; R6 mean≥90%, đủ độ phủ, load≥CPUcount. Trigger còn có dependency load-high. Chưa chứng minh mọi dạng overload hoặc ứng dụng chậm.
7. **Tại sao kiểm tra event hai lần?** Recovery có thể xảy ra lúc thu. Kiểm tra trước/sau giảm nguy cơ ghi hồ sơ cho problem đã đóng; vẫn không tạo transaction xuyên Zabbix và SQLite.
8. **Làm sao tránh hồ sơ trộn hai lần thu?** event_id UNIQUE, bundle transaction BEGIN IMMEDIATE, từ chối append khi đã có evidence/diagnoses. Lỗi rollback toàn transaction.
9. **Recovery được xác nhận thế nào?** r_eventid trỏ đúng event, cùng trigger/host, value1→0, thời gian hợp lệ; ghi bổ sung, không sửa evidence cũ. Chưa lưu recovery thì unverified, chưa biết hiện trạng.
10. **18/18 có phải accuracy100% không?** Đây là tỷ lệ luật mục tiêu khớp trên18 fault hợp lệ. Không có mẫu âm độc lập, không tính accuracy cóTN hoặc false-positive rate. n=3 mỗi loại chỉ là mô tả lab.
11. **Lượt R5-03 bị loại vì sao?** Bị chặn trước khi lệnh fault chạy, không có ground truth fault. Giữ attempt và adjudication, retry có ID riêng; không loại một kết quả chẩn đoán sai.
12. **Các mốc thời gian khác nhau thế nào?** DT từ fault đến problem có hai cận timestamp; CLI elapsed gồm API/thu/luật/SQLite; recovery recognition từ rollback đến recovery. Problem–recovery không phải downtime thật.
13. **Tại sao baseline không4h?** Người thực hiện chọn phiên ngắn, đo30m06s. 0 problem trong phiên đó không chứng minh vận hành nhiều ngày hoặc engine không có false positive.
14. **Backup nào phục hồi được gì?** Bundle phục hồi source/history, SQLite backup phục hồi incident, YAML phục hồi cấu hình host/template. YAML không thay MySQL/VM. C vàD cùng laptop không chống mất thiết bị.
15. **Mở rộng thế nào?** Tập âm gắn nhãn, nhiều host/topology/tải, baseline dài hơn, profiling từng pha và response-time đối chứng; chỉ thêm chức năng sau khi có tiêu chí kiểm chứng.
