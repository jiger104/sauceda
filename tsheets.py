import requests
from requests.auth import HTTPDigestAuth
import datetime
import tinys3

keyId = "AKIAJKIKJLANDLG4BC2Q"
sKeyId= "96yS/C1O7Tv7e9BbJMj836TSg5psoUlQ4qqBPDA4"
conn = tinys3.Connection(keyId, sKeyId, tls=True)
url = "https://rest.tsheets.com/api/v1/reports/payroll_by_jobcode"
date = datetime.datetime.today().strftime('%Y-%m-%d')
payload = {"data": {"start_date": "{}".format(date),"end_date": "{}".format(date)}}
headers = {'Authorization':'Bearer S.1__eca36b67bc526e97b6dc1e67caabbf1e896e887b'}
myResponse = requests.post(url, headers=headers, json=payload)

with open('{}.json'.format(date), 'w') as f:
      f.write(myResponse.text)
      x = open('{}.json'.format(date), 'rb')
      conn.upload('/Tsheets/{}.json'.format(date), x, 'sauceda-data')

if (myResponse.ok):
    print("T-Sheets API Success")
else:
    print("T-Sheets API Error")


