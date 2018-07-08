import requests
from requests.auth import HTTPDigestAuth
import json
import datetime

url = "https://rest.tsheets.com/api/v1/reports/payroll_by_jobcode"
s_date = datetime.datetime.today().strftime('%Y-%m-%d')
e_date = datetime.datetime.now
payload = {"data": {"start_date": "2017-03-12","end_date": "2017-03-18"}}
headers = {'Authorization':'Bearer S.1__eca36b67bc526e97b6dc1e67caabbf1e896e887b'}
myResponse = requests.post(url, headers=headers, json=payload)

print(s_date)

# with open('out.json', 'w') as f:
#    f.write(myResponse.text)

if (myResponse.ok):
    print("Success")

else:
    print("Error")