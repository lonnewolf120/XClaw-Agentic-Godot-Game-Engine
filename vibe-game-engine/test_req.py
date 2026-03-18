import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:8000/plugin/proposal', method='POST')
req.add_header('Content-Type', 'application/json')
data = json.dumps({'prompt':'hello','selection':[],'mode':'scene_mutation','options':{}}).encode()
try:
    with urllib.request.urlopen(req, data=data) as f:
        print("Success:", f.read().decode())
except Exception as e:
    print("Failed:", e)
    print(e.read().decode())
