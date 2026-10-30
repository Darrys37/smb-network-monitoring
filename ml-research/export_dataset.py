"""Export last window per reviewed pilot run; not a training/evaluation command."""
import argparse,csv,json
from pathlib import Path
from mlv2.core import read,save_new
from mlv2.features import FEATURES,extract
from mlv2.quality import audit


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    summary=audit(args.data_root,args.output)
    rows=[]
    for registration in sorted((args.data_root/'registry').glob('pilot-v2-*/*/registration.json')):
        reviews=list(registration.parent.glob('review-*.json'))
        if len(reviews)!=1:continue
        review=read(reviews[0])
        if review['validity']!='valid' or len(review['labels'])!=1:continue
        session,run=review['session_id'],review['run_id']
        if any(i['run_id']==run and i['issue']=='invalid_review_provenance' for i in summary['issues']):continue
        windows=[read(x) for x in (args.data_root/'observations'/session/run).glob('*.json')]
        if not windows:continue
        selected=max(windows,key=lambda w:w['decision_time'])
        rows.append({'session_id':session,'run_id':run,'window_id':selected['window_id'],
                     'label':review['labels'][0],**extract(selected)})
    if rows:
        with (args.output/'pilot_dataset.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (args.output/'feature_contract.json').write_text(json.dumps({'features':FEATURES,
        'metadata':['session_id','run_id','window_id','label'],'selection':'latest decision_time per valid reviewed run',
        'training_permitted':False,'note':'Pilot audit export; final evaluation requires completed independent sessions.'},indent=2),encoding='utf-8')
    print(json.dumps({'exported_runs':len(rows),'quality':summary},ensure_ascii=True))


if __name__=='__main__':main()
