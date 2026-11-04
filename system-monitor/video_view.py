"""Explain saved worker measurements without inventing unavailable evidence."""
PING={'success':'Có phản hồi','no_reply':'Không phản hồi'}
TCP={'success':'Kết nối được','refused':'Bị từ chối kết nối','timeout':'Hết thời gian chờ'}
SERVICE={'active':'Đang chạy','inactive':'Đã dừng','failed':'Bị lỗi','activating':'Đang khởi động','deactivating':'Đang dừng'}
DNS={'success':'Phân giải thành công','timeout':'Hết thời gian chờ','nxdomain':'Tên miền không tồn tại','no_answer':'Không có bản ghi trả lời','dns_error':'Máy chủ DNS trả lỗi'}
CHECK={
 'R1':'Đích không trả lời ICMP/TCP, nhưng máy đối chứng còn phản hồi.',
 'R2':'Nginx inactive/failed là bằng chứng trực tiếp; kiểm thêm ping và cổng web.',
 'R3':'Đối chiếu trạng thái Agent, mẫu số liệu và khả năng kết nối tới máy.',
 'R4':'DNS lỗi trong khi kết nối IP đối chứng cùng máy quan sát vẫn tốt.',
 'R5':'Ping tốt, TCP/80 từ xa lỗi nhưng HTTP tại máy chủ vẫn trả 200.',
 'R6':'CPU trung bình đạt ngưỡng, đủ lịch sử hợp lệ và load >= số CPU.',
 'R7':'Nút cha có bằng chứng down mới; gom các cảnh báo kết nối phụ thuộc.',
 'R8':'Có ít nhất 10 sự kiện lỗi mới trong cửa sổ 30 giây.'}
MEANING={
 'R1':'Khoanh vùng mất kết nối tới đích; chưa khẳng định máy đã tắt.',
 'R2':'Dấu hiệu phù hợp sự cố dịch vụ HTTP trên máy chủ.',
 'R3':'Agent có vấn đề; cần phân biệt với mất kết nối toàn máy.',
 'R4':'Dấu hiệu phù hợp lỗi DNS; cần kiểm resolver và đường DNS.',
 'R5':'Nghi ngờ lọc lưu lượng hoặc đường truy cập, không quy ngay Nginx dừng.',
 'R6':'Dấu hiệu CPU cao kéo dài; cần kiểm tiến trình và thời gian đáp ứng.',
 'R7':'Ưu tiên điều tra gateway; sự kiện gốc vẫn được giữ.',
 'R8':'Phát hiện mật độ cảnh báo cao; chưa chứng minh mọi cảnh báo cùng nguyên nhân.'}


def state(value,labels):
    return labels[value]+' ('+str(value)+')' if value in labels else 'Chưa đủ dữ liệu'


def number(value,unit=''):
    return f'{value:.1f}{unit}' if type(value) in (int,float) else 'Chưa đủ dữ liệu'


def measurements(result,case):
    node='cli01' if case=='R4' else 'srv01'
    item=next(r for r in result['latest_diagnostics'] if r['node']==node)
    facts=item['assessment']['facts'];get=facts.get
    profile=item['observation'].get('profile',{})
    lines=['Đối tượng: '+node.upper()+' | IP dịch vụ: '+str(profile.get('target_ip','chưa xác định'))]
    if case in {'R1','R2','R3','R5'}:
        lines+=['ICMP/Ping: '+state(get('target_ping'),PING)]
    if case in {'R1','R2','R5'}:
        lines+=['TCP cổng 80 từ MON01: '+state(get('target_tcp80'),TCP)]
    if case in {'R2','R3','R5'}:
        code=get('http_status_code')
        lines+=['HTTP tại máy chủ: '+(str(code) if type(code) is int else 'Chưa nhận được mã HTTP')]
        service='local_agent_state' if case=='R3' else 'local_service_state'
        lines+=[('Zabbix Agent: ' if case=='R3' else 'Nginx: ')+state(get(service),SERVICE)]
    if case=='R1':lines+=['Máy đối chứng: '+state(get('control_ping'),PING)]
    if case=='R3':lines+=['TCP cổng Agent 10050: '+state(get('agent_tcp'),TCP)]
    if case=='R4':
        lines+=['Máy quan sát DNS: '+str(get('dns_observer') or 'chưa xác định').upper(),
                'Kết quả DNS: '+state(get('dns_status'),DNS),
                'Kết nối IP đối chứng: '+state(get('dns_control'),PING)]
    if case=='R6':
        lines+=['CPU trung bình: '+number(get('cpu_mean'),'%')+' | Ngưỡng: '+number(get('cpu_high_percent'),'%'),
                'Độ phủ lịch sử: '+number(get('cpu_span'),' giây'),
                'Lịch sử hợp lệ: '+('Có' if get('cpu_samples_valid') is True else 'Chưa xác nhận'),
                'Load: '+number(get('cpu_load'))+' | Số CPU: '+number(get('cpu_count')),
                'Dữ liệu load/số CPU hợp lệ: '+('Có' if get('cpu_support_valid') is True else 'Chưa xác nhận')]
    if case=='R7':
        routing=result.get('node_states',{}).get('cli01',{}).get('evidence',{}).get('routing',{})
        forwarding=routing.get('forwarding_enabled')
        lines+=['Gateway CLI01 chuyển tiếp: '+('Bật (1)' if forwarding is True else 'Tắt (0)' if forwarding is False else 'Chưa đủ dữ liệu'),
                'Trạng thái nút cha: '+state(get('parent_status'),{'up':'Hoạt động','down':'Không hoạt động đúng'}),
                'Cảnh báo phụ thuộc được gom: '+str(result['correlation']['suppressed_events'])]
    if case=='R8':lines+=['Sự kiện lỗi mới: '+str(get('window_alert_count'))+' | Ngưỡng: 10',
                          'Cửa sổ đếm sự kiện: 30 giây','Can thiệp thử nghiệm: 20 kênh cảnh báo synthetic.']
    return item,lines


def diagnosis_lines(result,case):
    item,lines=measurements(result,case)
    matches=[d['rule_id'].split('_')[0] for d in item['assessment']['diagnoses'] if d['status']=='matched']
    selected=next((d for d in item['assessment']['diagnoses'] if d['rule_id'].startswith(case+'_')),None)
    status='KHỚP' if selected and selected['status']=='matched' else 'CHƯA XÁC NHẬN KHỚP'
    corr=result['correlation']
    return ['BẰNG CHỨNG WORKER THU ĐƯỢC',*lines,'',
            'ĐỐI CHIẾU LUẬT '+case+' — '+status,CHECK[case],
            'Các luật đang khớp trên đối tượng này: '+(', '.join(matches) or 'Chưa có'),'',
            'KẾT LUẬN: '+(MEANING[case] if status=='KHỚP' else 'Chưa đủ căn cứ để kết luận theo luật này.'),
            'TƯƠNG QUAN: '+str(corr['active_problem_events'])+' cảnh báo → '+str(corr['emitted_groups'])+' nhóm sự cố.']


def recovery_lines(result,case):
    _,lines=measurements(result,case)
    return ['BẰNG CHỨNG SAU PHỤC HỒI',*lines,'',
            'Sự cố còn hoạt động: '+str(result['correlation']['active_problem_events']),
            'Tác vụ chẩn đoán đang chờ: '+str(result['counts']['pending_jobs']),
            'Luật '+case+' không còn khớp trong lần đánh giá mới.',
            'Worker đã ghi nhận phục hồi bằng dữ liệu mới.']
