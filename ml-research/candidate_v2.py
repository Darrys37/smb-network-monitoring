"""Portable candidate rules: data-only JSON/SQLite, no eval or live activation."""
import json
import math
import sqlite3
from pathlib import Path

ABSTAIN = 'ABSTAIN'


def discrete_row(row, categorical, numeric):
    result = {key:row[key] for key in categorical}
    for key in numeric:
        value = row[key]
        if value is None or not math.isfinite(float(value)):
            result[key] = 'unknown'
        elif key == 'cpu_coverage_seconds':
            result[key] = 'sufficient' if value >= 240 else 'short'
        elif key == 'cpu_max_gap_seconds':
            result[key] = 'gap_ok' if value <= 120 else 'gap_large'
        else:
            result[key] = 'high_ge90' if value >= 90 else 'below90'
    return result


def export_cart(model, features):
    encoder = model['encode'].named_transformers_['cat']
    columns = [(key, str(value)) for key, values in zip(features, encoder.categories_) for value in values]
    tree = model['tree'].tree_
    classes = model['tree'].classes_.tolist()
    rules = []

    def visit(node, conditions):
        left, right = int(tree.children_left[node]), int(tree.children_right[node])
        if left == right:
            proportions = tree.value[node][0]
            total = float(sum(proportions))
            best = int(proportions.argmax())
            rules.append({'rule_id':f'cart-leaf-{node}', 'conditions':conditions,
                          'label':classes[best], 'training_runs':int(tree.n_node_samples[node]),
                          'leaf_class_fraction':float(proportions[best]/total),
                          'class_fractions':{label:float(value/total) for label,value in zip(classes,proportions)}})
            return
        feature, category = columns[int(tree.feature[node])]
        # A fitted one-hot binary split always lies strictly between zero and one.
        if not 0 <= float(tree.threshold[node]) < 1:
            raise ValueError('Unsupported CART split; discrete one-hot export only')
        visit(left, conditions+[{'feature':feature,'op':'ne','value':category}])
        visit(right, conditions+[{'feature':feature,'op':'eq','value':category}])

    visit(0, [])
    return rules


def cart_predict(rules, row):
    matched = []
    for rule in rules:
        ok = True
        for condition in rule['conditions']:
            actual = row.get(condition['feature'])
            if condition['op'] == 'eq':
                ok = ok and actual == condition['value']
            elif condition['op'] == 'ne':
                ok = ok and actual != condition['value']
            else:
                raise ValueError('Unsupported condition operator')
        if ok:
            matched.append(rule)
    if len(matched) != 1:
        return {'label':ABSTAIN,'reason':'Candidate leaves are missing or overlap'}
    return {'label':matched[0]['label'],'matched_rule':matched[0],
            'confidence_kind':'training leaf class fraction, not calibrated probability'}


def fp_predict(rules, row):
    tokens = {str(key)+'='+str(value) for key,value in row.items() if value not in ['unknown','not_applicable']}
    matched = [rule for rule in rules if set(rule['conditions']) <= tokens]
    if not matched:
        return {'label':ABSTAIN,'reason':'No association rule matched'}
    rank = lambda rule:(rule['confidence'],rule['support'],-len(rule['conditions']))
    score = max(map(rank, matched))
    winners = [rule for rule in matched if rank(rule)==score]
    if len({rule['label'] for rule in winners}) != 1:
        return {'label':ABSTAIN,'reason':'Equal-ranked association rules conflict'}
    return {'label':winners[0]['label'],'matched_rule':winners[0],
            'confidence_kind':'training association confidence, not calibrated probability'}


def write_database(path, cart, fp, manifest):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    db = sqlite3.connect(path)
    try:
        db.execute('PRAGMA user_version=1')
        db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value_json TEXT NOT NULL)')
        db.execute("CREATE TABLE candidates(rule_id TEXT PRIMARY KEY,algorithm TEXT NOT NULL CHECK(algorithm IN ('CART','FP-Growth')),conditions_json TEXT NOT NULL,label TEXT NOT NULL,training_runs INTEGER NOT NULL,statistics_json TEXT NOT NULL,status TEXT NOT NULL CHECK(status='candidate'))")
        for key,value in manifest.items():
            db.execute('INSERT INTO metadata VALUES(?,?)',(key,json.dumps(value,allow_nan=False)))
        for algorithm,rules in [('CART',cart),('FP-Growth',fp)]:
            for index,rule in enumerate(rules):
                stats = {key:value for key,value in rule.items() if key not in ['conditions','label','rule_id','training_runs']}
                db.execute('INSERT INTO candidates VALUES(?,?,?,?,?,?,?)',
                    (rule.get('rule_id',f'fp-{index:04}'),algorithm,json.dumps(rule['conditions']),
                     rule['label'],rule['training_runs'],json.dumps(stats,allow_nan=False),'candidate'))
        db.commit()
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    finally:
        db.close()


def load_database(path):
    db = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        if db.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Unsupported candidate schema')
        metadata = {key:json.loads(value) for key,value in db.execute('SELECT key,value_json FROM metadata')}
        output = {'CART':[],'FP-Growth':[]}
        for rid,algorithm,conditions,label,runs,stats,status in db.execute('SELECT * FROM candidates ORDER BY rule_id'):
            if status != 'candidate':
                raise ValueError('Candidate-only evaluator')
            output[algorithm].append({'rule_id':rid,'conditions':json.loads(conditions),'label':label,
                                      'training_runs':runs,**json.loads(stats)})
        return metadata,output
    finally:
        db.close()
