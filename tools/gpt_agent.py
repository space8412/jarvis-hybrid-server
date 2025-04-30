import requests, os

def request_gpt_agent(text):
    try:
        headers = {'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY")}'}
        res = requests.post(os.environ.get("GPT_AGENT_URL"), json={'text': text}, headers=headers)
        res.raise_for_status()
        return res.json()
    except:
        return {}
