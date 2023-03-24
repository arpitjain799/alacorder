# main 78
# sam robson



try:
    from alacorder import cal as alac
except:
    try:
        import pyximport; pyximport.install()
        from alacorder import cal as alac
    except:
        try:
            from alacorder import alac
        except:
            import alac

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
import warnings

warnings.filterwarnings('ignore')

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)


## COMMAND LINE INTERFACE

@click.group(invoke_without_command=True)
@click.version_option("78.4.5", package_name="alacorder")
@click.pass_context
def cli(ctx):
    """
    ALACORDER beta 78.4

    Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.

    """
    if ctx.invoked_subcommand is None:
        from alacorder import alacordergui
        alacordergui.loadgui()


@cli.command(help="Export data tables from archive or directory")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=alac.title(),
              help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=alac.both(), help="Path to output table (.xls, .xlsx, .csv, .json, .dta)")
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
def table(input_path, output_path, count, table, overwrite, log, no_write, no_prompt, debug, no_batch, compress): 

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
    inputs = alac.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.secho(inputs.ECHO, italic=True)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = alac.setoutputs(output_path,archive=False)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, italic=True)
    if not outputs.GOOD:
        raise Exception("Invalid output path!")
    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm(click.style("Existing file at output path will be written over! Continue?",bold=True)):
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
            pick = click.prompt(alac.pick_table_only())  # add str
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
                click.secho("Invalid table selection!", bold=True)

    # finalize config
    cf = alac.set(inputs, outputs, count=count, table=table, overwrite=overwrite, log=log, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)

    if cf.DEBUG:
        click.echo(cf)


    if cf.MAKE == "multiexport" and cf.TABLE == "all":
        o = alac.cases(cf)
    if cf.TABLE == "fees":
        o = alac.fees(cf)
    if cf.TABLE == "charges" or cf.TABLE == "disposition" or cf.TABLE == "filing":
        o = alac.charges(cf)
    if cf.TABLE == "cases":
        o = alac.cases(cf)

@cli.command(help="Create full text archive from case PDFs")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=alac.title(), help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=alac.just_archive(), help="Path to archive (.pkl.xz, .json.zip, .csv.zip, .parquet)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--dedupe / --ignore','dedupe', default=True, is_flag=True, help="Remove duplicate cases from archive outputs")
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--append', '-a', default=False, help="Append to archive at output path", is_flag=True, show_default=False)
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.option('--no-batch','-b', default=True, is_flag=True, help="Process all inputs as one batch")
@click.option('--skip','-skip', default='', type=click.Path(), help="Skip paths in archive at provided skip path")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def archive(input_path, output_path, count, overwrite, append, dedupe, log, no_write, no_batch, no_prompt, debug, compress, skip):

    # show_options_menu = False
    table = ""
    archive = True

    log = not log

    if append and skip == "":
        skip = output_path
    if append:
        overwrite = True
        no_prompt = True


    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = alac.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.secho(inputs.ECHO, italic=True)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    if append:
        overwrite = True

    # outputs - configure and log
    outputs = alac.setoutputs(output_path,archive=True)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, italic=True)

    if not outputs.GOOD:
        raise Exception("Invalid output path!")

    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")

    # skip paths in provided archive
    if skip != "" and inputs.IS_FULL_TEXT == False:
        try:
            if log or debug:
                click.secho(f"Collecting paths from archive at --skip/--append path...",italic=True)
            skip_paths = alac.read(skip)
            skip_paths = skip_paths['Path'].tolist()
        except:
            if debug:
                click.echo("Key Error when reading --skip/--append archive!")
            pass
        match_skip = pd.Series(inputs.QUEUE).map(lambda x: x not in skip_paths)
        inputs.QUEUE = inputs.QUEUE[match_skip]
        len_dif = inputs.FOUND - inputs.QUEUE.shape[0]
        if len(skip_paths) > 0 and log or debug:
                click.secho(f"Identified {len_dif} paths already in archive at path --skip/--append.")
    # append priority over overwrite
    if append and outputs.EXISTING_FILE == True:
        overwrite = True

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm("Existing file at output path will be written over! Continue?"):
                pass
            else:
                raise Exception("Existing file at output path!")


    cf = alac.set(inputs, outputs, count=count, table="", overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress, append=append)

    if debug:
        click.echo(cf)

    o = alac.archive(cf)

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
    rq = alac.readPartySearchQuery(listpath, qmax, qskip, no_log)

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
        click.secho("Starting browser... Do not close while in progress!",bold=True)

    alac.login(driver, cID=cID, uID=uID, pwd=pwd, speed=speed, no_log=no_log)

    if not no_log:
        click.secho("Authentication successful. Fetching cases via party search...",bold=True)

    for i, n in enumerate(query.index):
        if debug:
            click.secho(driver.current_url)
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                alac.login(driver, cID=cID, uID=uID, pwd=pwd, speed=speed, no_log=no_log)
        driver.implicitly_wait(4/speed)
        results = alac.party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], speed=speed, no_log=no_log, debug=debug)
        driver.implicitly_wait(4/speed)
        if len(results) == 0:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = "0"
            if not no_log:
                click.secho(f"Found no results for query: {query.NAME[n]}")
            continue
        with click.progressbar(results, show_eta=False, label=f"#{n}: {query.NAME[n]}") as bar:
            for url in bar:
                alac.downloadPDF(driver, url)
                driver.implicitly_wait(0.5/speed)
                time.sleep(2/speed)
        if not no_update:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = str(len(results))
            query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)

