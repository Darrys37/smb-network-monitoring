# Hồ sơ nghiệm thu kỹ thuật cuối tuần5

- rehearsals-summary.json và DEMO-*/ là ba lượt live mới, tách khỏi18 trial tuần4. DEMO-01 là attempt bị chặn trước fault; DEMO-01-retry1 là lượt mới.
- rehearsal-protocol-amendment.json ghi trước fault việc chấp nhận đúng các thông báo uptime sau reboot đã phân loại; không đổi trigger hoặc bỏ qua HTTP/Agent problem. final-background-recovery.json xác nhận cuối cùng không còn problem.
- mon01/srv01/cli01-final.json là trạng thái cuối. mon01-hypervisor-recovery.log/vm-recovery-actions.json giữ lỗi và cách khôi phục MON01; snapshot bị lỗi không tính backup hợp lệ.
- pytest.log là test thực tế MON01. pytest-windows-final.log là test từ đúng thư mục trên Windows; các log lỗi thao tác import ban đầu giữ riêng.
- diagnosis-week5-final.db là SQLite backup nhất quán, bị ignored khỏi Git nhưng có trong ZIP bàn giao. sqlite-backup.json ghi SHA; YAML là export host/template, không thay MySQL backup.
- python-mon01-freeze.txt và deployed-package-provenance.json ghi phiên bản thực tế. Nguồn40 tệp engine/test giữ nguyên, chỉ sửa .env.example và README ngoài tập source đóng băng.
- fallback/ là ảnh lịch sử tuần4 đã xem để kiểm tra credential; không gọi là ảnh active fault mới. Private lab IP được giữ để giải thích topology.

tools/ lưu mã điều phối; xác thực nhập ẩn hoặc env tạm, không có mật khẩu/token trong source. week5_rehearse.py thực sự reboot/gây lỗi Nginx, nên chỉ chạy trong lab đã cấu hình theo kịch bản. Các script finalize/assemble/package có đường dẫn máy hiện tại và không phải daemon của sản phẩm.
