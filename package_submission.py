"""Create a redacted, reproducible submission ZIP without making API requests."""
from pathlib import Path
import hashlib
import json
import zipfile
import shutil
from analysis.evidence import redact

ROOT=Path(__file__).resolve().parent


def shared_bytes(path):
    data=path.read_bytes()
    if path.suffix=='.json':
        return (json.dumps(redact(json.loads(data)),indent=2,ensure_ascii=False)+'\n').encode()
    if path.suffix=='.jsonl':
        return ''.join(json.dumps(redact(json.loads(line)),ensure_ascii=False)+'\n' for line in data.decode().splitlines() if line.strip()).encode()
    if path.suffix=='.csv':return redact(data.decode()).encode()
    return data


def main():
    from rebuild_evidence import main as rebuild
    rebuild()
    names=['README.md','CORRECTIONS.md','requirements.txt','.gitignore','rebuild_evidence.py','prepare_data.py','run_experiment.py','run_qwen.py','verify_models.py','test_single.py','results_logger.py','assemble_master_repository.py','build_master_research_log.py','package_submission.py','validate_submission.py','MASTER_RESEARCH_LOG.md','MODEL_COMPARISON.md','MASTER_RESULTS.csv','MASTER_RAW_RESPONSES.jsonl','MASTER_API_ERRORS.csv','MASTER_ERROR_ANALYSIS.csv','MASTER_RUN_METADATA.json','MANUAL_FAILURE_REVIEW.csv','experiment_inventory.md']
    selected=[ROOT/name for name in names]+[ROOT/'NEXT_STEPS.txt',ROOT/'import_friend2.py',ROOT/'import_expanded.py',ROOT/'Manual_Error_Review.xlsx',ROOT/'KAGGLE_WRITEUP.md',ROOT/'KAGGLE_FORM.txt',ROOT/'build_submission_assets.py',ROOT/'SUBMISSION_CHECKLIST.txt']
    for folder in ['analysis','tests','stimuli','retrieval','report','slides','data','runs','evidence/user/redacted','evidence/friend2','evidence/expanded_final','results/master','submission_assets']:
        selected += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.csv','.json','.jsonl','.md','.pdf','.txt','.pptx','.xlsx','.png'}]
    selected += [ROOT/'evidence/user/failure_review_AI_draft.csv']
    files={str(path.relative_to(ROOT)):shared_bytes(path) for path in sorted(set(selected)) if path.exists()}
    manifest={
        'status':'corrected incomplete reproduction; participant verification pending',
        'model_inference_calls_during_correction':0,
        'exclusions':['virtual environments','caches','original credential-containing user log','superseded first-project generated reports','external original-project backup','third project repo/ published-author code and closed-model reference logs'],
        'source_copy_policy':'JSON/JSONL copies are reserialized and credential identifiers redacted. Original local run files remain unchanged. analysis/source_hashes.json identifies local originals; hashes below identify public archive bytes.',
        'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
    }
    files['SUBMISSION_MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    target=ROOT/'submission/Embers_Final_Submission.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr('Embers_Final_Submission/'+name,data)
    shutil.copyfile(target,ROOT/'submission/Embers_Corrected_Combined.zip')
    print(target)
    return target


if __name__=='__main__':main()
