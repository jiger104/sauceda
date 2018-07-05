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
    if event['_metadata']['input_label'] == 'Endicia_AWS':

        if any(k in event['Type'] for k in ("Postage Purchase", "Postage Refund")):
            return None

        else:
            event['Tracking Number'] = fix_quote(event['Tracking Number'])

            if any(k in event['Refund Status'] for k in ("Refunded", "Refund Rejected")):
                event['Total Postage Amt'] = 0
            else:
                event['Total Postage Amt'] = fix_postage(event['Total Postage Amt'])

            return event

    if event['_metadata']['input_label'] == 'Shiphero':
        event['Order Date'] = str(datetime.strptime(event['Order Date'], '%m/%d/%Y %H:%M %p'))
        event['Created Date'] = str(datetime.strptime(event['Created Date'], '%m/%d/%Y %H:%M %p'))
        if event['Tracking Number'] == "Add a tracking number":
            event['Tracking Number'] = random.randint(9999, 99999)

    if event['_metadata']['input_label'] == 'Fedex_Gdrive':
        event['Shipment Date'] = str(datetime.strptime(event['Shipment Date'], '%m/%d/%Y'))

    if event['_metadata']['input_label'] == 'DHL_ftp':
        headers = ["Record Type", "Sold To", "Inventory Positioner", "BOL Number", "Billing Ref", "Billing Ref 2",
                   "Processing Facility", "Pick From", "Pickup Date", "Pickup Time", "Internal Tracking",
                   "Customer Confirm", "Delivery Confirm", "Recipient Name",
                   "Recipient Address 1", "Recipient Address 2", "Recipient City", "Recipient State", "Recipient Zip",
                   "Recipient Country", "VAS Num", "VAS Dec", "Actual Weight", "UOM Actual Weight", "Billing Weight",
                   "UOM Billing Weight", "Quantity", "UOM Quantity", "Pricing Zone", "Charge", "Customer Reference"]
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
    return x.replace("'", "")


def fix_postage(y):
    if y.startswith('$'):
        z = y.replace(",", "")
        return float(z[1:])
    return float(y)


