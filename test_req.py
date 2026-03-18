import requests

try:
    res = requests.post("http://127.0.0.1:8000/plugin/proposal", json={
        "prompt": "hello",
        "selection": [],
        "mode": "scene_mutation",
        "options": {}
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
