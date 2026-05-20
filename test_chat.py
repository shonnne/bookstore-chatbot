import urllib.request
import json

def chat(message):
    data = json.dumps({
        "model": "llama3.2",
        "prompt": message,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["response"]

print(chat("Say hello in one sentence."))