@cli.command(help="Mark query template sheet with cases found in archive or PDF directory input")
@click.option("--input-path", "-in", "in_path", required=True, prompt="Path to archive / PDF directory", help="Path to query template spreadsheet (.csv, .xls(x), .json)", type=click.Path())
@click.option("--output-path", "-out", "out_path", required=True, prompt="Query template spreadsheet path", type=click.Path(), help="Path to output query template spreadsheet")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
def mark(in_path, out_path, no_write=False):

    # get input text, names, dob
    input_archive = alac.read(in_path)
    mapinputs = alac.setinputs(input_archive)
    mapoutputs = alac.setoutputs()
    mapconf = alac.set(mapinputs, mapoutputs, no_write=True, no_prompt=True, overwrite=True, log=False, debug=True)

    caseinfo = alac.map(mapconf, lambda x: x, alac.getCaseNumber, alac.getName, alac.getDOB, names=['TEXT','CASE','NAME','DOB'])

    # get output cols 
    output_query = alac.readPartySearchQuery(out_path)[0]

    # get common columns
    q_columns = pd.Series(output_query.columns).astype("string")
    i_columns = pd.Series(caseinfo.columns).astype("string")
    q_columns = q_columns.str.upper().str.strip().str.replace(" ","_")
    i_columns = i_columns.str.upper().str.strip().str.replace(" ","_")
    common = q_columns.map(lambda x: x in i_columns.tolist())
    common_cols = q_columns[common]

    assert common_cols.shape[0] > 0

    output_query['RETRIEVED_ON'] = output_query.index.map(lambda x: time.time() if str(output_query.NAME[x]).replace(",","") in caseinfo.NAME.tolist() and output_query.RETRIEVED_ON[x] == "" else output_query.RETRIEVED_ON[x])
    output_query['CASES_FOUND'] = output_query['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
    output_query['RETRIEVED_ON'] = output_query['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
    if not no_write:
        with pd.ExcelWriter(out_path) as writer:
            output_query.to_excel(writer, sheet_name="MarkedQuery", engine="openpyxl")

    return output_query


@cli.command(help="Append one case text archive to another")
@click.option("--input-path", "-in", "in_path", required=True, prompt="Path to archive / PDF directory", help="Path to input archive", type=click.Path())
@click.option("--output-path", "-out", "out_path", required=True, prompt="Path to output archive", type=click.Path(), help="Path to output archive")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
def append(in_path, out_path, no_write=False):
    input_archive = alac.read(in_path)
    output_archive = alac.read(out_path)
    new_archive = pd.concat([output_archive, input_archive], ignore_index=True)
    if not no_write:
        cin = alac.setinputs(input_archive)
        cout = alac.setoutputs(out_path)
        conf = alac.set(cin, cout)
        conf.OVERWRITE = True
        conf.NO_PROMPT = True
        alac.write(conf, new_archive)
    return new_archive


if __name__ == "__main__":
    cli()