\# Hệ thống giám sát và hỗ trợ chẩn đoán sự cố mạng



\## Giới thiệu



Đồ án xây dựng hệ thống giám sát tập trung cho mô hình mạng

doanh nghiệp nhỏ bằng Zabbix và module Python.



Zabbix thu thập dữ liệu giám sát và phát hiện sự cố.

Module Python dự kiến thu thập thêm bằng chứng, áp dụng các

quy tắc chẩn đoán và lập hồ sơ sự cố gồm nguyên nhân có thể,

thông tin còn thiếu và hướng xử lý.



Hệ thống không sử dụng AI/học máy và không tự động sửa lỗi.



\## Mô hình triển khai



Các máy ảo chạy Ubuntu Server trên VirtualBox.



| Máy | IP Host-only | Vai trò |

|---|---|---|

| MON01 | 192.168.56.10/24 | Dự kiến chạy Zabbix và module Python |

| SRV01 | 192.168.56.20/24 | Máy chủ Nginx và SSH được giám sát |

| CLI01 | 192.168.56.30/24 | Máy khách kiểm tra kết nối và dịch vụ |



Mỗi máy có hai card mạng:



\- enp0s3: NAT, phục vụ kết nối Internet.

\- enp0s8: Host-only, phục vụ giao tiếp trong mạng lab.



Mạng lab: 192.168.56.0/24.

Card Host-only trên Windows: 192.168.56.1/24.

Các máy ảo sử dụng IP tĩnh trên card Host-only.



\## Trạng thái triển khai



Đã hoàn thành hạ tầng lab:



\- Ba máy liên lạc được bằng ICMP.

\- CLI01 truy cập Nginx trên SRV01 và nhận HTTP 200.

\- CLI01 đăng nhập SSH vào SRV01 thành công.

\- IP tĩnh được giữ sau khi khởi động lại.

\- Đã tạo snapshot và lưu bằng chứng kiểm tra.



Zabbix và module Python chưa được triển khai.



\## Kiểm tra dịch vụ



Chạy từ CLI01:



```bash

ping -c 4 192.168.56.20

curl -I --connect-timeout 5 http://192.168.56.20

ssh phat@192.168.56.20

