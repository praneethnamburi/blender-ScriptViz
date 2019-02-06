"""
Analyze mkturk behavior data.
"""
import json
import subprocess

agent = 'Sausage'
startDate = '20190201'
endDate = '20190205'
outFile = f'./_temp/{agent}{startDate}to{endDate}.json'

subprocess.run(f'node mkturkBeh_getData.js -a {agent} -s {startDate} -e {endDate} -o {outFile} --no-print')
tmp1 = json.loads(open(outFile).read())
print(len(tmp1.keys()))