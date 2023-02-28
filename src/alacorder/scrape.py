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


def readPartySearchQuery(path, qmax=0, qskip=0, speed=1, no_log=False):
	good = os.path.exists(path)

	ext = os.path.splitext(path)[1]
	if ext == ".xlsx" or ".xls":
		query = pd.read_excel(path, dtype=pd.StringDtype())
	if ext == ".csv":
		query = pd.read_csv(path, dtype=pd.StringDtype())
	if ext == ".json":
		query = pd.read_json(path, orient='table', dtype=pd.StringDtype())
	if qskip > 0:
		query = query.truncate(before=qskip)
	if qmax > 0:
		query = query.truncate(after=qmax+qskip)
	query_out = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER"])

	for c in query.columns:
		if c.upper().strip().replace(" ","_") in ["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER"]:
			if not no_log:
				click.echo(f"Column {c} identified in query file.")
			query_out[c.upper().strip().replace(" ","_")] = query[c]

	query_out = query_out.fillna('')
	return query_out

@click.command()
@click.option("--input-path", "-in", "listpath", required=True, prompt="Path to query table", help="Path to query table/spreadsheet (.xls, .xlsx, .csv, .json)", type=click.Path())
@click.option("--output-path", "-out", "path", required=True, prompt="PDF download path", type=click.Path(), help="Desired PDF output directory")
@click.option("--customer-id", "-c","cID", required=True, prompt="Alacourt Customer ID", help="Customer ID on Alacourt.com")
@click.option("--user-id", "-u","uID", required=True, prompt="Alacourt User ID", help="User ID on Alacourt.com")
@click.option("--password-id", "-p","pwd", required=True, prompt="Alacourt Password", help="Password on Alacourt.com")
@click.option("--archive-path", "-a", required=False, type=click.Path(), help="Create archive after directory export")
@click.option("--max", "-max","qmax", required=False, type=int, help="Maximum queries to conduct on Alacourt.com",default=0)
@click.option("--skip", "-skip","qskip", required=False, type=int, help="Skip entries at top of query file",default=0)
@click.option("--speed", default=1, type=int, help="Speed multiplier")
@click.option("--no-log","-nl", is_flag=True, default=False, help="Do not print logs to console")
def go(listpath, path, cID, uID, pwd, archive_path, qmax, qskip, speed, no_log):

	query = readPartySearchQuery(listpath, qmax, qskip, no_log)


	options = webdriver.ChromeOptions()
	options.add_experimental_option('prefs', {
		"download.default_directory": path, #Change default directory for downloads
		"download.prompt_for_download": False, #To auto download the file
		"download.directory_upgrade": True,
		"plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
	})
	driver = webdriver.Chrome(options=options)

	# start browser session, auth
	if not no_log:
		click.secho("Opening browser session... Do not move mouse or press any keys!",fg='bright_yellow',bold=True)

	login(driver, cID,uID,pwd,speed)

	if not no_log:
		click.secho("Authentication successful. Beginning search...",fg='green',bold=True)

	with click.progressbar(query.index) as bar:
		for i, n in enumerate(bar):
			results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], no_records=query.NO_RECORDS[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], speed=speed, no_log=no_log)
			with click.progressbar(results) as bar2:
				for ii, url in enumerate(bar2):
					downloadPDF(driver, url)
					if not no_log:
						click.echo(f"Downloaded case {ii} of query {i} / {max(query.index)}: {query.NAME[n]}")
			time.sleep(1.5/speed)
			driver.implicitly_wait(0.5/speed)

	if archive_path:
		arcconf = alac.setpaths(path, archive_path)
		archive = alac.init(arcconf)
		return archive




def login(driver, cID, username, pwd, speed, no_log=False):

	if not no_log:
		click.echo("Logging in to Alacourt at https://v2.alacourt.com/frmlogin.aspx...")

	login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

	driver.implicitly_wait(0.5/speed)
	
	cID_box = driver.find_element(by=By.NAME, 
		value="ctl00$ContentPlaceHolder$txtCusid")
	username_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId")
	pwd_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword")
	login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

	cID_box.send_keys(cID)
	username_box.send_keys(username)
	pwd_box.send_keys(pwd)

	driver.implicitly_wait(0.5/speed)
	login_button.click()

	driver.implicitly_wait(0.5/speed)

	try:
		continueLogIn = driver.find_element(by=By.NAME, 
		value="ctl00$ContentPlaceHolder$btnContinueLogin")
		continueLogIn.click()
	except:
		pass

	driver.implicitly_wait(0.5/speed)
	try:
		driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")
	except:
		pass

	driver.implicitly_wait(0.5/speed)


def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", no_records="", filed_before="", filed_after="", speed=1, no_log=False):

	time.sleep(1.5*speed)
	driver.implicitly_wait(0.5/speed)
	try:
		driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")
	except:
		pass

	if name != "":
		party_name_box = driver.find_element(by=By.ID,value="ContentPlaceHolder1_txtName")
		party_name_box.send_keys(name)
	if ssn != "":
		ssn_box.send_keys(ssn)
		ssn_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtSSN")
	if dob != "":
		date_of_birth_box.send_keys(dob)
		date_of_birth_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtDOB")

	if party_type == "plaintiffs":
		plaintiffs_select.click()
		plaintiffs_select = driver.find_element(by=By.ID, value="ContentPlaceHolder1_rdlPartyType_0")
	if party_type == "defendants":
		defendents_select.click()
		defendents_select = driver.find_element(by=By.ID, value="ContentPlaceHolder1_rdlPartyType_1")
	if party_type == "ALL":
		all_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$rdlPartyType")
		all_select.click()
	if county != "":
		county_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCounties")
		scounty = Select(county_select)
		scounty.select_by_visible_text(county)
	if division != "":
		division_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$UcddlDivisions1$ddlDivision")
		sdivision = Select(division_select)
		sdivision.select_by_visible_text(division)
	if case_year != "":
		case_year_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCaseYear")
		scase_year = Select(case_year_select)
		scase_year.select_by_visible_text(case_year)
	if no_records != "":
		no_records_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlNumberOfRecords")
		sno_records = Select(no_records_select)
		sno_records.select_by_visible_text(no_records)
	if filed_before != "":
		filed_before_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtFrom")
		filed_before_box.send_keys(sfiled_before)
	if filed_after != "":
		filed_after_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtTo")
		filed_after_box.send_keys(sfiled_after)

	# submit search
	search_button = driver.find_element(by=By.ID,value="searchButton")
	search_button.click()

	# count pages
	driver.implicitly_wait(0.5/speed)

	try:
		page_counter = driver.find_element(by=By.ID,value="ContentPlaceHolder1_dg_tcPageXofY").text
		pages = int(page_counter.strip()[-1])
	except:
	 	pages = 1

	if not no_log:
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
					if not no_log:
						click.echo(a)
			except:
				pass
		driver.implicitly_wait(0.5*speed)
		try:
			pager_select = Select(driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"))
			next_pg = int(pager_select.text) + 1
			driver.implicitly_wait(0.5/speed)
		except:
			try:
				driver.implicitly_wait(0.5/speed)
				time.sleep(0.5/speed)
				next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
				next_button.click()
			except:
				continue
	return pdflinks

def downloadPDF(driver, url, speed=1, no_log=False):
	a = driver.get(url)
	driver.implicitly_wait(1/speed)
	time.sleep(1/speed)
	if not no_log:
		click.echo(f"Downloaded {url}")

if __name__ == "__main__":
	go()
