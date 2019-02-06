import json
import subprocess

subprocess.call(['node', 'testjs.js'])
tmp1 = json.loads(open('temp.json').read())

a = 1