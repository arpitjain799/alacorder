# main 77
# sam robson


import warnings
from alacorder import alac as cal
import os
import sys
import math
import click
import pandas as pd
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options 

warnings.filterwarnings('ignore')

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)


## COMMAND LINE INTERFACE

@click.group()
@click.version_option("77.6", package_name="alacorder")
def cli():
    """
    ALACORDER beta 77.6

    Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.

    """
    pass

@cli.command(help="Export data tables from archive or directory")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=cal.title(),
              help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=cal.both(), help="Path to output table (.xls, .xlsx, .csv, .json, .dta)")
@click.option('--table', '-t', help="Table export choice (cases, fees, charges, disposition, filing, or all)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (Excel files not supported)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-prompt','-s', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--no-batch','-b', default=True, is_flag=True, help="Process all inputs as one batch")
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def table(input_path, output_path, count, table, overwrite, log, no_write, no_prompt, debug, no_batch, compress): # dropped dedupe, archive 

    ogtable = table
    archive = False
    show_options_menu = False

    log = not log 

    show_options_menu = True if no_prompt == False and overwrite == False and log == True and no_write == False and no_prompt == False and debug == False and no_batch == False and compress == False else False

    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = cal.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.echo(inputs.ECHO)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = cal.setoutputs(output_path,archive=False)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, fg='yellow', italic=True)
    if not outputs.GOOD:
        raise Exception("Invalid output path!")
    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm(click.style("Existing file at output path will be written over! Continue?",fg='bright_yellow',bold=True)):
                pass
            else:
                raise Exception("Existing file at output path!")

    # prompt table
    if outputs.MAKE == "multiexport" and table != "cases" and table != "fees" and table != "charges" and table != "disposition" and table != "filing":
        table = "all"
    if outputs.MAKE == "singletable" and table != "cases" and table != "fees" and table != "charges" and table != "disposition" and table != "filing":
        if no_prompt:
            raise Exception("Invalid/missing table selection!")
        else:
            pick = click.prompt(cal.pick_table_only())  # add str
            if pick == "B" or pick == "cases":
                table = "cases"
            elif pick == "C" or pick == "fees":
                table = "fees"
            elif pick == "D" or pick == "charges":
                table = "charges"
            elif pick == "E" or pick == "disposition":
                table = "disposition"
            elif pick == "F" or pick == "filing":
                table = "filing"
            else:
                click.secho("Invalid table selection!", fg='red', bold=True)

    # finalize config
    cf = cal.set(inputs, outputs, count=count, table=table, overwrite=overwrite, log=log, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)


    if cf.MAKE == "multiexport" and cf.TABLE == "all":
        o = cal.cases(cf)
    if cf.TABLE == "fees":
        o = cal.fees(cf)
    if cf.TABLE == "charges" or cf.TABLE == "disposition" or cf.TABLE == "filing":
        o = cal.charges(cf)
    if cf.TABLE == "cases":
        o = cal.cases(cf)

@cli.command(help="Create full text archive from case PDFs")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=cal.title(), help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt="cal.just_archive()", help="Path to archive (.pkl.xz, .json.zip, .csv.zip, .parquet)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--dedupe / --ignore','dedupe', default=True, is_flag=True, help="Remove duplicate cases from archive outputs")
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.option('--no-batch','-b', default=True, is_flag=True, help="Process all inputs as one batch")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def archive(input_path, output_path, count, overwrite, dedupe, log, no_write, no_batch, no_prompt, debug, compress):

    # show_options_menu = False
    table = ""
    archive = True

    log = not log


    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = cal.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.echo(inputs.ECHO)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = cal.setoutputs(output_path,archive=True)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, fg='yellow', italic=True)

    if not outputs.GOOD:
        raise Exception("Invalid output path!")

    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")


    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm("Existing file at output path will be written over! Continue?"):
                pass
            else:
                raise Exception("Existing file at output path!")

    cf = cal.set(inputs, outputs, count=count, table="", overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)

    if debug:
        click.echo(cf)

    o = cal.archive(cf)

# fetch

