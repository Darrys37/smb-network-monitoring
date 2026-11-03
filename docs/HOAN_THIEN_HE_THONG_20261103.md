# Hoàn thiện hệ thống trên ba VM — 03/11/2026

Đã hoàn thiện và kiểm chứng phần mở rộng hệ thống trên **MON01, SRV01, CLI01**: bảng quyết định chuyên gia trong SQLite, bảy nhóm đặc trưng, gateway có đường đi thật, correlation/suppression, nhiều lỗi đồng thời và worker chạy tự động. Sau đó mới chạy lại demo ML theo đúng thứ tự ưu tiên. Chưa có máy Ubuntu thật; không tính phần đó là đã hoàn thành.

Hướng dẫn thao tác: [system-monitor/README.md](../system-monitor/README.md). Bằng chứng kiểm tra máy được lưu tại [VERIFICATION.json](../evidence/system-v3/acceptance-20261103/VERIFICATION.json), [offline-checks.json](../evidence/system-v3/acceptance-20261103/offline-checks.json). Không dùng phần trăm tiến độ ước lượng để thay thế các tiêu chí dưới đây.

## Phần mới so với trước

| Nội dung | Trước đợt này | Hiện tại |
|---|---|---|
| Luật chuyên gia | R1–R6 bằng Python | Workflow mới đọc 8 luật / 7 nhóm / 40 hàng quyết định từ SQLite; engine cũ giữ để đối chứng |
| Đầu vào hệ thống | Bằng chứng rời; ML có hợp đồng 12 features riêng | Vector v3 có 7 nhóm + giá trị CPU/RAM thô và chất lượng phép đo |
| DNS | Có trạng thái/phản hồi theo collector cũ | Có thời gian truy vấn thực từ `dig Query time`, không dùng thời gian chờ lệnh làm thời gian phản hồi |
| Parent | Ba máy cùng mạng phẳng chưa chứng minh phụ thuộc | CLI01 thực sự chuyển tiếp tới địa chỉ dịch vụ SRV01 qua mạng internal riêng |
| Bão cảnh báo | Chưa có bằng chứng tích hợp | Cửa sổ 30 giây, nhóm có ID ổn định, giữ toàn bộ sự kiện gốc |
| Nhiều lỗi | Chưa kiểm chứng topology/multi-fault | Gateway hỏng + Nginx dừng vẫn giữ hai nhóm độc lập |
| Tự động | Người vận hành chọn/gọi chẩn đoán | systemd worker đọc event/recovery, cursor + queue bền vững, tự thu bằng chứng và lưu kết quả |
| Demo mới | Chưa có wrapper v3 | Một lệnh cho nginx/gateway/multi/storm, kiểm baseline và rollback có timer |
| ML | Runtime tối ưu có kiểm thử offline | Đã diễn tập lại Nginx thật: healthy → nginx_stopped → healthy; không đổi model/freeze |

## Luồng hoạt động cụ thể

1. `event.get` đọc các event mới theo event ID tăng dần. API dùng cận dưới bao gồm giá trị, nên cursor kế tiếp là ID cuối + 1. Khi tạo runtime DB lần đầu, worker bổ sung các problem đang mở dù chúng cũ hơn lookback. [Tài liệu event.get Zabbix 7.0](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/event/get).
2. Một transaction lưu event gốc, tạo job và cập nhật cursor. Event trùng ID không bị xử lý thành bản mới; nội dung bất biến mâu thuẫn bị từ chối. Recovery cũng được lưu. Job lỗi nguồn được giữ và thử lại, không bỏ event khi API/SSH chập chờn.
3. Các job của cùng node dùng chung một lần thu bằng chứng trong một vòng. Ngoài event, worker làm mới probe định kỳ 30 giây để có trạng thái nền và phát hiện dịch vụ cục bộ. Poll 5 giây là khoảng chờ mục tiêu; thời gian thực còn phụ thuộc các probe.
4. Thu Ping, TCP80/10050, HTTP tại đúng IP thuộc máy dịch vụ, DNS trên CLI01, số liệu CPU/RAM/Agent từ Zabbix và trạng thái parent. Bằng chứng không hợp lệ/cũ/lỗi giữ thành unknown/insufficient; không đổi timeout DNS thành một số ms bình thường.
5. `ExpertCatalog` chạy bộ so khớp chung trên điều kiện JSON an toàn đọc từ SQLite. Các luật được xét độc lập: gateway và Nginx có thể đồng thời khớp. Thay ngưỡng trong catalog có thể đổi kết luận mà không sửa hàm phân loại Python. Không dùng `eval`.
6. Correlation dựa trên topology đã khai báo và parent-down còn mới. Những cảnh báo phụ thuộc cùng đợt được gắn nhóm gốc. Lỗi dịch vụ có đo cục bộ độc lập, CPU hoặc DNS không bị ức chế chỉ vì parent down. Sự kiện gốc vẫn ở SQLite và Zabbix.
7. Báo cáo đọc kết quả hiện tại. Nhóm có ID ổn định để theo dõi các lần cập nhật; trong đồ án chưa có kênh gửi email/chat. “Một nhóm gốc” là kết quả tương quan, không phải tuyên bố đã gửi đúng một email.

