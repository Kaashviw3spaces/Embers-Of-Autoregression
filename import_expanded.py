"""Audit the final supplied folder and import new run logs once. No API calls."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import hashlib
import json
from analysis.evidence import redact

ROOT=Path(__file__).resolve().parent


def fingerprint(model,task,item,inp,expected,raw):
    return (str(model).lower(),str(task),str(item),inp,str(expected),raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('/Users/kashvi/Downloads/embers_expanded_campaign_complete'))
    source=parser.parse_args().source.resolve()
    audit=[];runs=[];new=[];primary=Counter();source_inputs=Counter()
    for path in sorted((source/'runs').glob('*.json')):
        data=json.loads(path.read_text())
        rows=data['results'];runs.append((path,data))
        destination=ROOT/'runs'/path.name
        if destination.exists():
            # Compare redacted structures as the existing source may have already
            # been redacted. Refuse to silently replace a changed experiment.
            if redact(json.loads(destination.read_text()))!=redact(data):
                raise ValueError('Changed existing run needs explicit reconciliation: '+path.name)
        else:new.append(path.name)
        for i,r in enumerate(rows):
            inp=r.get('input_words',r.get('input',''));expected=r.get('gt','');raw=r.get('raw_response',r.get('raw',''))
            primary[fingerprint(data['model'],data.get('task_name') or path.name.split('_')[0],r.get('stimulus_id',r.get('id',i)),inp,expected,raw)]+=1
            source_inputs[(inp,str(expected),raw)]+=1
    rows_seen=sum(len(data['results']) for _,data in runs)
    for path in sorted(p for p in source.rglob('*') if p.is_file()):
        relative=path.relative_to(source);raw=path.read_bytes()
        record={'directory':str(relative.parent),'file':str(relative),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'rows':'','role':'','decision':'','check':''}
        if '__pycache__' in path.parts or path.name=='.DS_Store':
            record.update(role='cache',decision='exclude',check='Not experiment evidence')
        elif relative.parts[0]=='runs' and path.suffix=='.json':
            d=json.loads(raw);record['rows']=len(d['results'])
            record.update(role='primary run log',decision='import new' if path.name in new else 'already imported',check='Parsed every record; existing run structures match')
        elif relative.parts[0]=='stimuli':
            prior=ROOT/'stimuli'/path.name
            assert prior.exists()
            assert prior.read_bytes()==raw,'Stimulus changed: '+path.name
            record.update(role='stimulus dataset',decision='existing copy',check='Byte-identical to existing stimuli; not new experiments')
        elif path.suffix=='.jsonl':
            items=[json.loads(line) for line in raw.decode().splitlines() if line.strip()];record['rows']=len(items)
            if path.name=='MASTER_RAW_RESPONSES.jsonl':
                derived=Counter(fingerprint(r['model'],r['task'],r['example_id'],r['input'],r['ground_truth'],r['raw_output']) for r in items)
                assert derived==primary,'Generated master differs from primary records: '+str(relative)
            else:
                derived=Counter((r['input'],str(r['ground_truth']),r['raw_prediction']) for r in items)
                assert not (derived-source_inputs),'Unmatched derived responses: '+str(relative)
            record.update(role='derived response export',decision='do not count twice',check='All output records match canonical run logs')
        elif path.suffix=='.json':
            d=json.loads(raw)
            if 'results' in d and isinstance(d['results'],list):
                match=source/'runs'/path.name
                assert match.exists() and json.loads(match.read_text())==d
                record.update(role='duplicate run package',decision='do not count twice',check='Matches same-named canonical run')
                record['rows']=len(d['results'])
            else:record.update(role='generated metadata',decision='recompute',check='JSON parsed; summary values are not independent evidence')
        elif path.suffix=='.csv':
            items=list(csv.DictReader(raw.decode().splitlines()));record['rows']=len(items)
            record.update(role='generated table/review',decision='recompute',check='CSV parsed; not additional API outputs')
            if path.name in {'MANUAL_FAILURE_REVIEW.csv','human_verification_review.csv'}:
                record['check']+='; '+str(sum(str(r.get('human_verified','')).lower()=='true' for r in items))+' human_verified flags'
        elif path.suffix=='.py':
            # Inspection only: source is never imported or executed.
            record.update(role='source script',decision='reference only',check='Read for parsing, channel substitution and request-setting provenance')
        elif path.suffix in {'.md','.txt','.log'}:
            raw.decode()
            record.update(role='written summary or supporting text',decision='supporting source only',check='Not evidence for percentages without matching run records')
        else:record.update(role='other',decision='exclude',check='Not an experiment source')
        audit.append(record)
    target=ROOT/'evidence/expanded_final';target.mkdir(parents=True,exist_ok=True)
    manifest={'source_directory':str(source),'audited_at':datetime.now(timezone.utc).isoformat(),
              'all_files_audited':len(audit),'canonical_run_files':len(runs),'canonical_source_rows':rows_seen,
              'new_run_files':new,'new_source_rows':sum(len(d['results']) for p,d in runs if p.name in new),
              'existing_source_rows_not_reimported':sum(len(d['results']) for p,d in runs if p.name not in new),
              'source_unchanged':True,'source_scripts_executed':False,'files':{}}
    for path,data in runs:
        if path.name not in new:continue
        destination=ROOT/'runs'/path.name
        output=(json.dumps(redact(data),indent=2,ensure_ascii=False)+'\n').encode()
        destination.write_bytes(output)
        manifest['files'][str(path.relative_to(source))]={'destination':str(destination.relative_to(ROOT)),'original_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256(output).hexdigest()}
    script=source/'execute_multitask_campaign.py'
    (target/script.name).write_text(redact(script.read_text()))
    manifest['files'][script.name]={'destination':str((target/script.name).relative_to(ROOT)),'original_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256((target/script.name).read_bytes()).hexdigest()}
    (target/'IMPORT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (ROOT/'analysis/FINAL_DIRECTORY_AUDIT.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(audit[0]));writer.writeheader();writer.writerows(audit)
    directories=defaultdict(list)
    for r in audit:directories[r['directory']].append(r)
    (ROOT/'analysis/FINAL_DIRECTORY_AUDIT.json').write_text(json.dumps({'source':str(source),'all_files':len(audit),'empty_directories':[str(p.relative_to(source)) for p in sorted(source.rglob('*')) if p.is_dir() and not any(p.iterdir())],
        'directories':{name:{'files':len(items),'roles':dict(Counter(r['role'] for r in items)),'decisions':dict(Counter(r['decision'] for r in items))} for name,items in directories.items()},
        'canonical_source_rows':rows_seen,'new_rows_imported':manifest['new_source_rows'],'duplicate_master_exports_verified':True},indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['all_files_audited','canonical_run_files','canonical_source_rows','new_source_rows','existing_source_rows_not_reimported']},indent=2))


if __name__=='__main__':main()
