"""Day 30: reproducible descriptive tables/figures from accepted day 29 data."""
import csv, hashlib, json, statistics, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

project=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
source=project/'evidence/week5/day29-20261017'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((source/'checksums.json').read_text())
for rel,digest in manifest.items(): assert sha(project/rel)==digest,rel
rows=list(csv.DictReader((source/'clean-runs.csv').open(encoding='utf-8-sig')))
oldsummary={r['scenario']:r for r in csv.DictReader((source/'scenario-summary.csv').open(encoding='utf-8-sig'))}
assert len(rows)==18 and len({r['run_id'] for r in rows})==18
scenarios=[f'R{i}' for i in range(1,7)]
labels=['Mất kết nối lab','Dừng Nginx','Dừng Agent 2','Chặn DNS','Lọc TCP80','CPU cao']
def writecsv(name,records):
    with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
stats=[]; outcomes=[]; status_rows=[]; points=[]
for s in scenarios:
    group=[r for r in rows if r['scenario']==s]; assert len(group)==3
    result={'scenario':s,'n_valid':len(group)}
    for field in ['dt_lower_seconds','dt_upper_seconds','cli_elapsed_seconds','rr_lower_seconds','rr_upper_seconds']:
        values=[float(r[field]) for r in group]
        for name,fn in [('min',min),('median',statistics.median),('max',max)]:
            key=field+'_'+name;result[key]=fn(values);assert abs(result[key]-float(oldsummary[s][key]))<1e-9
    stats.append(result)
    for r in group:
        assert int(r['valid_fault'])==1
        points.append({k:r[k] for k in ['run_id','scenario','problem_event_id','dt_lower_seconds','dt_upper_seconds','dt_quantized_lower_seconds','dt_quantized_upper_seconds','cli_elapsed_seconds','target_status','target_success']})
    result={'scenario':s,'n_valid':3,'matched_target':sum(int(r['target_success']) for r in group),'not_matched_target':sum(r['target_status']=='not_matched' for r in group),'insufficient_target':sum(r['target_status']=='insufficient_evidence' for r in group),'no_detection':sum(int(r['detected'])==0 for r in group),'engine_errors':sum(int(r['engine_exit_code'])!=0 for r in group)}
    assert sum(result[k] for k in ['matched_target','not_matched_target','insufficient_target','no_detection','engine_errors'])==3
    result['target_success_rate']=result['matched_target']/3;outcomes.append(result)
    counters={}
    for r in group:
        raw=json.loads((project/r['raw_folder']/'incident.json').read_text())
        for d in raw['diagnoses']:
            rule=d['rule_id'].split('_')[0]; counters.setdefault(rule,Counter())[d['status']]+=1
    for rule,c in sorted(counters.items()):
        status_rows.append(dict(scenario=s,rule=rule,matched=c['matched'],not_matched=c['not_matched'],insufficient_evidence=c['insufficient_evidence']))
assert sum(r['matched']+r['not_matched']+r['insufficient_evidence'] for r in status_rows)==108
writecsv('timing-summary.csv',stats);writecsv('diagnosis-outcomes.csv',outcomes);writecsv('rule-status-counts.csv',status_rows);writecsv('plotted-points.csv',points)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
figurefiles=[]
def save(fig,name):
    for ext in ['png','svg','pdf']:
        p=out/(name+'.'+ext);fig.savefig(p,dpi=190);figurefiles.append(p.name)
    plt.close(fig)
fig,ax=plt.subplots(figsize=(11,6.2))
for i,s in enumerate(scenarios):
    group=[r for r in rows if r['scenario']==s]
    for j,r in enumerate(group):
        x=i+(j-1)*.13;lo=float(r['dt_lower_seconds']);hi=float(r['dt_upper_seconds'])
        ax.vlines(x,lo-1,hi+1,color='#4684A3',lw=2,zorder=2)
        ax.scatter(x,lo,color='#16678D',s=40,zorder=3)
        ax.annotate(r['run_id'].split('-',1)[1],(x,hi+1),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8,color='#365667')
    ax.hlines(stats[i]['dt_lower_seconds_median'],i-.26,i+.26,color='#D26722',lw=2.5,zorder=4)
