"""Copy a redacted evidence snapshot from the third supplied project; no API calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import argparse
import zipfile
from pathlib import PurePosixPath
from analysis.evidence import redact

ROOT=Path(__file__).resolve().parent
SOURCE=Path('/Users/kashvi/Downloads/embers_replication')


def wanted(name):
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe archive path')
    return (name in {'README.md','docs/student_learning_curve.md'} or
            path.parent==PurePosixPath('logs') and path.suffix in {'.md','.jsonl'} or
            path.parent==PurePosixPath('results') and path.suffix=='.md' or
            path.parent==PurePosixPath('src') and path.suffix=='.py' or
            path.parent==PurePosixPath('data/benchmark_subsets') and path.suffix=='.jsonl')


def import_archive(archive_path):
    """Read only selected evidence files; never execute supplied scripts."""
    target=ROOT/'evidence/friend2'
    previous=json.loads((target/'IMPORT_MANIFEST.json').read_text()) if (target/'IMPORT_MANIFEST.json').exists() else {'files':{}}
    manifest={'source_archive':str(archive_path),'source_archive_sha256':hashlib.sha256(archive_path.read_bytes()).hexdigest(),
              'snapshot_at':datetime.now(timezone.utc).isoformat(),'source_unchanged':True,
              'source_reference_scripts':'Redacted copies for inspection only; not executed by the corrected pipeline.',
              'excluded':'Published datasets beyond the selected benchmarks, generated master duplicates as experiments, and scripts as executable pipeline code.',
              'files':{}}
    changes=[]
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir():continue
            parts=PurePosixPath(info.filename).parts
            if not parts or parts[0]!='embers_replication':continue
            relative='/'.join(parts[1:])
            if not wanted(relative):continue
            raw=archive.read(info)
            if info.filename.endswith('.jsonl'):
                records=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
                output=''.join(json.dumps(redact(r),ensure_ascii=False)+'\n' for r in records).encode()
            else:
                text=redact(raw.decode())
                if relative.endswith('.md'):
                    text='> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.\n\n'+text
                output=text.encode()
            digest=hashlib.sha256(raw).hexdigest()
            old=previous['files'].get(relative)
            status='added' if old is None else 'unchanged' if digest==old['original_sha256'] else 'changed'
            changes.append({'file':relative,'change':status,'original_sha256':digest})
            path=target/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(output)
            manifest['files'][relative]={'original_sha256':digest,'snapshot_sha256':hashlib.sha256(output).hexdigest(),'redaction_and_reserialization_applied':True}
    (target/'IMPORT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'analysis/ARCHIVE_UPDATE_DIFF.json').write_text(json.dumps({'archive_sha256':manifest['source_archive_sha256'],'changes':changes,'no_source_scripts_executed':True},indent=2)+'\n')
    counts=', '.join(str(sum(r['change']==status for r in changes))+' '+status for status in ['added','changed','unchanged'])
    print(f'Imported {len(changes)} selected files from archive; '+counts+'. No model calls.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if args.archive:
        import_archive(args.archive)
        return
    target=ROOT/'evidence/friend2'
    chosen=[*sorted((SOURCE/'logs').glob('*.jsonl')),*sorted((SOURCE/'logs').glob('*.md')),*sorted((SOURCE/'results').glob('*.md')),*sorted((SOURCE/'src').glob('*.py')),SOURCE/'README.md',SOURCE/'docs/student_learning_curve.md',*sorted((SOURCE/'data/benchmark_subsets').glob('*.jsonl'))]
    manifest={'source_directory':str(SOURCE),'snapshot_at':datetime.now(timezone.utc).isoformat(),'source_unchanged':True,'source_reference_scripts':'Redacted copies for inspection only; not executed by the corrected pipeline.','excluded':'repo/ contains the published authors\' repository and model logs; these are reference material, not team experiment results.','files':{}}
    for path in chosen:
        relative=path.relative_to(SOURCE)
        raw=path.read_bytes()
        if path.suffix=='.jsonl':
            records=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
            output=''.join(json.dumps(redact(r),ensure_ascii=False)+'\n' for r in records).encode()
        else:
            text=redact(raw.decode())
            if path.suffix=='.md':
                text='> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.\n\n'+text
            output=text.encode()
        destination=target/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(output)
        manifest['files'][str(relative)]={'original_sha256':hashlib.sha256(raw).hexdigest(),'snapshot_sha256':hashlib.sha256(output).hexdigest(),'redaction_and_reserialization_applied':True}
    (target/'IMPORT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Snapshotted {len(chosen)} files. Original source unchanged; credentials redacted; no inference calls.')


if __name__=='__main__':main()
