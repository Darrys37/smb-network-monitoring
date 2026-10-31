"""Render data-derived figures and Vietnamese defense notes after sealed evaluation."""
import argparse,hashlib,json,math,sqlite3
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from train_v2 import metrics

NAMES={'majority':'Majority','cart_numeric':'CART numeric','cart_discrete':'CART discrete',
       'fp_classifier':'FP classifier','cart_no_quality':'CART no quality','cart_missingness':'Availability only','cart_common':'No local HTTP/DNS'}
SHORT={'agent_stopped':'Agent stopped','cpu_stress':'CPU stress','dns_egress_blocked':'DNS blocked',
       'healthy':'Healthy','interface_down':'Interface down','nginx_stopped':'Nginx stopped',
       'remote_http_filtered':'HTTP filtered','ABSTAIN':'Abstain'}


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(result):
    summary=read(result/'metrics.json');manifest=read(result/'manifest.json')
    predictions=pd.read_csv(result/'locked_test_predictions.csv',encoding='utf-8-sig')
    comparison=pd.read_csv(result/'family_comparison.csv',encoding='utf-8-sig')
    for method,expected in summary.items():
        actual=metrics(predictions.label.tolist(),predictions[method].tolist())
        for key in ['correct','runs','coverage','macro_f1','accuracy_all_runs']:
            if not math.isclose(actual[key],expected[key],abs_tol=1e-12):raise ValueError('Metrics/CSV mismatch: '+method+'/'+key)
    if not read(result/'live_shadow_equivalence.json')['all_equal']:raise ValueError('Live shadow equivalence did not pass')
    out=result/('presentation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    methods=list(summary);x=np.arange(len(methods));width=.25
    fig,ax=plt.subplots(figsize=(12,5))
    for offset,key,title,color in [(-1,'accuracy_all_runs','Accuracy','#3465a4'),(0,'macro_f1','Macro-F1','#db8521'),(1,'coverage','Coverage','#31967a')]:
        ax.bar(x+offset*width,[summary[name][key] for name in methods],width,label=title,color=color)
    ax.set_xticks(x,[NAMES[name].replace(' ','\n',1) for name in methods]);ax.set_ylim(0,1.12)
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(ncol=3,frameon=False)
    ax.set_title(f"Locked test: {len(predictions)} runs, two same-host blocks");ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(out/'model_comparison.png',dpi=180);fig.savefig(out/'model_comparison.svg');plt.close(fig)
    mains=['cart_numeric','cart_discrete','fp_classifier'];fig,axes=plt.subplots(1,3,figsize=(17,6))
    vmax=max(max(map(max,summary[name]['confusion_matrix'])) for name in mains)
    for ax,name in zip(axes,mains):
        value=summary[name];matrix=np.array(value['confusion_matrix']);labels=[SHORT[label] for label in value['confusion_labels']]
        ax.imshow(matrix,cmap='Blues',vmin=0,vmax=max(1,vmax))
        ax.set_xticks(range(len(labels)),labels,rotation=60,ha='right');ax.set_yticks(range(len(labels)),labels)
        for (row,col),count in np.ndenumerate(matrix):
            if count:ax.text(col,row,str(count),ha='center',va='center',color='white' if count>vmax*.6 else '#17314d')
        ax.set_title(NAMES[name]);ax.set_xlabel('Prediction')
    axes[0].set_ylabel('Ground truth');fig.suptitle('Held-out confusion matrices (counts)')
    fig.savefig(out/'confusion_matrices.png',dpi=180);fig.savefig(out/'confusion_matrices.svg');plt.close(fig)
    families=sorted(set(comparison.diagnostic_family));fig,ax=plt.subplots(figsize=(12,5));width=.19
    for index,(method,color) in enumerate([('expert','#787878'),('cart_numeric','#3465a4'),('cart_discrete','#db8521'),('fp_classifier','#31967a')]):
        values=comparison[comparison.method==method].set_index('diagnostic_family').loc[families]
        ax.bar(np.arange(len(families))+(index-1.5)*width,values.f1_including_abstention,width,
               label='Expert' if method=='expert' else NAMES[method],color=color)
    ax.set_xticks(range(len(families)),[SHORT[name].replace(' ','\n',1) for name in families]);ax.set_ylim(0,1.12)
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(ncol=4,frameon=False);ax.set_title('Six independent diagnostic-family questions: F1, abstention included')
    fig.savefig(out/'family_comparison.png',dpi=180);fig.savefig(out/'family_comparison.svg');plt.close(fig)
    n=len(predictions);train=manifest['train_rows'];timing=read(result/'same_input_latency.json')
    test_root=Path(manifest['test_sources'][0]['path']).parents[3]
    attempts=[read(path) for path in test_root.glob('trial-logs/test-v2-*/*/RESULT.json')]
    reasons=Counter(row.get('error_type') or 'independent_timing_or_validity_check' for row in attempts if not row['valid'])
    lines=['# Báo cáo nghiệm thu phần học máy trên lab VM','',
        f'Đã đánh giá trên **{n} lượt test mới**, sau khi khóa train gồm **{train} lượt pilot**. Hai block test cùng SRV01; đây là đánh giá giữ riêng theo thời gian trong lab, chưa phải chuyển host.',
        '', '| Phương pháp | Đúng / tổng | Macro-F1 | Coverage |','|---|---:|---:|---:|']
    for method,value in summary.items():lines.append(f"| {NAMES[method]} | {value['correct']}/{value['runs']} | {value['macro_f1']:.3f} | {value['coverage']:.1%} |")
    lines+=['','![So sánh](model_comparison.png)','','![Confusion matrices](confusion_matrices.png)',
        '', '## Đối chứng với luật chuyên gia','',
        'Expert trả sáu nhận định độc lập. Insufficient được giữ riêng; không ép thành healthy. Hình dưới so cùng câu hỏi từng nhóm, không trộn với accuracy phân loại bảy lớp.',
        '', '![Đối chứng từng nhóm](family_comparison.png)',
        '', '## Độ trễ cùng đầu vào','',
        'Warm offline, raw observation nạp sẵn; gồm dựng feature và inference. Không gồm API/SSH hoặc chờ Zabbix phát hiện.',
        '', '| Phương pháp | Median ms | P95 ms | Số lần đo |','|---|---:|---:|---:|']
    for method,value in timing['methods'].items():lines.append(f"| {NAMES.get(method,'Expert')} | {value['median_ms']:.3f} | {value['p95_ms']:.3f} | {value['calls']} |")
    healthy=predictions[predictions.label=='healthy']
    lines+=['','## Bình thường, thiếu dữ liệu và giới hạn','',f'Có {len(healthy)} lượt healthy test. Báo số đếm báo nhầm/từ chối theo từng phương pháp, không suy FPR production từ số ít lượt này.']
    lines+=['',f"Thu thập có {len(attempts)} attempt đã chốt: {sum(row['valid'] for row in attempts)} valid, {sum(not row['valid'] for row in attempts)} uncertain. Điểm phân loại ở trên có điều kiện trên các lượt đạt protocol; đây không phải tỷ lệ thành công của mọi attempt.",
            '', 'Lý do uncertain được giữ nguyên: '+json.dumps(dict(reasons),ensure_ascii=False)+'.',
            '', 'Gate platform trước/sau trial ghi nhận kernel stall/reboot bất ngờ và chốt uncertain theo bằng chứng độc lập, không theo điểm classifier. Gate này có tính bảo thủ; báo riêng tỷ lệ attempt đạt yêu cầu thay vì loại ca lỗi mà không nêu.']
    for method in mains:
        wrong=sum(value not in ['healthy','ABSTAIN'] for value in healthy[method]);abstain=sum(healthy[method]=='ABSTAIN')
        lines.append(f'- {NAMES[method]}: {wrong}/{len(healthy)} dự đoán fault trên healthy; {abstain}/{len(healthy)} từ chối.')
    lines+=['',f"Availability-only đúng {summary['cart_missingness']['correct']}/{n}; majority đúng {summary['majority']['correct']}/{n}. Đối chứng này cho thấy mức tín hiệu chỉ do việc có/thiếu dữ liệu; không được bỏ nó khỏi báo cáo.",
        '', 'Dữ liệu được cân bằng theo lớp và can thiệp đã biết. Confidence/lift và tỷ lệ lớp tại lá là thống kê train, không phải xác suất nguyên nhân đúng đã hiệu chỉnh. CPU cao ngoài lab có thể là công việc hợp lệ.',
        '', 'Mô hình chỉ nhận whitelist feature; run ID, timestamp, tên lỗi, output expert và recovery không phải predictor. Collector gọi theo lịch độc lập nhãn. Mỗi valid run chỉ dùng cửa sổ cuối.',
        '', 'Chưa có bằng chứng chuyển VM sang PC thật, nhiều lỗi đồng thời, root-cause topology hoặc suppression. Hai block không đủ để tính CI theo phiên đáng tin cậy. Không có yêu cầu ML phải thắng expert.',
        '', 'Pilot phát triển có các đợt lỗi ảo hóa/RCU được lưu log. Những lượt đầu dùng kiểm tra can thiệp và timing trước khi có bộ đếm kernel; test mới thêm kiểm tra platform ổn định. Vì vậy pilot là dữ liệu phát triển có hạn chế, không được mô tả như một bộ test sạch đã giấu kín.',
        '', '## Câu trả lời ngắn khi bảo vệ','',
        f'“Em dùng {train} lượt pilot làm tập phát triển, khóa cấu hình và thu riêng {n} lượt test mới. Cây CART phân loại trực tiếp; FP-Growth tìm tập mục rồi module của em lọc và xếp luật feature → nhãn. Em so với chuyên gia trên cùng bằng chứng, giữ trường hợp thiếu thông tin. Luật SQLite được kiểm tra tương đương với model và shadow lúc fault; em chưa tự kích hoạt luật vào engine vận hành.”',
        '', 'Khi nói về kết quả, đọc đúng số đếm trong bảng; không dùng confidence train để thay cho độ chính xác test hoặc chứng minh quan hệ nhân quả.','']
    (out/'BAO_CAO_NGHIEM_THU.md').write_text('\n'.join(lines),encoding='utf-8')
    db=sqlite3.connect((result/'candidate_rules.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    rule_lines=['# Luật học được — chỉ thống kê train','',
        '| Thuật toán | Rule ID | Nhãn lab | IF | Số lượt train hỗ trợ | Thống kê train |',
        '|---|---|---|---|---:|---|']
    try:
        for rid,algo,conditions,label,count,stats in db.execute('SELECT rule_id,algorithm,conditions_json,label,training_runs,statistics_json FROM candidates ORDER BY algorithm,rule_id'):
            conditions=json.loads(conditions);stats=json.loads(stats)
            if algo=='CART':
                expression=' AND '.join(c['feature']+(' = ' if c['op']=='eq' else ' != ')+str(c['value']) for c in conditions) or 'TRUE'
                statistic=f"leaf class fraction={stats['leaf_class_fraction']:.1%}"
            else:
                expression=' AND '.join(conditions)
                statistic=f"support={stats['support']:.3f}; association confidence={stats['confidence']:.1%}; lift={stats['lift']:.3f}"
            rule_lines.append(f'| {algo} | {rid} | {label} | `{expression}` | {count} | {statistic} |')
    finally:db.close()
    rule_lines+=['','Các phần trăm trên không phải xác suất chẩn đoán đã hiệu chỉnh. Kết quả test nằm trong báo cáo chính; nhãn mô tả kịch bản lab, không chứng minh nguyên nhân vật lý duy nhất.','']
    (out/'LUAT_HOC_DUOC.md').write_text('\n'.join(rule_lines),encoding='utf-8')
    inputs=[result/name for name in ['manifest.json','metrics.json','locked_test_predictions.csv','family_comparison.csv','same_input_latency.json','candidate_rules.sqlite','research_registry.sqlite','live_shadow_equivalence.json']]
    (out/'FIGURES.json').write_text(json.dumps({'input_sha256':{path.name:sha(path) for path in inputs},
        'output_sha256':{path.name:sha(path) for path in out.iterdir() if path.is_file()}},indent=2),encoding='utf-8')
    (result/'presentation-latest.json').write_text(json.dumps({'output_dir':str(out)},indent=2),encoding='utf-8')
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--result',type=Path,required=True)
    print(json.dumps({'presentation_dir':str(render(parser.parse_args().result))},ensure_ascii=True))