ax.set(xticks=range(6),xticklabels=[f'{s}\n{label}' for s,label in zip(scenarios,labels)],ylabel='Thời gian từ gây lỗi đến problem (giây)',ylim=(-8,430),title='Thời gian Zabbix phát hiện theo kịch bản')
ax.grid(axis='y',alpha=.18)
ax.legend(handles=[Line2D([],[],marker='o',linestyle='',color='#16678D',label='Từng lượt: cận dưới DT'),Line2D([],[],color='#D26722',lw=2.5,label='Median cận dưới'),Line2D([],[],color='#4684A3',lw=2,label='Khoảng DT mở rộng ±1 giây')],loc='upper left',frameon=False,fontsize=9)
fig.text(.5,.025,'n=3 mỗi kịch bản; nhãn 01/02/03 là lượt thử, R5 dùng 03-retry1. Khoảng không phải confidence interval.\nCận DT lấy từ timestamp trước/sau fault; ±1 giây chỉ là lượng tử hóa, chưa gồm sai lệch clock giữa VM.',ha='center',fontsize=9)
fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.89);save(fig,'detection-time')
fig,ax=plt.subplots(figsize=(11,5.6))
for i,s in enumerate(scenarios):
    group=[float(r['cli_elapsed_seconds']) for r in rows if r['scenario']==s]
    ax.scatter([i-.13,i,i+.13],group,color='#16678D',s=45,zorder=3)
    ax.hlines(statistics.median(group),i-.26,i+.26,color='#D26722',lw=2.5)
ax.set(xticks=range(6),xticklabels=scenarios,ylabel='Thời gian toàn bộ CLI (giây)',ylim=(0,7.6),title='Thời gian chạy chẩn đoán sau khi có event')
ax.grid(axis='y',alpha=.18)
ax.legend(handles=[Line2D([],[],marker='o',linestyle='',color='#16678D',label='Từng lượt'),Line2D([],[],color='#D26722',lw=2.5,label='Median')],frameon=False)
fig.text(.5,.04,'CLI gồm API, thu thập evidence, áp dụng luật và ghi SQLite; không phải thời gian suy luận thuần.\nThời gian chờ event hoặc chuyển probe trước khi gọi CLI không nằm trong chỉ số này.',ha='center',fontsize=9)
fig.subplots_adjust(left=.1,right=.98,bottom=.19,top=.88);save(fig,'diagnosis-cli-time')
fig,ax=plt.subplots(figsize=(11,5.6));bottom=[0]*6
for key,color,label in [('matched_target','#267B69','Khớp mục tiêu, hồ sơ đạt'),('not_matched_target','#BF534A','Không khớp mục tiêu'),('insufficient_target','#D6A145','Thiếu bằng chứng mục tiêu'),('no_detection','#767F8A','Không phát hiện'),('engine_errors','#855CA6','Lỗi engine')]:
    values=[r[key] for r in outcomes];ax.bar(scenarios,values,bottom=bottom,color=color,label=label,width=.55);bottom=[a+b for a,b in zip(bottom,values)]
for i,r in enumerate(outcomes):ax.text(i,3.10,f'{r["matched_target"]}/3',ha='center',fontweight='bold')
ax.set(ylim=(0,3.6),yticks=[0,1,2,3],ylabel='Số fault hợp lệ',title='Kết quả chẩn đoán của luật mục tiêu')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.12),ncol=3,frameon=False,fontsize=9)
fig.text(.5,.025,'18 fault hợp lệ; R5-03 hủy trước fault được giữ riêng. Các nhóm còn lại đều bằng 0 trong bộ thử này.\n18/18 không phải accuracy tổng quát: chưa có mẫu âm; các luật phụ được thống kê riêng trong CSV.',ha='center',fontsize=9)
fig.subplots_adjust(left=.1,right=.98,bottom=.28,top=.88);save(fig,'diagnosis-outcomes')

