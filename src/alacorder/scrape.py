# the alacourt scraper, or, alacollect
# incomplete draft 1
# alacorder 76
# sam robson

## USE ON MACOS WITH CHROME INSTALLED! 
## DO NOT PRESS KEYS OR MOVE MOUSE WHILE SCRAPING.
## THIS IS A HEADED AUTOMATED SCRIPT.
## SET DEFAULT DOWNLOADS DIRECTORY IN CHROME TO DESIRED PDF DIRECTORY TARGET BEFORE INITIATING TASK.

import time
import click
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options # for 
import pandas as pd

gnames = [] # add list of names ["Last First", "Last First"] 
driver = None

options = webdriver.ChromeOptions()
options.add_experimental_option('prefs', {
"download.default_directory": "/Users/samuelrobson/Desktop/pdfbin/", #Change default directory for downloads
"download.prompt_for_download": False, #To auto download the file
"download.directory_upgrade": True,
"plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
})


@click.command()
@click.option("--customer-id", "-c","cID", required=True, prompt="Customer ID")
@click.option("--user-id", "-u","uID", required=True, prompt="User ID")
@click.option("--password-id", "-p","pwd", required=True, prompt="Password")
def go(cID, uID, pwd, names=None):
	global driver
	if names == None:
		global gnames
		if len(gnames) == 0:
			name_input = click.prompt("Enter names separated by comma")
			names = name_input.split(",")
			names = pd.Series(names).str.strip().replace(",","").tolist()
		else:
			names = gnames
	click.secho("Opening browser session... Do not move mouse or press any keys!",fg='bright_yellow',bold=True)
	driver = webdriver.Chrome(options=options)
	login(cID,uID,pwd)
	click.secho("Authentication successful. Beginning search...",fg='green',bold=True)
	for nm in names:
		p = party_search(name=nm)
		for i, x in enumerate(p):
			downloadPDF(str(x))
			time.sleep(5)
			click.secho(f"{i} downloaded successfully.")
		time.sleep(10)


def login(cID, username, pwd):

	login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

	driver.implicitly_wait(0.5)
	
	cID_box = driver.find_element(by=By.NAME, 
		value="ctl00$ContentPlaceHolder$txtCusid")
	username_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId")
	pwd_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword")
	login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

	cID_box.send_keys(cID)
	username_box.send_keys(username)
	pwd_box.send_keys(pwd)

	driver.implicitly_wait(0.5)
	login_button.click()

	driver.implicitly_wait(0.5)

	try:
		continueLogIn = driver.find_element(by=By.NAME, 
		value="ctl00$ContentPlaceHolder$btnContinueLogin")
		continueLogIn.click()
	except:
		pass

	driver.implicitly_wait(0.5)
	try:
		driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")
	except:
		pass

	driver.implicitly_wait(0.5)

def party_search(name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", no_records="", filed_before="", filed_after=""):

	driver.implicitly_wait(0.5)
	try:
		driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")
	except:
		pass

	party_name_box = driver.find_element(by=By.ID,value="ContentPlaceHolder1_txtName")
	ssn_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtSSN")
	plaintiffs_select = driver.find_element(by=By.ID, value="ContentPlaceHolder1_rdlPartyType_0")
	defendents_select = driver.find_element(by=By.ID, value="ContentPlaceHolder1_rdlPartyType_1")
	all_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$rdlPartyType")
	date_of_birth_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtDOB")
	county_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCounties")
	division_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$UcddlDivisions1$ddlDivision")
	case_year_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCaseYear")
	no_records_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlNumberOfRecords")
	filed_before_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtFrom")
	filed_after_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtTo")


	if name != "":
		party_name_box.send_keys(name)

	if ssn != "":
		ssn_box.send_keys(ssn)

	if dob != "":
		date_of_birth_box.send_keys(dob)

	if party_type == "plaintiffs":
		plaintiffs_select.click()

	if party_type == "defendants":
		defendents_select.click()

	if party_type == "ALL":
		all_select.click()

	if county != "":
		scounty = Select(county_select)
		scounty.select_by_visible_text(county)

	if division != "":
		sdivision = Select(division_select)
		sdivision.select_by_visible_text(division)

	if case_year != "":
		scase_year = Select(case_year_select)
		scase_year.select_by_visible_text(case_year)


	if no_records != "":
		sno_records = Select(no_records_select)
		sno_records.select_by_visible_text(no_records)

	if filed_before != "":
		filed_before_box.send_keys(sfiled_before)

	if filed_after != "":
		filed_after_box.send_keys(sfiled_after)

	search_button = driver.find_element(by=By.ID,value="searchButton")

	search_button.click()

	driver.implicitly_wait(2)


	results = []
	resulturls = []
	resultpages = []
	total = 0


	stop = False
	new = 1
	oldnew = 0

	while new > 0:
		oldnew = len(results)
		links = getURLtoPDF()
		print(links)
		results = results + links
		results = pd.Series(results).drop_duplicates().tolist()
		new = len(results) - oldnew
		total = len(results)
		try:
			next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
			next_button.click()
		except:
			pass
	results = pd.Series(results).drop_duplicates().tolist()
	return results

		
def close():
	driver.close()
	driver.quit()

def getURLtoPDF():
	pdflinks = []
	plants = driver.find_elements(By.CLASS_NAME, "menuHover")
	for x in plants:
		try:
			if "PDF" in x.get_attribute("href"):
				pdflinks.append(x.get_attribute("href"))
		except:
			pass
	return pdflinks

def downloadPDF(url):
	driver.implicitly_wait(0.5)
	a = driver.get(url)
	driver.implicitly_wait(0.5)
	time.sleep(5)
	return None
	

if __name__ == "__main__":
	go()





