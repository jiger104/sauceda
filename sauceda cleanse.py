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
  input = event['_metadata']['input_label']

#cleanse endicia input. remove event types of postage purchase and refund, cleanse tracking number and standardize date and time formats
  if input == 'Endicia_InvoiceDetail':
    if any (k in event['Type'] for k in ("Postage Purchase", "Postage Refund")):
      return None
    else:
      event['Tracking Number'] = event['Tracking Number'].replace("'","")
      event['Total Postage Amt'] = fix_endicia_postage(event)
      event = fix_date(event)
      return event

#cleanse shiphero input. standardize dates, quantities (as integer), column for dist channel,label type, and random tracking number for those orders without one
  if input == 'Shiphero_ShipmentsReport':
    event = fix_date(event)
    event['Label Status'] = "Valid"
    event['Quantity Shipped Error'] = fix_shiphero_qty(event)
    event['Dist Channel'] = fix_shiphero_dist(event)
    event['Label Type'] = fix_shiphero_label(event)
    event['Tracking Number'] = fix_shiphero_tracking(event)
    return event

#cleanse shiphero void report
  if input == 'ShipHero_ShipmentsReport_VOID':
    event['Label Status'] = "Void"
    return event

#cleanse fedex input. standardize dates and times
  if input == 'Fedex_InvoiceDetail':
     event = fix_date(event)
     return event

#cleanse dhl input. add headers to the csv, remove the first row of the input since it is junk data and standardize dates and times
  if input == 'DHLe-commerce_InvoiceDetail':
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


#cleanse tsheets input to split data into columns and add date to each row
  if input == 'TSheets_EmployeeJobCosting':
      event['date'] = event['_metadata']['file_name'].replace('Tsheets/',"").replace('.csv', "")
      event['project'] = event['original_row'][0].split(" >>")[0]
      event['job_code'] = event['original_row'][0].split(">> ")[1]
      event['total hours'] = float(event['original_row'][2])
      event = fix_date(event)
      return event

#cleanse shipstation input. standardize dates
  if input == 'Shipstation_aws':
    event = fix_date(event)
    return event





#functions
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#change endicia postage to float value or 0 based on refund status
def fix_endicia_postage(event):
  r = event['Refund Status']
  t = event['Total Postage Amt']
  if any(k in r for k in ("Refunded", "Refund Rejected")):
      t = 0
      return t
  else:
      if t.startswith('$'):
          z = t.replace(",","")
          return float(z[1:])
      return float(t)

#add a column to shiphero for dist channel. ecomm or wholesale based on condition below
def fix_shiphero_dist(event):
  r = int(event['Quantity Shipped'])
  o = str(event['Order Number'])
  c = event['3PL Customer']
  h = event['Store']
  if c == "Howler Bros" and o[:2] == "IF":
    g = "Wholesale B2B"
  elif c == "Kammok Operations" and o[:2] == "KW":
    g = "Wholesale B2B"
  elif o[:4] != "EXC-" and r >= 10 and h == "Manual Order":
    g = "Wholesale B2B"
  else:
    g = "E-Commerce B2C"
  return g

#delete first 8 characters of tracking number of  any DHL domestic shipment on shiphero report, Also add random integer for orders with no tracking number
def fix_shiphero_tracking(event):
    m = event['Method']
    t = event['Tracking Number']
    if m[:6] == "DHL SM":
      return t[8:]
    elif t == "Add a tracking number":
      t = random.randint(99999,999999)
      return t
    else:
      return t

#add in label for items with 0 qty in shiphero shipments report
def fix_shiphero_qty(event):
    q = int(event['Quantity Shipped'])
    if q == 0:
        e = "True"
        return e
    else:
        return "False"

#add a column to shiphero for label type. inbound or outbound based on condition below for tecovas return labels
def fix_shiphero_label(event):
  r = event['Method']
  h = event['3PL Customer']
  if r == "FEDEX_GROUND" and h == "Tecovas":
    g = "Inbound"
  else:
    g = "Outbound"
  return g

#global function to fix date formatting
def fix_date(event):
    input = event['_metadata']['input_label']
    if input == 'Shipstation_aws':
      try:
         event['Date - Shipped Date'] = str(datetime.strptime(event['Date - Shipped Date'], '%m/%d/%Y %I:%M:%S %p'))
      except:
         event['Date - Shipped Date'] = str(datetime.strptime(event['Date - Shipped Date'], '%m/%d/%Y %H:%M'))
      return event

    if input == "Endicia_InvoiceDetail":
      if event['Postmark'] and event['Date/Time']:
        event['Postmark'] = str(datetime.strptime(event['Postmark'], '%m/%d/%y'))
        event['Date/Time'] = str(datetime.strptime(event['Date/Time'], ' %m/%d/%y-%I:%M:%S:%p'))
      else:
        event['Date/Time'] = str(datetime.strptime(event['Date/Time'], ' %m/%d/%y-%I:%M:%S:%p'))
        event['Postmark'] = event['Date/Time']
      return event

    if input == 'Fedex_InvoiceDetail':

      event['Invoice Month (yyyymm)'] = str(datetime.strptime(event['Invoice Month (yyyymm)'], '%Y%m'))

      if event['Shipment Date'] and event['Shipment Delivery Date']:
        event['Shipment Date'] = str(datetime.strptime(event['Shipment Date'], '%m/%d/%Y'))
        event['Shipment Delivery Date'] = str(datetime.strptime(event['Shipment Delivery Date'], '%m/%d/%Y'))
      else:
        event['Shipment Date'] = str(datetime.strptime(event['Shipment Date'], '%m/%d/%Y'))
        event['Shipment Delivery Date'] = event['Shipment Date']
      return event

    if input == 'Shiphero_ShipmentsReport' or x == 'Shiphero_ShipmentsReport_VOID':
        event['Order Date'] = str(datetime.strptime(event['Order Date'], '%m/%d/%Y %I:%M %p'))
        event['Created Date'] = str(datetime.strptime(event['Created Date'], '%m/%d/%Y %I:%M %p'))
        return event

    if input == "TSheets_EmployeeJobCosting":
       event['date'] = str(datetime.strptime(event['date'], '%Y-%d-%m'))
       return event





