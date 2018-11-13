from dateutil import parser
from datetime import datetime


class Shiphero_ShipmentsReport:

    def __init__(self, event):
    self.event = event

    def fix_shiphero_qty(self):
        q = int(self.event['Quantity Shipped'])
        if q == 0:
            e = "True"
            return e
        else:
            return "False"

    def fix_shiphero_label(self):
        r = self.event['Method']
        h = self.event['3PL Customer']
        if r == "FEDEX_GROUND" and h == "Tecovas":
            g = "Inbound"
        else:
            g = "Outbound"
        return g

    def fix_shiphero_tracking(self):
        m = self.event['Method']
        t = self.event['Tracking Number']
        if m[:6] == "DHL SM":
            return t[8:]
        elif t == "Add a tracking number":
            t = random.randint(99999, 999999)
            return t
        else:
            return t

    def fix_shiphero_unique(self):
        o = self.event['Order Number']
        c = (datetime.strptime(
            self.event['Created Date'], '%m/%d/%Y %I:%M %p'))
        d = datetime.strftime(c, '%m%d%Y')
        return (o + "-" + str(d))

    def fix_shiphero_dist(self):
        r = int(self.event['Quantity Shipped'])
        o = str(self.event['Order Number'])
        c = self.event['3PL Customer']
        h = self.event['Store']
        if c == "Howler Bros" and o[:2] == "IF":
            g = "Wholesale B2B"
        elif c == "Kammok Operations" and o[:2] == "KW":
            g = "Wholesale B2B"
        elif o[:4] != "EXC-" and r >= 10 and h == "Manual Order":
            g = "Wholesale B2B"
        else:
            g = "E-Commerce B2C"
        return g

    def fix_shiphero_date(self):
        o, c = self.event['Order Date'], self.event['Created Date']
