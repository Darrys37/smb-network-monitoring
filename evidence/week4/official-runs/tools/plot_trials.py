"""Publication-ready descriptive figures; each point is a real trial, n=3/class."""
import csv
import json
from pathlib import Path
import statistics
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(sys.argv[1])
rows=list(csv.DictReader((root/'all-trials.csv').open(encoding='utf-8')))
assert len(rows)==18
out=root/'figures'
out.mkdir(exist_ok=True)
scenarios=['R1','R2','R3','R4','R5','R6']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,5))
for ax,field,title in zip(axes,['detection_delay_min_seconds','cli_elapsed_seconds'],
                        ['Thời gian Zabbix phát hiện','Thời gian chạy CLI']):
    for i,s in enumerate(scenarios):
        group=[r for r in rows if r['scenario']==s]
        pairs=[(j,float(r[field])) for j,r in enumerate(group) if r[field]]
        ax.scatter([i+(j-1)*.12 for j,v in pairs],[v for j,v in pairs],s=48,color='#1d6fa5',zorder=3)
        values=[v for j,v in pairs]
        if values:
            m=statistics.median(values)
            ax.plot([i-.23,i+.23],[m,m],color='#d05b26',lw=2,zorder=4)
    ax.set_xticks(range(6),scenarios)
    ax.set_ylabel('Giây')
    ax.set_title(title,pad=12)
    ax.set_ylim(bottom=0)
    ax.grid(axis='y',alpha=.2)
fig.suptitle('18 lượt fault hợp lệ · ba lượt mỗi kịch bản',fontsize=15,y=.98)
fig.text(.5,.025,'Chấm: từng lượt; vạch cam: median. Detection dùng cận dưới clock; CSV giữ hai cận và sai số ±1 giây.\nCLI gồm API, thu evidence, luật và lưu SQLite. R5-03 bị hủy trước fault được giữ riêng.',ha='center',fontsize=9)
fig.subplots_adjust(bottom=.20,top=.82,wspace=.25)
for suffix in ('png','svg','pdf'):
    fig.savefig(out/('thoi-gian-phat-hien-va-cli.'+suffix),dpi=220)
plt.close(fig)

fig,ax=plt.subplots(figsize=(9,5))
bottom=[0]*6
styles=[('matched','#287f74','Matched, hồ sơ đạt'),('abstained','#d39a32','Thiếu evidence mục tiêu'),('other','#b75356','Kết quả còn lại')]
for key,color,label in styles:
    counts=[]
    for s in scenarios:
        group=[r for r in rows if r['scenario']==s]
        counts.append(sum((r['target_success_end_to_end']=='True') if key=='matched' else
            (r['target_diagnosis_status']=='insufficient_evidence') if key=='abstained' else
            (r['target_success_end_to_end']!='True' and r['target_diagnosis_status']!='insufficient_evidence') for r in group))
    ax.bar(scenarios,counts,bottom=bottom,color=color,label=label,width=.58)
    bottom=[a+b for a,b in zip(bottom,counts)]
for i,s in enumerate(scenarios):
    good=sum(r['target_success_end_to_end']=='True' for r in rows if r['scenario']==s)
    ax.text(i,3.08,f'{good}/3',ha='center',fontsize=12)
ax.set_ylim(0,3.6);ax.set_yticks([0,1,2,3]);ax.set_ylabel('Số lượt fault hợp lệ')
ax.set_title('Kết quả luật mục tiêu theo kịch bản',pad=15)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.10),ncol=3,frameon=False,fontsize=9)
fig.text(.5,.025,'Mẫu số gồm mọi fault hợp lệ. n=3 mỗi loại; không phải accuracy có true negatives hay độ tin cậy dài hạn.',ha='center',fontsize=8)
fig.subplots_adjust(bottom=.23,top=.85)
for suffix in ('png','svg','pdf'):
    fig.savefig(out/('ket-qua-luat-muc-tieu.'+suffix),dpi=220)
plt.close(fig)
(out/'figure-metadata.json').write_text(json.dumps({'source':'../all-trials.csv','rows':18,'n_per_class':3,
 'method':'Descriptive individual points and median; no confidence interval or healthy-negative accuracy inferred.',
 'matplotlib_version':matplotlib.__version__},indent=2)+'\n')
print(out)
