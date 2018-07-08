'''
Alooma's Code Engine allows you to write whatever custom code
you choose to cleanse, enrich, split, delete, make calls out,
and do whatever is possible with native Python code that you desire!

While we ship with just the standard "def transform(event)" function,
we've written some common code examples below for you to work from.
Check out our Code Engine docs for even more!
https://support.alooma.com/hc/en-us/articles/360000698651

If you have any questions about writing code,
or want to import a custom library,
feel free to contact us at support@alooma.com
'''
from datetime import datetime
import random
import csv, io

def transform(event):

  #cleanse endicia input. remove event types of postage purchase and refund, cleanse tracking number and standardize date and time formats
  if event['_metadata']['input_label'] == 'Endicia_AWS':

    if any (k in event['Type'] for k in ("Postage Purchase", "Postage Refund")):
      return None

    else:
      event['Tracking Number'] = fix_quote(event['Tracking Number'])
      event['Date/Time'] = str(datetime.strptime(event['Date/Time'], ' %m/%d/%y-%I:%M:%S:%p'))
      event['Postmark'] = fix_endicia_date(event['Postmark'])

      #if there are any endicia refunds or refunds rejected set the total postage to 0 otherwise make total postage a float value
      if any (k in event['Refund Status'] for k in ("Refunded", "Refund Rejected")):
            event['Total Postage Amt'] = 0
      else:
            event['Total Postage Amt'] = fix_postage(event['Total Postage Amt'])

      return event

   #cleanse shiphero input. standardize dates, quantities (as integer), and add a column for dist channel. Also add a random tracking number for those orders without one
  if event['_metadata']['input_label'] == 'Shiphero_aws':
    event['Order Date'] = str(datetime.strptime(event['Order Date'], '%m/%d/%Y %H:%M %p'))
    event['Created Date'] = str(datetime.strptime(event['Created Date'], '%m/%d/%Y %H:%M %p'))
    event['Quantity Shipped'] = int(event['Quantity Shipped'])
    event['Dist Channel'] = fix_shiphero_dist(event)
    if event['Tracking Number'] == "Add a tracking number":
      event['Tracking Number'] = random.randint(9999,99999)

  #cleanse fedex input. standardize dates and times
  if event['_metadata']['input_label'] == 'Fedex_aws':
     event['Invoice Month (yyyymm)'] = str(datetime.strptime(event['Invoice Month (yyyymm)'], '%Y%m'))
     event['Shipment Date']          = fix_fedex_date(event['Shipment Date'])
     event['Shipment Delivery Date']  = fix_fedex_date(event['Shipment Delivery Date'])

  #cleanse dhl input. add headers to the csv, remove the first row of the input since it is junk data and standardize dates and times
  if event['_metadata']['input_label'] == 'DHL_ftp':
    headers = ["Record Type", "Sold To", "Inventory Positioner", "BOL Number", "Billing Ref", "Billing Ref 2", "Processing Facility", "Pick From", "Pickup Date", "Pickup Time", "Internal Tracking", "Customer Confirm", "Delivery Confirm", "Recipient Name",
    "Recipient Address 1", "Recipient Address 2", "Recipient City", "Recipient State", "Recipient Zip", "Recipient Country", "VAS Num", "VAS Dec", "Actual Weight", "UOM Actual Weight", "Billing Weight", "UOM Billing Weight", "Quantity", "UOM Quantity", "Pricing Zone", "Charge", "Customer Reference"]
    string = event['message']
    metadata = event['_metadata']
    f = io.StringIO(string)
    reader = csv.reader(f, delimiter=',')
    event = {}
    fields = list(reader)[0]
    event['data'] = dict(zip(headers[:len(fields)], fields))
    event['_metadata'] = metadata

    if event['data']['Record Type'] == "HDR":
      return None
    else:
      event['data']['Pickup Date'] = str(datetime.strptime(event['data']['Pickup Date'], '%Y%m%d'))

    return event

  return event

def fix_quote(x):
  return x.replace("'","")

def fix_postage(y):
  if y.startswith('$'):
    z = y.replace(",","")
    return float(z[1:])
  return float(y)

def fix_fedex_date(f):
  if f:
    f = str(datetime.strptime(f, '%m/%d/%Y'))
  else:
    f = "2018-01-01 00:00:00"
  return f

def fix_endicia_date(e):
  if e:
    e = str(datetime.strptime(e, '%m/%d/%Y'))
  else:
    e = "2018-01-01 00:00:00"
  return e

#add a column to shiphero for dist channel. ecomm or wholesale based on heuristic below
def fix_shiphero_dist(event):
  r = event['Quantity Shipped']
  h = event['Store']
  if (any (k in event['3PL Customer'] for k in ("Howler Bros", "Kammok Operations", "The Brobe", "William Murray"))) and r >= 10 and h == "Manual Order":
    g = "Wholesale"
  else:
    g = "E-Commerce"
  return g







