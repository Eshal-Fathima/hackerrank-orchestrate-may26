import urllib.request
import json
import os

key = os.environ.get("GROQ_API_KEY", "NOT SET")
print(f"Key value: {key}")
print(f"Key length: {len(key)}")

payload = json.dumps({
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "say hi"}],
    "max_tokens": 10
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        print("SUCCESS:", json.loads(resp.read())["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    print(f"FAILED: {e.code} - {e.read().decode()}")