rawlink=lambda rid,file:f'../../week4/official-runs/{rid}/{file}'
lines=['# Tuần 5 — ngày 30: bảng, biểu đồ và phát hiện thực nghiệm','','Ngày 17/10/2026 (UTC+7). Hoàn thành phạm vi ngày 30 theo roadmap: bảng kết quả, biểu đồ detection theo kịch bản, kết quả chẩn đoán và các phát hiện có bằng chứng. Đầu vào là dữ liệu đã nghiệm thu ngày 29; không gây thêm lỗi hoặc thay đổi luật/trigger.','','## Dữ liệu và phương pháp','','Đối chiếu toàn bộ 19 tệp trong manifest ngày 29 trước phân tích. Tính lại 90 số thống kê (6 kịch bản × 5 chỉ số × 3 phép min/median/max), khớp bảng ngày 29 với sai số kiểm tra < 1e-9. 18 fault hợp lệ, mỗi nhóm n=3; R5-03 hủy trước fault không vào mẫu số. 18 CLI mã 0, 18 incident closed.','','DT là khoảng [problem − fault_after, problem − fault_before]; bảng báo median hai cận và miền từ cận dưới nhỏ nhất đến cận trên lớn nhất. Miền này không phải confidence interval. Hình DT hiển thị từng lượt, median cận dưới và khoảng đo mở rộng ±1 giây do độ phân giải timestamp. Sai lệch clock chưa đo được. CLI đo toàn bộ lần gọi chương trình, không phải suy luận thuần.','','## Bảng 30.1 — thời gian và kết quả','','| Kịch bản | n | DT median hai cận (s) | Miền DT (s) | CLI median [min–max] (s) | Mục tiêu khớp |','|---|---:|---:|---:|---:|---:|']
for t,o in zip(stats,outcomes):
    lines.append(f'| {t["scenario"]} | 3 | {t["dt_lower_seconds_median"]:.0f}–{t["dt_upper_seconds_median"]:.0f} | {t["dt_lower_seconds_min"]:.0f}–{t["dt_upper_seconds_max"]:.0f} | {t["cli_elapsed_seconds_median"]:.3f} [{t["cli_elapsed_seconds_min"]:.3f}–{t["cli_elapsed_seconds_max"]:.3f}] | {o["matched_target"]}/3 |')
