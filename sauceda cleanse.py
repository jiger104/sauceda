from datetime import datetime
import random
import csv
import io


def transform(event):

    input = event['_metadata']['input_label']
    if input == 'Endicia_InvoiceDetail':
        cleanse_endicia(event)
    elif input == 'Shiphero_ShipmentsReport':
        cleanse_shiphero_shipmentsreport(event)
    elif input == 'ShipHero_ShipmentsReport_VOID':
        cleanse_shiphero_shipmentsreport_void(event)
    elif input == 'Fedex_InvoiceDetail':
        cleanse_fedex(event)
    elif input == 'DHLe-commerce_InvoiceDetail':
        cleanse_dhl(event)
    elif input == 'TSheets_EmployeeJobCosting':
        cleanse_tsheets(event)
    elif input == 'Shipstation_Aws':
        cleanse_shipstation(event)
    elif input == 'APC_InvoiceDetail':
        cleanse_apc(event)
    return event

# cleanse endicia input. ignore postage purchase
# cleanse tracking number and standardize date and time formats


def cleanse_endicia(event):
    if event['Type'] == "Postage Purchase":
        return None
    else:
        event['Tracking Number'] = event['Tracking Number'].replace("'", "")
        event['Total Postage Amt'] = float(event['Total Postage Amt'][1:])
        event['Postmark'], event['Date/Time'] = fix_endicia_date(
            event['Postmark'], event['Date/Time'])
        return event

# cleanse shiphero input. standardize dates, quantities (as integer), column
# for dist channel,label type, and random tracking number for those orders without one


def cleanse_shiphero_shipmentsreport(event):
    event['Label Status'] = "Valid"
    event['Quantity Shipped Error'] = fix_shiphero_qty(event)
    event['Dist Channel'] = fix_shiphero_dist(event)
    event['Label Type'] = fix_shiphero_label(event)
    event['Tracking Number'] = fix_shiphero_tracking(event)
    event['Unique Shipment ID'] = fix_shiphero_unique(event)
    event['Multi-Pkg ID'] = event['Unique Shipment ID'] + \
        ":" + event['Quantity Shipped']
    event['Order Date'], event['Created Date'] = fix_shiphero_date(
        event['Order Date'], event['Created Date'])
    return event

# cleanse shiphero void report


def cleanse_shiphero_shipmentsreport_void(event):
    event['Label Status'] = "Void"
    event['Order Date'], event['Created Date'] = fix_shiphero_date(
        event['Order Date'], event['Created Date'])
    return event

# cleanse fedex input. standardize dates and times


def cleanse_fedex(event):
    event['Invoice Month (yyyymm)'], event['Shipment Date'], event['Shipment Delivery Date'] = fix_fedex_date(
        event['Invoice Month (yyyymm)'], event['Shipment Date'], event['Shipment Delivery Date'])
    return event

# cleanse dhl input. add headers to the csv, remove the first row of the input since it is junk data and standardize
# dates and times


def cleanse_dhl(event):
  event = fix_dhl_header(event)
  if event['Record Type'] == "HDR":
    return None
  else:
    event['Pickup Date'] = str(
      datetime.strptime(event['Pickup Date'], '%Y%m%d'))
    event['Invoice Date'] = fix_dhl_invoice_date(
      event['_metadata']['file_name'])
    return event

# cleanse tsheets input to split data into columns and add date to each row


def cleanse_tsheets(event):
    event['date'] = event['_metadata']['file_name'].replace(
        'Tsheets/', "").replace('.csv', "")
    event['project'] = event['original_row'][0].split(" >>")[0]
    event['job_code'] = event['original_row'][0].split(">> ")[1]
    event['total hours'] = float(event['original_row'][2])
    event['date'] = fix_tsheets_date(event['date'])
    return event

# cleanse shipstation input. standardize dates

def cleanse_shipstation(event):
    event['Date - Shipped Date'] = fix_shipstation_date(
        event['Date - Shipped Date'])
    return event

# cleanse apc input. standardize dates
# def cleanse_apc(event):
#     event['InvoiceDate'] = fix_apc_date(event)
#     return event


# functions
# -----------------------------------------------------------------------------------------------------------------------
# add a column to shiphero for dist channel. ecomm or wholesale based on condition below


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

# concatenate shiphero created date and order date as unique shipment field


def fix_shiphero_unique(event):
    o = event['Order Number']
    c = (datetime.strptime(event['Created Date'], '%m/%d/%Y %I:%M %p'))
    d = datetime.strftime(c, '%m%d%Y-%I%M%p')
    return (o + ":" + str(d))


# delete first 8 characters of tracking number of  any DHL domestic shipment on shiphero report, Also add random integer
# for orders with no tracking number
def fix_shiphero_tracking(event):
    m = event['Method']
    t = event['Tracking Number']
    if m[:6] == "DHL SM":
        return t[8:]
    elif t == "Add a tracking number":
        t = random.randint(99999, 999999)
        return t
    else:
        return t