@cli.command(help="Fetch cases from Alacourt.com with input query spreadsheet headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE.")
@click.option("--input-path", "-in", "listpath", required=True, prompt="Path to query table", help="Path to query table/spreadsheet (.xls, .xlsx, .csv, .json)", type=click.Path())
@click.option("--output-path", "-out", "path", required=True, prompt="PDF download path", type=click.Path(), help="Desired PDF output directory")
@click.option("--customer-id", "-c","cID", required=True, prompt="Alacourt Customer ID", help="Customer ID on Alacourt.com")
@click.option("--user-id", "-u","uID", required=True, prompt="Alacourt User ID", help="User ID on Alacourt.com")
@click.option("--password", "-p","pwd", required=True, prompt="Alacourt Password", help="Password on Alacourt.com", hide_input=True)
@click.option("--max", "-max","qmax", required=False, type=int, help="Maximum queries to conduct on Alacourt.com",default=0)
@click.option("--skip", "-skip", "qskip", required=False, type=int, help="Skip entries at top of query file",default=0)
@click.option("--speed", default=1, type=float, help="Speed multiplier")
@click.option("--no-log","-nl", is_flag=True, default=False, help="Do not print logs to console")
@click.option("--no-update","-w", is_flag=True, default=False, help="Do not update query template after completion")
@click.option("--ignore-complete","-g", is_flag=True, default=False, help="Ignore initial completion status in query template")
@click.option("--debug","-d", is_flag=True, default=False, help="Print detailed runtime information to console")
def fetch(listpath, path, cID, uID, pwd, qmax, qskip, speed, no_log, no_update, ignore_complete, debug):
    """
    Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to fetch.
    
    USE WITH CHROME (TESTED ON MACOS) 
    KEEP YOUR COMPUTER POWERED ON AND CONNECTED TO THE INTERNET.
    
    Args:
        listpath: (path-like obj) Query template path / input path
        path: (path-like obj) Path to output/downloads directory 
        cID (str): Alacourt.com Customer ID
        uID (str): Alacourt.com User ID
        pwd (str): Alacourt.com Password
        qmax (int, optional): Max queries to pull from inputs
        qskip (int, optional): Skip top n queries in inputs
        speed (int, optional): Fetch rate multiplier
        no_log (bool, optional): Do not print logs to console
        no_update (bool, optional): Do not update input query file with completion status
        debug (bool, optional): Print detailed logs to console

    Returns:
        [driver, query_out, query_writer]:
            driver[0]: Google Chrome WebDriver() object 
            query_out[1]: (pd.Series) Fetchr queue
            query_writer[2]: (pd.DataFrame) Updated input query file
    """
    if debug:
        sys.tracebacklimit = 10
    rq = cal.readPartySearchQuery(listpath, qmax, qskip, no_log)

    query = pd.DataFrame(rq[0]) # for fetchr - only search columns
    query_writer = pd.DataFrame(rq[1]) # original sheet for write completion 
    incomplete = query.RETRIEVED_ON.map(lambda x: True if x == "" else False)
    query = query[incomplete]

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
        click.secho("Starting browser... Do not close while in progress!",fg='bright_yellow',bold=True)

    login(driver, cID, uID, pwd, speed)

    if not no_log:
        click.secho("Authentication successful. Fetching cases via party search...",fg='bright_green',bold=True)

    for i, n in enumerate(query.index):
        if debug:
            click.secho(driver.current_url)
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                login(driver, cID, uID, pwd, speed, no_log)
        driver.implicitly_wait(4/speed)
        results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], speed=speed, no_log=no_log)
        driver.implicitly_wait(4/speed)
        if len(results) == 0:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = "0"
            if not no_log:
                click.secho(f"Found no results for query: {query.NAME[n]}")
            continue
        with click.progressbar(results, show_eta=False, label=f"#{n}: {query.NAME[n]}") as bar:
            for url in bar:
                downloadPDF(driver, url)
                driver.implicitly_wait(0.5/speed)
                time.sleep(2/speed)
        if not no_update:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = str(len(results))
            query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)


def login(driver, cID, username, pwd, speed, no_log=False, path=""):
    """
    Login to Alacourt.com using (driver) and auth (cID, username, pwd) at (speed) for browser download to directory at (path)
    
    Args:
        driver (WebDriver): Google Chrome selenium.WebDriver() object
        cID (str): Alacourt.com Customer ID
        username (str): Alacourt.com User ID
        pwd (str): Alacourt.com Password
        speed (TYPE): Fetch rate multiplier
        no_log (bool, optional): Do not print logs
        path (str, optional): Set browser download path 
    
    Returns:
        driver (WebDriver): Google Chrome selenium.WebDriver() object
    """
    if driver == None:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {
            "download.default_directory": path, #Change default directory for downloads
            "download.prompt_for_download": False, #To auto download the file
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
        })
        driver = webdriver.Chrome(options=options)

    if not no_log:
        click.echo("Connecting to Alacourt...")

    login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

    if not no_log:
        click.echo("Logging in...")

    driver.implicitly_wait(0.5/speed)
    
    cID_box = driver.find_element(by=By.NAME, 
        value="ctl00$ContentPlaceHolder$txtCusid")
    username_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId")
    pwd_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword")
    login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

    cID_box.send_keys(cID)
    username_box.send_keys(username)
    pwd_box.send_keys(pwd)

    driver.implicitly_wait(1/speed)

    login_button.click()

    driver.implicitly_wait(1/speed)

    try:
        continueLogIn = driver.find_element(by=By.NAME, 
        value="ctl00$ContentPlaceHolder$btnContinueLogin")
        continueLogIn.click()
    except:
        pass


    driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

    if not no_log:
        click.secho("Successfully connected and logged into Alacourt!",fg='bright_green', bold=True)

    driver.implicitly_wait(0.5/speed)

    return driver

