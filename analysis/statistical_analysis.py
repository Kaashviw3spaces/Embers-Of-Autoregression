"""Optional descriptive paired check; no fabricated p-values or causal conclusions."""
from pathlib import Path
import json
import math
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analysis.scoring import evaluate


def mcnemar_exact(y1,y2):
    if len(y1)!=len(y2):
        raise ValueError('Paired arrays must have equal lengths.')
    b=sum(bool(a) and not bool(c) for a,c in zip(y1,y2))
    c=sum(bool(c) and not bool(a) for a,c in zip(y1,y2))
    n=b+c
    p=min(1.0,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/(2**n)) if n else 1.0
    return {'b':b,'c':c,'p_value':p,'method':'two-sided exact conditional McNemar'}


def analyze_paired_runs(file1,file2):
    runs=[json.loads(Path(f).read_text()) for f in [file1,file2]]
    maps=[]
    for run in runs:
        mapping={}
        for r in run['results']:
            if r.get('api_error',r.get('error')):continue
            key=(r.get('input_words',r.get('input','')),r['gt'])
            mapping[key]=evaluate(r.get('raw_response',''),r['gt'],r.get('finish_reason'),run.get('task_name','acronym1'))['strict_correct']
        maps.append(mapping)
    matched=sorted(maps[0].keys() & maps[1].keys())
    result={'n_identical_inputs_and_answers':len(matched),'correct_first':sum(bool(maps[0][k]) for k in matched),'correct_second':sum(bool(maps[1][k]) for k in matched),'limitation':'Descriptive stored-output comparison. Verify checkpoint, settings and channel provenance before inference.'}
    print(json.dumps(result,indent=2))
    return result


if __name__ == '__main__':
    if len(sys.argv)!=3:
        raise SystemExit('Usage: python3 analysis/statistical_analysis.py FIRST_RUN.json SECOND_RUN.json')
    analyze_paired_runs(*sys.argv[1:])