# add in label for items with 0 qty in shiphero shipments report


def fix_shiphero_qty(event):
    q = int(event['Quantity Shipped'])
    if q == 0:
        e = "True"
        return e
    else:
        return "False"

# add a column to shiphero for label type. inbound or outbound based on condition below for tecovas return labels


def fix_shiphero_label(event):
    r = event['Method']
    h = event['3PL Customer']
    if r == "FEDEX_GROUND" and h == "Tecovas":
        g = "Inbound"
    else:
        g = "Outbound"
    return g

# function to add DHL event headers


def fix_dhl_header(event):
    headers = ["Record Type", "Sold To", "Inv_Posnr", "BOL", "Billing Ref", "Billing Ref 2",
               "Shipping Point", "Pick From", "Pickup Date", "Pickup Time", "Internal Tracking", "Customer Confirm",
               "Delivery Confirm", "Recipient Name", "Recipient Address 1", "Recipient Address 2", "Recipient City",
               "Recipient State", "Recipient Zip", "Recipient Country", "VAS Num", "VAS Dec", "Actual Weight",
               "UOM Actual Weight", "Billing Weight", "UOM Billing Weight", "Quantity", "UOM Quantity", "Pricing Zone",
               "Charge", "Customer Reference 1", "Customer Reference 2", "PRI_Dropoff", "PRI_Sort", "PRI_Stamp",
               "PRI_Machine", "PRI_Manifest", "PRI_BPM", "PRI_Future_Use 1", "PRI_Future_Use 2", "PRI_Future_Use 3",
               "Content_Endorsement", "Unassignable_Addrs", "Special_Handling", "Late_Arrival", "USPS_Qualif", "Client_SRD",
               "SC_Irreg", "Ret_Unassn_Chg", "Ret_Unprocess_Chg", "Ret_Recall_Disc_Chg", "Ret_Dup_Mail_Chg", "Ret_Cont_Assur_Chg",
               "Move_Update_Return", "GST_Tax", "HST_Tax", "PST_Tax", "VAT_Tax", "Duties", "Tax", "Paper_Invoice_Fee", "Screening_Fee",
               "Non_Auto_Flats", "FUTURE_USE 1", "Fuel 1", "Min_PickupChg 1", "Future Chg 1", "Future Chg 2", "Future Chg 3",
               "Future Chg 4", "Future Chg 5", "Future Chg 6", "Future Chg 7", "Future Chg 8", "Future Chg 9", "Future Chg 10",
               "Future Chg 11", "Future Chg 12", "Future Chg 13", "SC_placehold10", "FUEL 2", "MINPICKUP 2"]
    string = event['message']
    metadata = event['_metadata']
    f = io.StringIO(string)
    reader = csv.reader(f, delimiter=',')
    event = {}
    fields = list(reader)[0]
    event = dict(zip(headers[:len(fields)], fields))
    event['_metadata'] = metadata
    return event

# function to extract invoice date from the DHL filename


def fix_dhl_invoice_date(filename):
    a, b, c = filename.partition('_')
    d, e, f = c.partition('_')
    f = f.replace('.csv', "")
    f = str(datetime.strptime(f, '%Y%m%d'))
    return f


def fix_shipstation_date(date):
    try:
        date = str(datetime.strptime(
            date, '%m/%d/%Y %I:%M:%S %p'))
    except:
        date = str(datetime.strptime(
            date, '%m/%d/%Y %H:%M'))
    return date


def fix_endicia_date(postmark, date):
    if postmark and date:
        postmark = str(datetime.strptime(
            postmark, '%m/%d/%y'))
        date = str(datetime.strptime(
            date, ' %m/%d/%y-%I:%M:%S:%p'))
    else:
        date = str(datetime.strptime(
            date, ' %m/%d/%y-%I:%M:%S:%p'))
        postmark = date
    return postmark, date


def fix_fedex_date(invoice_date, ship_date, delivery_date):
    invoice_date = str(
        datetime.strptime(invoice_date, '%Y%m'))

    if ship_date and delivery_date:
        ship_date = str(datetime.strptime(
            ship_date, '%m/%d/%Y'))
        delivery_date = str(datetime.strptime(
            delivery_date, '%m/%d/%Y'))
    else:
        ship_date = str(datetime.strptime(
            ship_date, '%m/%d/%Y'))
        delivery_date = ship_date
    return invoice_date, ship_date, delivery_date


def fix_shiphero_date(order_date, created_date):
    order_date = str(datetime.strptime(
        order_date, '%m/%d/%Y %I:%M %p'))
    created_date = str(datetime.strptime(
        created_date, '%m/%d/%Y %I:%M %p'))
    return order_date, created_date


def fix_tsheets_date(date):
    date = str(datetime.strptime(event['date'], '%Y-%d-%m'))
    return date

# def fix_apc_date(event):
#     event['InvoiceDate'] = str(datetime.strptime(event['InvoiceDate'], '%Y-%m-%d + 'T' + %H:%M:%S'))
#     return event
