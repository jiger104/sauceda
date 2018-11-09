from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

user = "jigarpatel@scalefactor.com"
pwd = "E61da4n2@"

driver = webdriver.Firefox()
driver.get("http://login.xero.com")
assert "Xero" in driver.title

elem = driver.find_element_by_id("email")

elem.send_keys(user)

elem = driver.find_element_by_id("password")

elem.send_keys(pwd)

elem.send_keys(Keys.RETURN)

time.sleep(5)

driver.get("https://go.xero.com/AccountsReceivable/Search.aspx?graphSearch=False&dateWithin=any&pageSize=25&unsentOnly=False&orderby=InvoiceDate&direction=ASC")
assert "Invoices" in driver.title

time.sleep(3)

elem = driver.find_elements_by_xpath('//TD[contains(@id, "ext-gen")]')

elem[1].click()