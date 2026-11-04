"""One video, four plain Vietnamese screens. Real worker decisions only."""
import argparse
from datetime import datetime, timezone
import getpass
import json
from pathlib import Path
import shlex
import sys
import time
import uuid
import textwrap
from video_view import diagnosis_lines, recovery_lines

ROOT=Path(__file__).resolve().parents[1]
REMOTE='/home/phat/do-an/system-monitor'
CASES={
 'R1':('MẤT KẾT NỐI TỚI MÁY CHỦ','srv01','Chặn kết nối tới địa chỉ dịch vụ; giữ đường quản trị.', 'Không nhận được phản hồi từ đích; máy đối chứng vẫn hoạt động.'),
 'R2':('DỊCH VỤ WEB NGỪNG HOẠT ĐỘNG','srv01','Dừng dịch vụ Nginx trên máy chủ.', 'Máy chủ còn hoạt động, nhưng dịch vụ web đã dừng.'),
 'R3':('AGENT GIÁM SÁT BỊ DỪNG','srv01','Dừng riêng Zabbix Agent trên máy chủ.', 'Máy và web vẫn hoạt động; riêng Agent thu số liệu bị dừng.'),
 'R4':('KHÔNG PHÂN GIẢI ĐƯỢC TÊN MIỀN','cli01','Chặn truy vấn DNS trên CLI01.', 'Kết nối bằng IP còn tốt, nhưng phân giải tên thất bại.'),
 'R5':('ĐƯỜNG TRUY CẬP WEB BỊ CHẶN','srv01','Chặn cổng web từ máy giám sát; giữ Nginx chạy.', 'Web tại máy chủ vẫn tốt; nghi ngờ đường truy cập hoặc lọc lưu lượng.'),
 'R6':('CPU CAO KÉO DÀI','srv01','Tạo tải CPU có giới hạn; cần khoảng 5–6 phút thu lịch sử.', 'Lịch sử CPU và tải hệ thống phù hợp dấu hiệu CPU cao kéo dài.'),
 'R7':('GATEWAY KHÔNG CHUYỂN TIẾP','cli01','Tắt chức năng chuyển tiếp của gateway CLI01.', 'Gateway không chuyển tiếp; các cảnh báo phụ thuộc được gom về gốc.'),
 'R8':('BÃO CẢNH BÁO','mon01','Bơm 20 tín hiệu cảnh báo thử, không phải 20 máy bị lỗi.', 'Có ít nhất 10 sự kiện lỗi mới trong 30 giây.')}


def panel(case,step,title,lines,pause=False):
    if sys.stdout.isatty():print('\033[2J\033[H',end='')
    print('\n'+'═'*76+'\n  DEMO '+case+' — '+CASES[case][0])
    print('  BƯỚC '+str(step)+'/4  |  '+title+'\n'+'═'*76)
    print()
    for line in lines:
        for part in textwrap.wrap(line,72) or ['']:print('  '+part)
    if pause:input()


def snapshot(transport):
    code="import sys,json,subprocess;from pathlib import Path;sys.path.insert(0,"+repr(REMOTE)+");from report import report;r=report(Path("+repr(REMOTE)+"));r['worker_service']=subprocess.run(['systemctl','is-active','do-an-monitor-v3.service'],capture_output=True,text=True).stdout.strip();print(json.dumps(r))"
    return transport.runner('mon01',code)


def row(result,node='srv01'):
    return next(r for r in result['latest_diagnostics'] if r['node']==node)


def healthy(result):
    c=result['correlation'];srv=row(result)
    f=srv['assessment']['feature_vector']['features']
    return (result.get('worker_service')=='active' and c['active_problem_events']==0 and result['counts']['pending_jobs']==0 and
            f['http_status_code']==200 and f['parent_status']=='up' and
            all(s['status']=='up' and 0<=result['report_clock']-s['observed_at']<=60 for s in result['node_states'].values()) and
            all(0<=result['report_clock']-r['observation']['decision_time']<=60 and all(s['status']=='ok' for s in r['observation']['sources'].values()) for r in result['latest_diagnostics']))



def baseline_reason(result):
    problems = []
    if result.get('worker_service') != 'active':problems.append('Worker chưa chạy.')
    if result['counts']['pending_jobs']:problems.append('Còn '+str(result['counts']['pending_jobs'])+' tác vụ đang xử lý.')
    if result['correlation']['active_problem_events']:
        problems.append('Còn '+str(result['correlation']['active_problem_events'])+' cảnh báo chưa phục hồi.')
        events={(e['source'],e['event_id']):e for e in result.get('events',[])}
        for group in result['correlation']['groups']:
            for member in group['members']:
                event=events.get((member['source'],member['event_id']),{})
                label=event.get('name') or ('Cảnh báo kết nối '+member['node']+' chưa ghi nhận phục hồi')
                problems.append(label)
    f=row(result)['assessment']['feature_vector']['features']
    if f['http_status_code']!=200:problems.append('Web chưa trả HTTP 200.')
    if f['parent_status']!='up':problems.append('Gateway chưa được xác nhận hoạt động.')
    for r in result['latest_diagnostics']:
        if not 0<=result['report_clock']-r['observation']['decision_time']<=60:problems.append('Bằng chứng '+r['node']+' đã cũ.')
        for name,s in r['observation']['sources'].items():
            if s['status']!='ok':problems.append('Nguồn đo '+r['node']+'/'+name+' chưa hoạt động.')
    if not problems:problems.append('Trạng thái node chưa đủ mới hoặc chưa được xác nhận up.')
    return ' '.join(problems)


