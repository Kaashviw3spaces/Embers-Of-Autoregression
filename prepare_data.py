"""Reconstruct the user's documented seed-42 selection; not an original upload."""
from pathlib import Path
import csv
import json
import random

ROOT=Path(__file__).resolve().parent


def prepare_user_plan(root=ROOT):
    sources={cipher:[json.loads(line) for line in (root/'stimuli'/f'rot{cipher}dec_highprob.jsonl').read_text().splitlines() if line.strip()] for cipher in [13,12]}
    if len(sources[13])!=len(sources[12]):raise ValueError('Cipher files differ in length')
    for a,b in zip(sources[13],sources[12]):
        if a['correct_output']!=b['correct_output']:raise ValueError('Corresponding plaintexts differ')
    indices=sorted(random.Random(42).sample(range(len(sources[13])),30))
    data=root/'data';data.mkdir(exist_ok=True)
    tests=[]
    for index in indices:
        for cipher in [13,12]:
            item=sources[cipher][index]
            tests.append({'id':f'ROT-{cipher}_{index}','source_index':index,'cipher':f'ROT-{cipher}','input':item['input'],'prompt':item['instruction_plus_input'],'expected':item['correct_output'],'provenance':'Reconstructed from the documented seed-42 selection and supplied matching official stimuli; original selected file was not uploaded.'})
    with (data/'selected_tests_reconstructed.jsonl').open('w',encoding='utf-8') as file:
        for item in tests:file.write(json.dumps(item,ensure_ascii=False)+'\n')
    plan=[]
    for model in ['qwen3-30b-a3b','qwen3-32b']:
        for thinking in ['off','on']:
            for guidance in ['off','on']:
                for item in tests:
                    plan.append({'run_id':f'{model}_{thinking}_{guidance}_{item["id"]}','requested_model':model,'thinking':thinking,'internet_guidance':guidance,'test_id':item['id'],'cipher':item['cipher'],'status':'planned; not evidence of execution'})
    with (data/'planned_matrix.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=list(plan[0]));writer.writeheader();writer.writerows(plan)
    return tests,plan


if __name__=='__main__':
    tests,plan=prepare_user_plan()
    print(f'Reconstructed {len(tests)} test items and {len(plan)} planned cells. No API calls made.')