def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", filed_before="", filed_after="", speed=1, no_log=False, debug=False):
    """
    Collect PDFs via SJIS Party Search Form from Alacourt.com
    Returns list of URLs for downloadPDF() to download
    
    Args:
        driver (WebDriver): selenium/chrome web driver object 
        name (str, optional): Name (LAST FIRST)
        party_type (str, optional): "Defendants" | "Plaintiffs" | "ALL"
        ssn (str, optional): Social Security Number
        dob (str, optional): Date of Birth
        county (str, optional): County
        division (str, optional): "All Divisions"
            "Criminal Only"
            "Civil Only"
            "CS - CHILD SUPPORT"
            "CV - CIRCUIT - CIVIL"
            "CC - CIRCUIT - CRIMINAL"
            "DV - DISTRICT - CIVIL"
            "DC - DISTRICT - CRIMINAL"
            "DR - DOMESTIC RELATIONS"
            "EQ - EQUITY-CASES"
            "MC - MUNICIPAL-CRIMINAL"
            "TP - MUNICIPAL-PARKING"
            "SM - SMALL CLAIMS"
            "TR - TRAFFIC"
        case_year (str, optional): YYYY
        filed_before (str, optional): M/DD/YYYY
        filed_after (str, optional): M/DD/YYYY
        speed (int, optional): Fetch rate multiplier
        no_log (bool, optional): Do not print logs.
        debug (bool, optional): Print detailed logs.
    
    Returns:
        URL list to PDFs
    """
    speed = speed * 1.5


    if "frmIndexSearchForm" not in driver.current_url:
        driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

    driver.implicitly_wait(5/speed)


    # connection error 
    try:
        party_name_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtName")
    except selenium.common.exceptions.NoSuchElementException:
        if not no_log:
            click.secho("Connection error. Attempting reconnection...", fg='red', bold=True)
        driver.refresh()
        driver.implicitly_wait(10/speed)
        party_name_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtName")
        if not no_log:
            click.secho("Successfully connected and logged into Alacourt!", fg='bright_green', bold=True)

    # field search

    if name != "":
        party_name_box.send_keys(name)
    if ssn != "":
        ssn_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtSSN")
        ssn_box.send_keys(ssn)
    if dob != "":
        date_of_birth_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtDOB")
        date_of_birth_box.send_keys(dob)
    if party_type != "":
        party_type_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$rdlPartyType")
        pts = Select(party_type_select)
        if party_type == "plaintiffs":
            pts.select_by_visible_text("Plaintiffs")
        if party_type == "defendants":
            pts.select_by_visible_text("Defendants")
        if party_type == "all":
            pts.select_by_visible_text("ALL")

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
    no_records_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlNumberOfRecords")
    sno_records = Select(no_records_select)
    sno_records.select_by_visible_text("1000")
    if filed_before != "":
        filed_before_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtFrom")
        filed_before_box.send_keys(filed_before)
    if filed_after != "":
        filed_after_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtTo")
        filed_after_box.send_keys(filed_after)

    driver.implicitly_wait(1/speed)

    # submit search
    search_button = driver.find_element(by=By.ID,value="searchButton")

    driver.implicitly_wait(1/speed)
    try:
        search_button.click()
    except:
        driver.implicitly_wait(5/speed)
        time.sleep(5)

    if debug:
        click.echo("Submitted party search form...")

    driver.implicitly_wait(1/speed)

    # count pages
    try:
        page_counter = driver.find_element(by=By.ID,value="ContentPlaceHolder1_dg_tcPageXofY").text
        pages = int(page_counter.strip()[-1])

    except:
        pages = 1

    # count results
    try:
        results_indicator = driver.find_element(by=By.ID, value="ContentPlaceHolder1_lblResultCount")
        results_count = int(results_indicator.text.replace("Search Results: ","").replace(" records returned.","").strip())
        if results_count == 1000 and debug or no_log:
            click.echo(f"Max records (1000) returned for party {name}!")
    except:
        pass

    if debug:
        click.echo(f"Found {results_count} results, fetching URLs and downloading PDFs...")

    if debug:
        click.echo(pages)

    # get PDF links from each page
    pdflinks = []
    i = 0
    for i in range(0,pages):
        driver.implicitly_wait(0.5/speed)
        hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
        for x in hovers:
            try:
                a = x.get_attribute("href")
                if "PDF" in a:
                    pdflinks.append(a)
            except:
                pass
        driver.implicitly_wait(0.5/speed)
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

def downloadPDF(driver, url, speed=1, no_log=False, cID="", uID="", pwd=""):
    if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
        login(driver, cID, uID, pwd, speed, no_log)
    a = driver.get(url)
    driver.implicitly_wait(0.5/speed)


if __name__ == "__main__":
    cli()