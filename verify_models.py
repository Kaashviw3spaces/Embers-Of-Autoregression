"""List advertised model IDs only; this does not verify checkpoint identity."""
import argparse
import getpass
import os


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base_url',default=os.getenv('OPENAI_BASE_URL',''))
    args=parser.parse_args()
    if not args.base_url:
        parser.error('Provide the shared open-model server URL via --base_url or OPENAI_BASE_URL.')
    import requests
    key=os.getenv('OPENAI_API_KEY') or getpass.getpass('API key (hidden): ')
    response=requests.get(args.base_url.rstrip('/')+'/models',headers={'Authorization':f'Bearer {key}'},timeout=(5,15))
    print('HTTP status:',response.status_code)
    if response.status_code==200:
        for model in response.json().get('data',[]):print(model.get('id'))
    print('Advertised aliases alone do not establish distinct checkpoints or effective thinking controls.')


if __name__=='__main__':main()
