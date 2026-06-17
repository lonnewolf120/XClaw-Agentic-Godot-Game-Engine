import subprocess
import os

print('Running...')
with open('out2.log', 'w', encoding='utf-8') as f:
    subprocess.run([
        'bin/godot.windows.editor.x86_64.console.exe',
        '--path', 'dummy_proj',
        '-e', '--headless'
    ], stdout=f, stderr=subprocess.STDOUT)

with open('out2.log', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('LIVE EDITOR')
if idx != -1:
    print(text[idx-50:idx+1500])
else:
    print('Not found. Tail of log:')
    print(text[-1000:])
