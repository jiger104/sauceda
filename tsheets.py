import requests
from requests.auth import HTTPDigestAuth
import json
import datetime

url = "https://rest.tsheets.com/api/v1/reports/payroll_by_jobcode"
date = datetime.datetime.today().strftime('%Y-%m-%d')
payload = {"data": {"start_date": "{}".format(date),"end_date": "{}".format(date)}}
headers = {'Authorization':'Bearer S.1__eca36b67bc526e97b6dc1e67caabbf1e896e887b'}
myResponse = requests.post(url, headers=headers, json=payload)

with open('out.json', 'w') as f:
    f.write(myResponse.text)

if (myResponse.ok):
    print("T-Sheets API Success")
else:
    print("T-Sheets API Error")