def detected(result,case,since):
    node='cli01' if case=='R4' else 'srv01'
    r=row(result,node)
    if r['observation']['decision_time']<since:return False
    if case=='R7' and result['correlation']['suppressed_events']<1:return False
    return any(d['rule_id'].startswith(case+'_') and d['status']=='matched' for d in r['assessment']['diagnoses'])




def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES)
    args=parser.parse_args()
    if not args.case:
        print('CHỌN MỘT VIDEO RIÊNG:')
        for key,value in CASES.items():print(' ',key,'—',value[0])
        args.case=input('\nNhập mã video (Enter = R5): ').strip().upper() or 'R5'
        if args.case not in CASES:parser.error('Chọn mã R1 đến R8')
    case=args.case
    sys.path.insert(0,str(ROOT/'tools'))
    from lab_settings import settings,vm_states
    config=settings(ROOT)
    for path in config.get('dependency_paths',[]):sys.path.insert(0,path)
    from lab_transport import LabTransport
    from lab_session import lab_session
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from monitoring.platform import ready,unchanged
    from video_faults import HOST
    if not config.get('coordination_root'):raise ValueError('Cần cấu hình tools/lab.local.json')
    if any(v!='running' for v in vm_states().values()):raise ValueError('Cần bật đủ ba VM')
    source=(Path(__file__).with_name('video_faults.py')).read_text(encoding='utf-8')
    token=uuid.uuid4().hex[:12]
    folder=ROOT/'evidence/system-v3/video-demos'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')/token
    folder.mkdir(parents=True)
    def save(name,data):(folder/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    def command(action):
        code=source.replace("if __name__=='__main__':", "if False:")+"\nprint(json.dumps(control("+repr(action)+","+repr(case)+","+repr(token)+",source="+repr(source)+")))"
        return json.loads(transport.sudo(HOST[case],'python3 -c '+shlex.quote(code)))
    with lab_session(config['coordination_root']):
        print('Đăng nhập trước khi quay. Mật khẩu không được lưu.')
        transport=LabTransport(getpass.getpass('Mật khẩu SSH lab: '));armed=False;stage=1
        try:
            platform=transport.platform_health();save('platform-before',platform)
            if not ready(platform):raise RuntimeError('Nền VM chưa ổn định; chưa tạo lỗi.')
            before=snapshot(transport);save('before',before)
            if not healthy(before):raise RuntimeError('Chưa tạo lỗi. '+baseline_reason(before))
            panel(case,1,'HỆ THỐNG ĐANG BÌNH THƯỜNG',[
                'Máy chủ web hoạt động — HTTP 200.','Gateway hoạt động; không còn sự cố của lần trước.',
                'Tình huống thử nghiệm: '+CASES[case][2]],pause=True)
            if not healthy(snapshot(transport)) or not ready(transport.platform_health()):
                raise RuntimeError('Baseline đã thay đổi khi chờ; chưa tạo lỗi.')
            stage=2;armed=True;fault=command('arm');save('fault',fault)
            panel(case,2,'ĐÃ TẠO LỖI — CHỜ WORKER PHÁT HIỆN',[
                CASES[case][2],'Worker đang tự thu bằng chứng và đối chiếu luật.',
                'Đang kiểm tra trạng thái kết nối và dịch vụ.'])
            deadline=time.monotonic()+(400 if case=='R6' else 100)
            result=None
            while time.monotonic()<deadline:
                current=snapshot(transport)
                if detected(current,case,fault['fault_at']):result=current;break
                time.sleep(3)
            if result is None:raise TimeoutError('Chưa ghi nhận đúng luật trong thời gian chờ; không tính demo đạt.')
            save('detected',result);stage=3
            stamp=datetime.fromtimestamp(row(result,'cli01' if case=='R4' else 'srv01')['observation']['decision_time']).strftime('%H:%M:%S')
            panel(case,3,'ĐÃ PHÁT HIỆN — LUẬT '+case,
                  ['Thời điểm ghi nhận: '+stamp,'',*diagnosis_lines(result,case)],pause=True)
            stage=4;save('recovery',command('recover'));armed=False
            panel(case,4,'ĐANG XÁC NHẬN PHỤC HỒI',['Đã gửi lệnh phục hồi.','Chờ dữ liệu mới từ Zabbix và worker…'])
            deadline=time.monotonic()+(360 if case=='R6' else 150)
            while time.monotonic()<deadline:
                current=snapshot(transport)
                if healthy(current) and not detected(current,case,fault['fault_at']):break
                time.sleep(3)
            else:raise TimeoutError('Đã yêu cầu phục hồi nhưng chưa xác minh baseline; xem hồ sơ, chưa tính hoàn tất.')
            save('after',current)
            after=transport.platform_health();save('platform-after',after)
            if not unchanged(platform,after):raise RuntimeError('VM thay đổi/treo trong lượt thử; không chứng nhận demo đạt.')
            save('result',{'status':'VIDEO_DEMO_VERIFIED','case':case,'token':token})
            panel(case,4,'ĐÃ PHỤC HỒI — HỆ THỐNG BÌNH THƯỜNG',
                  recovery_lines(current,case),pause=True)
        except (Exception,KeyboardInterrupt) as error:
            save('failure',{'error_type':type(error).__name__})
            panel(case,stage,'LƯỢT DEMO CHƯA HOÀN TẤT',[
                str(error) if isinstance(error,(RuntimeError,TimeoutError)) else type(error).__name__,
                'Kết quả: chưa xác minh hoàn tất tình huống thử nghiệm.'])
            raise
        finally:
            if armed:
                try:save('cleanup',command('recover'))
                except Exception:print('Chưa xác minh được phục hồi qua SSH; timer trong VM vẫn là dự phòng.')
            transport.close()


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:raise SystemExit(130)
    except Exception as error:
        print('Demo dừng:',type(error).__name__)
        raise SystemExit(2)
