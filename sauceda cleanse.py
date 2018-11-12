from datetime import datetime
import random
import csv
import io


def transform(event):
    input = event['_metadata']['input_label']

# cleanse endicia input. remove event types of postage purchase and refund,
# cleanse tracking
# number and standardize date and time formats
    if input == 'Endicia_InvoiceDetail':
        if event['Type'] == "Postage Purchase":
            return None
        else:
            event['Tracking Number'] = event['Tracking Number'].replace(
                "'", "")
            event['Total Postage Amt'] = float(event['Total Postage Amt'][1:])
            event = fix_date(event)
            return event

# cleanse shiphero input. standardize dates, quantities (as integer), column
# for dist channel,label type, and random tracking number for those orders without one
    if input == 'Shiphero_ShipmentsReport':
        event['Label Status'] = "Valid"
        event['Quantity Shipped Error'] = fix_shiphero_qty(event)
        event['Dist Channel'] = fix_shiphero_dist(event)
        event['Label Type'] = fix_shiphero_label(event)
        event['Tracking Number'] = fix_shiphero_tracking(event)
        event['Unique Shipment ID'] = fix_shiphero_unique(event)
        event = fix_date(event)
        return event

# cleanse shiphero void report
    if input == 'ShipHero_ShipmentsReport_VOID':
        event['Label Status'] = "Void"
        return event

# cleanse fedex input. standardize dates and times
    if input == 'Fedex_InvoiceDetail':
        event = fix_date(event)
        return event

# cleanse dhl input. add headers to the csv, remove the first row of the input since it is junk data and standardize
# dates and times
    if input == 'DHLe-commerce_InvoiceDetail':
        event = fix_dhl_headers(event)
        if event['data']['Record Type'] == "HDR":
            return None
        event['data']['Pickup Date'] = str(
            datetime.strptime(event['data']['Pickup Date'], '%Y%m%d'))
        event['data']['Invoice Date'] = fix_dhl_invoice_date(event['_metadata']['file_name'])
        return event

# cleanse tsheets input to split data into columns and add date to each row
    if input == 'TSheets_EmployeeJobCosting':
        event['date'] = event['_metadata']['file_name'].replace(
            'Tsheets/', "").replace('.csv', "")
        event['project'] = event['original_row'][0].split(" >>")[0]
        event['job_code'] = event['original_row'][0].split(">> ")[1]
        event['total hours'] = float(event['original_row'][2])
        event = fix_date(event)
        return event

# cleanse shipstation input. standardize dates
    if input == 'Shipstation_aws':
        event = fix_date(event)
        return event


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
    return (o + "-" + str(d))


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


def fix_dhl_headers(event):
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
    event['data'] = dict(zip(headers[:len(fields)], fields))
    event['_metadata'] = metadata
    return event

#function to extract invoice date from the DHL filename 

def fix_dhl_invoice_date(filename):
    a, b, c = filename.partition('_')
    d, e, f = c.partition('_')
    f = f.replace('.csv', "")
    f = str(datetime.strptime(f, '%Y%m%d'))
    return f

# global function to fix date formatting


def fix_date(event):
    input = event['_metadata']['input_label']
    if input == 'Shipstation_aws':
        try:
            event['Date - Shipped Date'] = str(datetime.strptime(
                event['Date - Shipped Date'], '%m/%d/%Y %I:%M:%S %p'))
        except:
            event['Date - Shipped Date'] = str(datetime.strptime(
                event['Date - Shipped Date'], '%m/%d/%Y %H:%M'))
        return event

    if input == "Endicia_InvoiceDetail":
        if event['Postmark'] and event['Date/Time']:
            event['Postmark'] = str(datetime.strptime(
                event['Postmark'], '%m/%d/%y'))
            event['Date/Time'] = str(datetime.strptime(
                event['Date/Time'], ' %m/%d/%y-%I:%M:%S:%p'))
        else:
            event['Date/Time'] = str(datetime.strptime(
                event['Date/Time'], ' %m/%d/%y-%I:%M:%S:%p'))
            event['Postmark'] = event['Date/Time']
        return event

    if input == 'Fedex_InvoiceDetail':

        event['Invoice Month (yyyymm)'] = str(
            datetime.strptime(event['Invoice Month (yyyymm)'], '%Y%m'))

        if event['Shipment Date'] and event['Shipment Delivery Date']:
            event['Shipment Date'] = str(datetime.strptime(
                event['Shipment Date'], '%m/%d/%Y'))
            event['Shipment Delivery Date'] = str(datetime.strptime(
                event['Shipment Delivery Date'], '%m/%d/%Y'))
        else:
            event['Shipment Date'] = str(datetime.strptime(
                event['Shipment Date'], '%m/%d/%Y'))
            event['Shipment Delivery Date'] = event['Shipment Date']
        return event

    if input == 'Shiphero_ShipmentsReport' or input == 'Shiphero_ShipmentsReport_VOID':
        event['Order Date'] = str(datetime.strptime(
            event['Order Date'], '%m/%d/%Y %I:%M %p'))
        event['Created Date'] = str(datetime.strptime(
            event['Created Date'], '%m/%d/%Y %I:%M %p'))
        return event

    if input == "TSheets_EmployeeJobCosting":
        event['date'] = str(datetime.strptime(event['date'], '%Y-%d-%m'))
        return event