`matched` là phù hợp tập dấu hiệu, chưa chứng minh duy nhất nguyên nhân vật lý. Mỗi luật có ba giả thuyết kèm hướng điều tra. Điểm 85/65/45% là điểm ưu tiên chuyên gia gán, **không phải xác suất đúng đã đo**. Confidence FP và tỷ lệ lớp ở lá CART cũng là thống kê train, chưa hiệu chỉnh xác suất.

## Bảy nhóm đặc trưng

`[icmp_status, tcp80_status, http_status_code, dns_response_time_ms, resource_status, agent_availability, parent_status]`

`resource_status` gom trạng thái CPU/RAM hiện thời; phần raw vẫn giữ riêng hai tỷ lệ %. Luật quá tải CPU kéo dài kiểm thêm lịch sử/độ phủ/khoảng cách mẫu và thông tin CPU/load. Không coi một mẫu CPU cao là quá tải kéo dài.

Không thể đảm bảo mọi phép đo được chụp đúng cùng một nanosecond. Observation ghi thời điểm thu và sample clock, rồi kiểm độ mới ở decision time. Đó là một snapshot có giới hạn độ lệch/độ cũ, không phải đo đồng bộ tuyệt đối.

## Topology đã kiểm chứng

MON01 có route `172.30.20.0/24 via 192.168.56.30`. CLI01 có NIC3 `172.30.20.1/24` và forwarding. SRV01 có NIC3 `172.30.20.20/24`; policy theo địa chỉ nguồn buộc đường trả về qua CLI01. IP quản trị `192.168.56.10/.20/.30` vẫn hoạt động.

Phép thử MON01 `ping -t 1 172.30.20.20` nhận Time Exceeded từ `192.168.56.30`; HTTP qua địa chỉ routed nhận200. Hai host Zabbix mới (`10685`, `10686`) là hai đối tượng giám sát trên VM hiện có, không phải hai máy mới. Gateway được xác minh chức năng forwarding/interface/route ngay cả khi nó vẫn trả lời ping.

Giữ đường quản trị riêng giúp đọc trạng thái Nginx trên SRV01 khi đường dịch vụ qua gateway bị hỏng. Vì vậy có thể nhận ra “gateway hỏng và Nginx cũng dừng”, thay vì suy rằng mọi thứ phía sau đều chỉ là hậu quả của gateway.

## Kết quả thử thật và phục hồi

Các lượt dưới đây là kiểm tra tích hợp có kiểm soát, **không phải ước lượng accuracy khoa học từ hàng trăm mẫu độc lập**.

| Lượt | Kết quả quan sát |
|---|---|
| Gateway tắt forwarding | 6 sự kiện hoạt động → 1 nhóm CLI01, 4 cảnh báo con bị ức chế; lúc chụp có một job đang xử lý |
| Gateway + 20 kênh synthetic | 26 sự kiện → 1 nhóm, 24 bị ức chế, queue đã xử lý hết; giữ raw |
| Gateway + Nginx dừng | 6 sự kiện → 2 nhóm; R2 và R7 cùng khớp trên SRV01, không mất lỗi dịch vụ |
| Wrapper nginx | 3 sự kiện → 1 nhóm dịch vụ; phục hồi về 0 event/0 job |
| Wrapper multi | 7 sự kiện → 2 nhóm; 4 cảnh báo phụ thuộc bị ức chế; phục hồi về 0/0 |
| Wrapper storm | 25 sự kiện → 1 nhóm; 23 bị ức chế; phục hồi về 0/0 |

Số sự kiện giữa các lượt có thể khác do thời điểm poll và trigger Agent/HTTP. Không sửa dữ liệu để ép các lượt có cùng số cảnh báo. Hai mươi kênh synthetic là phép thử bơm cảnh báo vào Zabbix qua [`history.push`](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/history/push), không đại diện cho 20 sự cố vật lý.

Wrapper được chạy thật tại:

- [Nginx](../evidence/system-v3/demos/20261103T110341211214Z/)
- [Nhiều lỗi](../evidence/system-v3/demos/20261103T110829751598Z/)
- [Bão cảnh báo](../evidence/system-v3/demos/20261103T111020375034Z/)

Timer rollback systemd độc lập đã **thực sự tự chạy** lệnh khởi động Nginx sau thời hạn; journal ghi Started/Deactivated successfully và service active. Các timer của fault được tạo/kiểm tra trước khi tác động. Có `finally` khôi phục sớm; nếu tiến trình laptop mất kết nối thì timer vẫn nằm trong VM.

Trạng thái chốt: ba VM NTP đồng bộ, Agent2 và overlay active; MON01 Zabbix/MySQL/worker active; SRV01 Nginx active; CLI01 forwarding=1. Không còn problem của các host lab đang mở, event hoạt động=0 và pending jobs=0. Legacy `diagnosis.db` vẫn 39 incidents / 301 evidence / 172 diagnoses / 29 recoveries; integrity ok, không có lỗi FK.

