"""Sequential, explicitly opt-in live runner. Offline rebuilding needs no API key."""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import time

from analysis.evidence import redact
from analysis.scoring import evaluate, normalized_answer

ROOT = Path(__file__).resolve().parent


def parse_acronym_response(raw_text, gt=None):
    # gt is accepted for compatibility but deliberately never consulted.
    return normalized_answer(raw_text, "acronym1")


def parse_cipher_response(raw_text):
    return normalized_answer(raw_text, "rot13dec")


def make_request(model, prompt, thinking, guidance, temperature=.6, max_tokens=4096):
    if guidance:
        prompt = "Reference material:\n" + guidance + "\n\nTask:\n" + prompt
    return {
        "model": model,
        "messages": [{"role":"system", "content":"Return only the final transformed text in the final answer."}, {"role":"user", "content":prompt}],
        "reasoning_effort":"medium" if thinking else "none",
        "temperature":temperature, "top_p":.95, "max_tokens":max_tokens,
    }


def response_record(response_data, request):
    choice = response_data["choices"][0]
    message = choice["message"]
    usage = response_data.get("usage") or {}
    return {
        "content":message.get("content") or "", "reasoning_content":message.get("reasoning_content") or "",
        "finish_reason":choice.get("finish_reason"), "response_id":response_data.get("id"),
        "requested_model":request["model"], "returned_model":response_data.get("model"),
        "checkpoint_verified":False, "thinking_verified":False,
        "prompt_tokens":usage.get("prompt_tokens"), "completion_tokens":usage.get("completion_tokens"),
        "total_tokens":usage.get("total_tokens"), "raw_api_response":redact(response_data),
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=["qwen3-32b","qwen3-30b-a3b"])
    parser.add_argument("--task_type", required=True, choices=["acronym","cipher"])
    parser.add_argument("--conditions", default="")
    parser.add_argument("--mode", default="smoke", choices=["smoke","pilot","full"])
    parser.add_argument("--intervention", default="baseline", choices=["baseline","thinking","guidance","thinking_guidance"])
    parser.add_argument("--guidance_file", default=str(ROOT/"retrieval/guidance.txt"))
    parser.add_argument("--max_samples", type=int)
    parser.add_argument("--max_tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=.6)
    parser.add_argument("--base_url", default=os.getenv("OPENAI_BASE_URL", ""))
    parser.add_argument("--output_dir", default=str(ROOT/"runs"))
    parser.add_argument("--live", action="store_true", help="Actually send server requests; otherwise only preview.")
    args=parser.parse_args()
    if args.max_tokens <= 0 or args.max_samples is not None and args.max_samples <= 0:
        parser.error("Token/sample limits must be positive.")
    names=args.conditions.split(',') if args.conditions else (["acronym1_11","acronym1_51","acronym1_15"] if args.task_type=="acronym" else ["rot13dec","rot12dec"])
    guidance=Path(args.guidance_file).read_text().strip() if "guidance" in args.intervention else ""
    if "guidance" in args.intervention and not guidance:
        parser.error("Guidance conditions require a nonempty, cited guidance file.")
    limit=args.max_samples or (5 if args.mode=="smoke" else 100 if args.mode=="pilot" else None)
    plans=[]
    for task in names:
        path=ROOT/'stimuli'/f"{task}{'' if 'acronym' in task else '_highprob'}.jsonl"
        items=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        for index,item in enumerate(items[:limit]):
            plans.append((task,index,item,make_request(args.model,item['instruction_plus_input'],'thinking' in args.intervention,guidance,args.temperature,args.max_tokens)))
    if not args.live:
        print(f"DRY RUN: {len(plans)} planned sequential requests; no API calls made.")
        print(json.dumps(plans[0][3],indent=2))
        print("Mode/checkpoint identities remain unverified.")
        return
    if not args.base_url:
        parser.error("Set --base_url or OPENAI_BASE_URL to the shared open-model server.")
    from urllib.parse import urlparse
    if (urlparse(args.base_url).hostname or '').lower().endswith(('openai.com','anthropic.com','googleapis.com')):
        parser.error("Use the shared open-model server, not paid model endpoints.")
    import requests
    key=os.getenv('OPENAI_API_KEY') or getpass.getpass('API key (hidden): ')
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory=Path(args.output_dir);directory.mkdir(parents=True,exist_ok=True)
    log=directory/f'live_attempts_{timestamp}.jsonl'
    print(f"Logging to {log}. Sequential; stops on first server/transport error.")
    for number,(task,index,item,body) in enumerate(plans,1):
        row={'timestamp':datetime.now(timezone.utc).isoformat(),'task_name':task,'stimulus_id':index,'model':args.model,'condition':args.intervention,'request':body,'input_words':item['input'],'prompt':body['messages'][-1]['content'],'gt':item['correct_output'],'api_error':None}
        started=time.monotonic()
        try:
            response=requests.post(args.base_url.rstrip('/')+'/chat/completions',headers={'Authorization':f'Bearer {key}'},json=body,timeout=(10,180))
            row['http_status']=response.status_code
            if response.status_code != 200:
                row['api_error']=f'HTTP {response.status_code}: '+redact(response.text or 'empty response body')
            else:
                data=response.json();details=response_record(data,body);row.update(details)
                row['raw_response']=details['content']
                row.update(evaluate(details['content'],item['correct_output'],details['finish_reason'],task))
                row['correct']=row['strict_correct']
        except (requests.RequestException, ValueError, KeyError, IndexError) as error:
            row['api_error']=redact(str(error))
        except KeyboardInterrupt:
            row['api_error']='Interrupted by participant; server request may still be running. No automatic retry.'
        row['latency']=time.monotonic()-started
        with log.open('a',encoding='utf-8') as file:
            file.write(json.dumps(redact(row),ensure_ascii=False)+'\n')
        print(f"{number}/{len(plans)} {task}:{index} {row.get('status', 'request_error')}",flush=True)
        if not row['api_error']:
            print('Returned model:',row.get('returned_model'))
            print('Finish reason:',row.get('finish_reason'))
            print('Reasoning characters:',len(row.get('reasoning_content') or ''))
            print('Final answer:',repr(row.get('content','')))
        if row['api_error']:
            print("Stopped without automatic retries; a disconnected call may still occupy a server slot.")
            break
        time.sleep(3.5)


if __name__ == '__main__':
    main()
