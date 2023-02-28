# the alacourt scraper, or, alacollect
# incomplete draft 2
# alacorder 76
# sam robson

## USE WITH CHROME (TESTED ON MACOS) 
## KEEP YOUR COMPUTER POWERED ON AND CONNECTED TO THE INTERNET.
## SET DEFAULT DOWNLOADS DIRECTORY IN BROWSER TO DESIRED PDF DIRECTORY TARGET BEFORE INITIATING TASK.

import os
import time
import click
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options 
from alacorder import alac


def readPartySearchQuery(path, qmax=0, qskip=0):
	good = os.path.exists(path)

	ext = os.path.splitext(path)[1]
	if ext == ".xlsx" or ".xls":
		query = pd.read_excel(path, dtype=pd.StringDtype())
	if ext == ".csv":
		query = pd.read_csv(path, dtype=pd.StringDtype())
	if ext == ".json":
		query = pd.read_json(path, orient='table', dtype=pd.StringDtype())
	click.echo(query.describe())
	if qskip > 0:
		query = query.truncate(before=qskip)
	if qmax > 0:
		query = query.truncate(after=qmax+qskip)
	query_out = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER"])

	for c in query.columns:
		if c.upper().strip().replace(" ","_") in ["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER"]:
			click.echo(f"Column {c} identified in query file.")
			query_out[c.upper().strip().replace(" ","_")] = query[c]

	query_out = query_out.fillna('')
	return query_out

# speed option?
@click.command()
@click.option("--input-path", "-in", "listpath", required=True, prompt="Path to search query table", help="Path to search query table/spreadsheet (.xls, .xlsx, .csv, .json)", type=click.Path())
@click.option("--output-path", "-out", "path", required=True, prompt="PDF download path", type=click.Path())
@click.option("--customer-id", "-c","cID", required=True, prompt="Alacourt Customer ID")
@click.option("--user-id", "-u","uID", required=True, prompt="Alacourt User ID")
@click.option("--password-id", "-p","pwd", required=True, prompt="Alacourt Password")
@click.option("--archive-path", "-a", required=False, type=click.Path(), help="Create full text archive after completing query")
@click.option("--max", "-max","qmax", required=False, type=click.Path(), help="Create full text archive after completing query",default=0)
@click.option("--skip", "-skip","qskip", required=False, type=click.Path(), help="Create full text archive after completing query",default=0)
def go(listpath, path, cID, uID, pwd, archive_path, qmax, qskip):

	query = readPartySearchQuery(listpath, qmax, qskip)


	options = webdriver.ChromeOptions()
	options.add_experimental_option('prefs', {
		"download.default_directory": path, #Change default directory for downloads
		"download.prompt_for_download": False, #To auto download the file
		"download.directory_upgrade": True,
		"plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
	})
	driver = webdriver.Chrome(options=options)

	# start browser session, auth
	click.secho("Opening browser session... Do not move mouse or press any keys!",fg='bright_yellow',bold=True)
	login(driver, cID,uID,pwd)
	click.secho("Authentication successful. Beginning search...",fg='green',bold=True)


	for n in query.index:
		results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], no_records=query.NO_RECORDS[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n])
		for url in results:
			downloadPDF(driver, url)
		time.sleep(2)
		driver.implicitly_wait(0.5)

	if archive_path:
		arcconf = alac.setpaths(path, archive_path)
		archive = alac.init(arcconf)
		return archive




def login(driver, cID, username, pwd):

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


def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", no_records="", filed_before="", filed_after=""):

	time.sleep(3)
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

	# submit search
	search_button = driver.find_element(by=By.ID,value="searchButton")
	search_button.click()

	# count pages
	driver.implicitly_wait(0.5)

	try:
		page_counter = driver.find_element(by=By.ID,value="ContentPlaceHolder1_dg_tcPageXofY").text
		pages = int(page_counter.strip()[-1])
	except:
	 	pages = 1

	click.echo(f"Found {pages} pages of results for {name}")

	# get PDF links from each page
	pdflinks = []
	i = 0
	for i in range(0,pages-1):
		hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
		for x in hovers:
			try:
				a = x.get_attribute("href")
				if "PDF" in a:
					pdflinks.append(a)
					click.echo(a)
			except:
				pass
		driver.implicitly_wait(1)
		try:
			pager_select = Select(driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"))
			next_pg = int(pager_select.text) + 1
			driver.implicitly_wait(1)
		except:
			try:
				driver.implicitly_wait(1)
				time.sleep(1)
				next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
				next_button.click()
			except:
				continue

	return pdflinks

def downloadPDF(driver, url, sleep=5, log=True):
	a = driver.get(url)
	driver.implicitly_wait(2)
	time.sleep(sleep-2)
	if log:
		click.echo(f"Downloaded {url}")

if __name__ == "__main__":
	go()