lines+=['','[Bảng thời gian đầy đủ](timing-summary.csv) · [Kết quả chẩn đoán](diagnosis-outcomes.csv) · [Từng điểm trên hình](plotted-points.csv) · [108 đầu ra luật](rule-status-counts.csv)','','## Hình 30.1 — thời gian phát hiện','','![Thời gian phát hiện](detection-time.png)','','## Hình 30.2 — thời gian CLI chẩn đoán','','![Thời gian CLI](diagnosis-cli-time.png)','','## Hình 30.3 — kết quả chẩn đoán','','![Kết quả luật mục tiêu](diagnosis-outcomes.png)','','Các nhóm không khớp, thiếu bằng chứng mục tiêu, không phát hiện và lỗi engine đều bằng 0. Đây là kết quả luật mục tiêu, không phải chấm toàn bộ luật phụ thành đúng/sai. 108 đầu ra luật gồm 18 matched, 66 not_matched, 24 insufficient_evidence.','','## Các phát hiện có bằng chứng','','1. **Detection thay đổi rõ giữa các kịch bản.** R6 có median 356 s và miền 316–391 s; R3 có median 269 s và miền 183–295 s; R2 có median 10 s và miền 5–23 s. Các lần thử đều cho R6/R3 chậm hơn R2. Điều này phù hợp với việc các trigger dùng cửa sổ/điều kiện khác nhau, nhưng bộ thử không cô lập từng nguyên nhân hoặc đo chi phí từng bước Zabbix. Không dùng khác biệt này để kết luận engine Python chậm. Bằng chứng: [bảng](timing-summary.csv), [R6-01](../../week4/official-runs/R6-01/run.json), [R3-01](../../week4/official-runs/R3-01/run.json), [R2-01](../../week4/official-runs/R2-01/run.json), [snapshot trigger](../../week4/baseline-20261016T162549Z/effective-config-start.json).','','2. **Detection và thời gian CLI đo hai giai đoạn khác nhau.** R6 có DT median cao nhất (356 s) nhưng CLI median thấp nhất (0,502 s); R1 có DT median 19–20 s nhưng CLI median cao nhất (6,660 s), khoảng 13,27 lần R6. R5 có CLI median 2,590 s. Thứ hạng khác nhau cho thấy không nên lấy detection làm thời gian chạy thuật toán. Chưa có profiling để phân chia chi phí API/probe/SQLite hoặc chứng minh chính xác nguyên nhân chênh lệch. Bằng chứng: [từng điểm](plotted-points.csv), [log R1-01](../../week4/official-runs/R1-01/diagnosis.log), [log R6-01](../../week4/official-runs/R6-01/diagnosis.log).','','3. **Luật mục tiêu khớp cả sáu nhóm, nhưng 18/18 chưa đo accuracy tổng quát.** Mỗi nhóm đạt 3/3 trong đúng fault đã chủ động tạo; R5-03-retry1 thay lượt hủy trước fault, không phải chọn lại sau một chẩn đoán sai. Chưa có tập âm độc lập để tính specificity, false-positive rate hay accuracy có TN. Không biến các kết quả not_matched ngoài mục tiêu thành TN. Bằng chứng: [kết quả theo nhóm](diagnosis-outcomes.csv), [sổ 19 lượt](../day29-20261017/attempts.csv), [adjudication lượt hủy](../../week4/official-runs/R5-03/adjudication.json).','','4. **Thiếu evidence ở luật phụ vẫn cần giữ trong phân tích.** Có 24/108 đầu ra insufficient_evidence, dù cả 18 luật mục tiêu matched. Ví dụ R5-02 có R6 thiếu cửa sổ CPU (239 s so với yêu cầu 240 s). Đây không phải kết quả mục tiêu R5 sai, cũng không chứng minh CPU khỏe. Dữ liệu không đầy đủ phải được giữ đúng trạng thái. Bằng chứng: [bảng 108 đầu ra](rule-status-counts.csv), [hồ sơ R5-02](../../week4/official-runs/R5-02/incident.json).','','## Giới hạn và nghiệm thu','','Các thống kê chỉ mô tả ba lượt mỗi loại trên cùng lab; không có kiểm định suy rộng hoặc khoảng tin cậy. Baseline 30 phút 06 giây không đủ đánh giá cảnh báo dài hạn và không thay mẫu âm cho engine. Ảnh event được chụp hồi cứu sau phục hồi. Không cộng DT và CLI để gọi tổng thời gian xử lý vì còn khoảng chờ/chuyển probe trước CLI.','','Đã tạo ba hình ở PNG, SVG, PDF; CSV cung cấp tất cả điểm và hai cận DT/RR. Nguồn, SHA-256 và phương pháp trong [analysis-validation.json](analysis-validation.json). Mã tái tạo tại [tools/day30_analysis.py](tools/day30_analysis.py). Ngày 31 tiếp theo là hoàn thiện Chương 2; việc nghiệm thu ngày 30 không đóng toàn bộ Chương 3 hoặc toàn bộ tuần 5.','']
(out/'PHAN_TICH_NGAY_30.markdown').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
validation={'result':'PASS','generated_at_utc':datetime.now(timezone.utc).isoformat(),'day29_manifest_files_verified':len(manifest),'input_sha256':{str(p.relative_to(project)).replace('\\','/'):sha(p) for p in [source/'checksums.json',source/'clean-runs.csv',source/'scenario-summary.csv']},'valid_faults':18,'n_per_scenario':3,'statistics_checked_against_day29':90,'plot_point_count_per_timing_chart':18,'target_matched':18,'all_rule_output_count':108,'figure_files':figurefiles,'matplotlib_version':matplotlib.__version__,'general_accuracy':None,'method':'Descriptive raw points and medians, intervals from timestamps; no confidence intervals or healthy-negative accuracy.','visual_review':'pending'}
(out/'analysis-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(validation,ensure_ascii=False,indent=2))