## Kiểm thử và độ trễ

33 bài hệ thống và 74 bài ML đều qua. Kiểm tra bao gồm 88 observation lịch sử cho R1–R6, 324 tổ hợp trạng thái/HTTP scope, dữ liệu thiếu/cũ, đổi ngưỡng qua SQLite, dedup/cursor/queue/retry/restart, backfill problem cũ, cycle topology, sự cố độc lập và parent recovery. Các tổ hợp này là regression fixtures, không được tính thành các fault trial mới.

Mã đang chạy trên MON01 được kiểm SHA256 khớp repository. Bộ freeze ML xác minh23 file và84 observation train/test; candidate hash `0e3440b9…edf0` không đổi. Một lần gọi test trực tiếp ban đầu thiếu Paramiko do không nạp dependency_paths; chạy lại đúng môi trường CLI đã qua đủ74 bài, không sửa model để né lỗi môi trường.

Audit cuối có132 event Zabbix (gồm problem/recovery và synthetic), tất cả job done. Độ trễ **từ timestamp event Zabbix đến decision lưu vào DB**: nhỏ nhất3s, median8s, lớn nhất21s. Đây không phải độ trễ từ lúc tác động lỗi; trigger có chu kỳ riêng, Agent nodata còn có cửa sổ30s và HTTP baseline có thể chờ tới chu kỳ tiếp theo.

Benchmark replay tổng hợp, mỗi cấu hình5 lần trên laptop Windows/Python3.14:

| Event | Không suppression: median ms | Có suppression: median ms | Nhóm sau suppression |
|---:|---:|---:|---:|
| 101 | 0.63 | 0.85 | 1 |
| 1.001 | 11.14 | 9.24 | 1 |
| 10.001 | 137.56 | 105.78 | 1 |

Đây chỉ là thời gian thuật toán trong bộ nhớ, không gồm SSH, Zabbix, ingestion SQLite hay tải mạng của10.000 host. Có ít nhóm hơn không tự chứng minh nguyên nhân chính xác hơn. Worker lab hiện đọc lại lịch sử để dựng trạng thái; muốn triển khai lâu dài cần phân trang/index/retention và quản lý active state theo khối, chưa kiểm tải production.

## ML sau cùng đã làm gì?

Đã chạy [demo mới](../evidence/ml-v2/demos/checks/demo-20261103T110440323644Z/result.json), valid=true: trước lỗi CART/FP đề xuất healthy; hai snapshot khi Nginx dừng đều đề xuất nginx_stopped, expert R2 khớp; sau phục hồi cả hai về healthy. Chỉ sử dụng profile cũ SRV01 `.20`, không train lại hoặc bổ sung demo vào tập test đã chốt.

Kết quả nghiên cứu cũ giữ nguyên: numeric CART42/42, discrete CART+gate36/42, FP+gate36/42 trên42 lượt valid test đã tách; ABSTAIN vẫn tính trong mẫu số. Các số này không chứng minh mô hình hỗ trợ nhiều lỗi/gateway mới. Expert v3 chạy độc lập với việc nạp mô hình; ML không dùng kết luận expert làm feature dự đoán. Chương trình demo ML gọi hai nhánh để đối chiếu, chưa tách thành hai dịch vụ vận hành độc lập.

Muốn ML hỗ trợ topology mới cần định nghĩa nhãn multi-fault và feature contract mới, thu dữ liệu phù hợp, tách theo run/session/host rồi train/test lại. Không lấy vector v3 bảy nhóm đưa vào mô hình cũ12 features. Chưa tự kích hoạt learned rules hoặc dùng đề xuất ML để sửa hạ tầng.

## Backup và những việc ngoài phạm vi đã thống nhất

Đã tạo checkpoint SQLite nhất quán, config và secrets riêng trên VM; secrets giữ mode600, không xuất vào Git/source ZIP. File cấu hình root được lưu trong `/var/backups/do-an-system-v3`. Source và bằng chứng mới được sao lưu riêng trên C/D theo receipt backup; không sao chép lại đĩa VM45GB cho lần sửa code này.

Cold backup cũ ở `D:\Study\network-monitoring-project\VM_BACKUP\cold-vms-after-ml-20261101T090139460860Z`, source riêng ở `SOURCE_BACKUP`. Thư mục `backups` cũ đã dọn theo yêu cầu, không sử dụng lại. Cold backup trước v3 chưa chứa topology mới; source/installer và checkpoint hiện tại giúp cài lại. Chưa chạy boot-restore toàn VM trong đợt này.

Các phần còn ngoài phạm vi: máy Ubuntu thật/video máy thật (đã hoãn do chưa có máy); khả năng khái quát của ML trên host/topology/lỗi đồng thời mới; khả năng chịu tải và vận hành production; gửi thông báo ra kênh bên ngoài. Không coi các mục này đã đạt vì demo ba VM thành công.
