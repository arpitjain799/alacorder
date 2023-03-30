"""
 alacorder on polars
 ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌
 ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││
 ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘
 Dependencies: selenium, polars, pandas, PyMuPDF, PySimpleGUI, click, tqdm, xlsxwriter, openpyxl, xlsx2csv
 (c) 2023 Sam Robson <sbrobson@crimson.ua.edu>
"""

name = "ALACORDER"
version = "79.1.5"
long_version = "partymountain"

AUTOLOAD_GUI = True

import click, fitz, os, sys, time, glob, inspect, math, re, warnings, xlsxwriter, threading, platform, tqdm, selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import polars as pl
import pandas as pd
fname = f"{name} {version}"
fshort_name = f"{name} {version.rsplit('.')[0]}"
warnings.filterwarnings('ignore')
pl.Config.set_tbl_rows(20)
pl.Config.set_fmt_str_lengths(100)
pl.Config.set_tbl_cols(10)
pl.Config.set_tbl_formatting('UTF8_FULL_CONDENSED')
pd.set_option("mode.chained_assignment", None)
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

#   #   #   #      GRAPHICAL USER INTERFACE    #   #   #   #

def loadgui():
     """
     Load PySimpleGUI tk graphical interface 
     """
     import PySimpleGUI as sg
     psys = platform.system()
     plat = platform.platform()
     if "Darwin" in (plat, psys) or "macOS" in (plat, psys):
          inferred_platform = "mac"
     elif "Windows" in (plat, psys):
          inferred_platform = "windows"
     elif "Linux" in (plat, psys):
          inferred_platform = "linux"
     else:
          inferred_platform = None
     if inferred_platform == "mac":
          HEADER_FONT = "Default 22"
          LOGO_FONT = "Courier 20"
          ASCII_FONT = "Courier 18"
          BODY_FONT = "Default 12"
          WINDOW_RESIZE = False
          WINDOW_SIZE = [480, 500]
     else:
          HEADER_FONT = "Default 14"
          ASCII_FONT = "Courier 8"
          LOGO_FONT = "Courier 15"
          BODY_FONT = "Default 10"
          WINDOW_RESIZE = True
          WINDOW_SIZE = [500, 540]
     sg.theme("DarkBlack")
     sg.set_options(font=BODY_FONT)
     fetch_layout = [
           [sg.Text("""Collect case PDFs in bulk from Alacourt.""",font=HEADER_FONT,pad=(5,5))],
           [sg.Text("""Requires Google Chrome. Use column headers NAME, PARTY_TYPE, SSN,\nDOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel\nspreadsheet to submit a list of queries for Alacorder to scrape. Each column\ncorresponds to a search field in Party Search.""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(tooltip="Existing query template (.xlsx)", size=[22,10], key="SQ-INPUTPATH-",focus=True), sg.FileBrowse(button_text="Select File", button_color=("white","black")), sg.Button(button_text="New Query", button_color=("white","black"),k="NEWQUERY", enable_events=True)],
           [sg.Text("Output Path: "), sg.InputText(tooltip="PDF download destination folder", size=[29,10], key="SQ-OUTPUTPATH-"), sg.FolderBrowse(button_text="Select Folder", button_color=("white","black"))],
           [sg.Text("Max queries: "), sg.Input(key="SQ-MAX-", default_text="0", size=[5,1]),sg.Text("Skip from top: "), sg.Input(key="SQ-SKIP-", default_text="0",size=[5,1])],
           [sg.Text("Alacourt.com Credentials", font=BODY_FONT)],
           [sg.Text("Customer ID:"), sg.Input(key="SQ-CUSTOMERID-",size=(13,1)), sg.Text("User ID:"), sg.Input(key="SQ-USERID-",size=(13,1))],
           [sg.Text("Password:"), sg.InputText(key="SQ-PASSWORD-",password_char='*',size=(15,1))],
           [sg.Button("Start Query",key="SQ",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]]
     archive_layout = [
           [sg.Text("""Create full text archives from a\ndirectory with PDF cases.""", font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""Case text archives require a fraction of the storage capacity and processing\ntime used to process PDF directories. Before exporting your data to tables,\ncreate an archive with supported file extensions .pkl.xz, .json, .csv, and\n.parquet. Once archived, use your case text archive as an\ninput for multitable or single table export.""", pad=(5,5))],
           [sg.Text("Input Directory: "), sg.InputText(tooltip="PDF directory or full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)",size=[25,1], key="MA-INPUTPATH-",focus=True), sg.FolderBrowse(button_text="Select Folder", button_color=("white","black"))],
           [sg.Text("Output Path: "), sg.InputText(tooltip="Output archive file path (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[39,1], key="MA-OUTPUTPATH-")],
           [sg.Text("Skip Cases From: "), sg.Input(tooltip="Skip all input cases found in PDF directory or archive (.parquet, .pkl, .pkl.xz, .json, .csv)", key="MA-SKIP-",size=[24,1],pad=(0,10))],
           [sg.Text("Max cases: "), sg.Input(key="MA-COUNT-", default_text="0", size=[5,1]), sg.Checkbox("Allow Overwrite",default=True,key="MA-OVERWRITE-"), sg.Checkbox("Try to Append",key="MA-APPEND-", default=False)],
           [sg.Button("Make Archive",button_color=("white","black"),key="MA",enable_events=True,bind_return_key=True, disabled_button_color=("grey","black"), mouseover_colors=("grey","black"), pad=(10,10))]] # "MA"
     append_layout = [
           [sg.Text("""Append case text archive with the contents\nof a case directory or archive.""", font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""Case text archives require a fraction of the storage capacity and\nprocessing time used to process PDF directories. Before exporting\nyour data to tables, create an archive with a supported file\nextension (.parquet, .json, .csv, .pkl.xz). Once archived, use\nyour case text archive as an input for table export.""", pad=(5,5))],
           [sg.Text("To Append: "), sg.InputText(tooltip="PDF Directory or full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[30,10], key="AA-INPUTPATH-",focus=True), sg.FileBrowse(button_text="Select File", button_color=("white","black"))],
           [sg.Text("To Be Appended: "), sg.InputText(tooltip="Destination full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[26,10], key="AA-OUTPUTPATH-"), sg.FileBrowse(button_text="Select File", button_color=("white","black"))],
           [sg.Button("Append Archives", key="AA",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"), bind_return_key=True)]] # "AA"
     table_layout = [
           [sg.Text("""Export data tables from\ncase archive or directory.""", font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""Alacorder processes case detail PDFs and case text archives into data\ntables suitable for research purposes. Export an Excel spreadsheet\nwith detailed cases information (cases), fee sheets (fees), and\ncharges information (charges), or select a table\nchoice to export to a single-table format.""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(tooltip="PDF directory or full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[28,10], key="TB-INPUTPATH-",focus=True), sg.FolderBrowse(button_text="Select Folder", button_color=("white","black"))],
           [sg.Text("Output Path: "), sg.InputText(tooltip="Multitable export (.xlsx, .xls) or single-table export (.xlsx, .xls, .json, .csv, .dta, .parquet)", size=[39,10], key="TB-OUTPUTPATH-")],
           [sg.Radio("All Tables (.xlsx, .xls)", "TABLE", key="TB-ALL-", default=True), 
                 sg.Radio("Cases", "TABLE", key="TB-CASES-", default=False), 
                 sg.Radio("Charges", "TABLE", key="TB-CHARGES-", default=False), 
                 sg.Radio("Fees","TABLE",key="TB-FEES-",default=False)],
           [sg.Text("Max cases: "), sg.Input(key="TB-COUNT-", default_text="0", size=[5,1]), sg.Checkbox("Allow Overwrite", key="TB-OVERWRITE-", default=True), sg.Checkbox("Compress", key="TB-COMPRESS-")],
           [sg.Button("Export Table",key="TB",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]] # "TB"
     about_layout = [
           [sg.Text(f""" ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌\n ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││\n ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘\n  {version}""",font=ASCII_FONT, pad=(5,5))],
           [sg.Text("Alacorder retrieves and processes\nAlacourt case detail PDFs into\ndata tables and archives.",font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""1.  fetch - Retrieve case detail PDFs in bulk from Alacourt.\n2.  archive - Create full text archives from PDF directory.\n3.  table - Export data tables from case archive or directory.\n4.  append - Append contents of one archive to another.""", font=BODY_FONT)],
           [sg.Text("""View documentation, source code, and latest updates at\ngithub.com/sbrobson959/alacorder.\n\n© 2023 Sam Robson""", font=BODY_FONT)]
           ] # "ABOUT"
     tabs = sg.TabGroup(expand_x=True, expand_y=False, size=[0,0], font="Courier",layout=[[sg.Tab("fetch", layout=fetch_layout, pad=(2,2))],
                [sg.Tab("archive", layout=archive_layout, pad=(2,2))],            
                [sg.Tab("table", layout=table_layout, pad=(2,2))],
                [sg.Tab("append", layout=append_layout, pad=(2,2))],
                [sg.Tab("about", layout=about_layout, pad=(2,2))]])
     layout = [[sg.Text(fshort_name,font=LOGO_FONT, pad=(5,5))],[tabs],
              [sg.ProgressBar(100, size=[5,10], expand_y=False, orientation='h', expand_x=True, key="PROGRESS", bar_color="black")],
              [sg.Multiline(expand_x=True,expand_y=True,background_color="black",reroute_stdout=True,pad=(5,5),font="Courier 11",write_only=True,autoscroll=True,no_scrollbar=True,size=[None,4],border_width=0)]]
     window = sg.Window(title=name, layout=layout, grab_anywhere=True, resizable=WINDOW_RESIZE, size=WINDOW_SIZE)
     while True:
           event, values = window.read()
           if event in ("Exit","Quit",sg.WIN_CLOSED):
                 window.close()
                 break
           elif "TOTAL" in event and "PROGRESS" in event:
               window['PROGRESS'].update(max=values[event],current_count=0)
           elif "PROGRESS" in event and "TOTAL" not in event:
               window["PROGRESS"].update(current_count=values[event])
           elif "COMPLETE" in event:
               print("Alacorder completed the task.")
               window['AA'].update(disabled=False)
               window['SQ'].update(disabled=False)
               window['MA'].update(disabled=False)
               window['TB'].update(disabled=False)
               window['MA'].update(disabled=False)
               window['PROGRESS'].update(current_count=0, max=100)
               sg.popup("Alacorder completed the task.")
               continue
           elif event == "NEWQUERY":
                 if window['SQ-INPUTPATH-'].get() == "":
                      sg.popup("To create empty query template, enter file output path (extension must be .xlsx) in Input Path, then press the New Query button to try again.")
                 else:
                      if makeQueryTemplate(window['SQ-INPUTPATH-'].get()):
                           sg.popup("Alacorder created query template.")
                      else:
                           sg.popup("Enter valid path with .xlsx extension in Input Path box and try again.")
           elif event == "TB":
                 if window["TB-INPUTPATH-"].get() == "" or window["TB-OUTPUTPATH-"].get() == "":
                    sg.popup("Check configuration and try again.")
                 if bool(window["TB-ALL-"]) == True:
                         tabl = "all"
                 elif bool(window["TB-CASES-"]) == True:
                         tabl = "cases"
                 elif bool(window["TB-CHARGES-"]) == True:
                         tabl = "charges"
                 elif bool(window["TB-FEES-"]) == True:
                         tabl = "fees"
                 else:
                         continue
                 try:
                         try:
                               count = int(window['TB-COUNT-'].get().strip())
                         except:
                               count = 0
                         try:
                               cf = set(window['TB-INPUTPATH-'].get(), window['TB-OUTPUTPATH-'].get(), count=count,table=tabl,overwrite=window['TB-OVERWRITE-'].get(),compress=window['TB-COMPRESS-'].get(),no_prompt=True, debug=False,archive=False,window=window)
                         except:
                               print("Check configuration and try again.")
                               window['TB'].update(disabled=False)
                               continue
                         window['TB'].update(disabled=True)
                         threading.Thread(target=init,args=(cf,window), daemon=True).start()
                         continue
                 except:
                         print("Check configuration and try again.")
                         window['TB'].update(disabled=False)
                         continue
           elif event == "MA":
                  if window["MA-INPUTPATH-"].get() == "" or window["MA-OUTPUTPATH-"].get() == "":
                        sg.popup("Check configuration and try again.")
                        window['MA'].update(disabled=False)
                        continue
                  try:
                        count = int(window['MA-COUNT-'].get().strip())
                  except:
                        count = 0
                  try:
                  		aa = set(window['MA-INPUTPATH-'].get(),window['MA-OUTPUTPATH-'].get(),count=count, archive=True,overwrite=window['MA-OVERWRITE-'].get(), append=window['MA-APPEND-'].get(), no_prompt=True,window=window)
                  except:
                        sg.popup("Check configuration and try again.")
                        window['MA'].update(disabled=False)
                        continue
                  window['MA'].update(disabled=True)
                  threading.Thread(target=archive, args=(aa, window), daemon=True).start()
                  continue
           elif event == "SQ":
                 if window["SQ-INPUTPATH-"].get() == "" or window["SQ-OUTPUTPATH-"].get() == "":
                         sg.popup("Check configuration and try again.")
                 try:
                         pwd = window["SQ-PASSWORD-"].get()
                         try:
                               sq_max = int(window['SQ-MAX-'].get().strip())
                               sq_skip = int(window['SQ-SKIP-'].get().strip())
                         except:
                               sq_max = 0
                               sq_skip = 0
                         window['SQ'].update(disabled=True)
                         threading.Thread(target=fetch, args=(window['SQ-INPUTPATH-'].get(),window['SQ-OUTPUTPATH-'].get(),window['SQ-CUSTOMERID-'].get(),window['SQ-USERID-'].get(),pwd,sq_max,sq_skip,False,False,False,window), daemon=True).start()
                         continue
                 except:
                         print("Check configuration and try again.")
                         window['SQ'].update(disabled=False)
                         continue
           elif event == "AA":
                 if window["AA-INPUTPATH-"].get() == "" or window["AA-OUTPUTPATH-"].get() == "":
                         sg.popup("Check configuration and try again.")
                         continue
                 try:
                         window['AA'].update(disabled=True)
                         threading.Thread(target=append_archive, args=(window['AA-INPUTPATH-'].get(),window['AA-OUTPUTPATH-'].get()), kwargs={'window':window},daemon=True).start()
                         continue
                 except:
                         print("Check configuration and try again.")
                         window['AA'].update(disabled=False)
                         continue
           else:
                 pass

#   #   #   #       COMMAND LINE INTERFACE     #   #   #   #

@click.group(invoke_without_command=AUTOLOAD_GUI, context_settings=CONTEXT_SETTINGS)
@click.version_option(f"{version}", package_name=f"{name} {long_version}")
@click.pass_context
def cli(ctx):
     """
     ALACORDER 79 (partymountain) 
     by Sam Robson
     """
     if AUTOLOAD_GUI and ctx.invoked_subcommand == None:
        loadgui()

@cli.command(name="start", help="Launch graphical user interface")
def cli_start():
     loadgui()

@cli.command(name="append", help="Append one case text archive to another")
@click.option("--input-path", "-in", "in_path", required=True, prompt="Path to archive / PDF directory", help="Path to input archive", type=click.Path())
@click.option("--output-path", "-out", "out_path", required=True, prompt="Path to output archive", type=click.Path(), help="Path to output archive")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
def cli_append(in_path, out_path, no_write=False):
    """Append one case text archive to another
    
    Args:
        in_path (Path|DataFrame): Path to input archive / PDF directory
        out_path (Path): Path to output archive
        no_write (bool, optional): Do not export to output path
    
    Returns:
        DataFrame: Appended archive
    """
    print("Appending archives...")
    conf = set(in_path, out_path, append=True, archive=True, no_prompt=True, overwrite=True, no_write=no_write)
    input_archive = read(in_path).to_pandas()
    output_archive = read(out_path).to_pandas()
    new_archive = pl.from_pandas(pd.concat([output_archive, input_archive], ignore_index=True))
    if not no_write:
        write(conf, new_archive)
    return new_archive

@cli.command(name="fetch", help="Fetch cases from Alacourt.com with input query spreadsheet headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE.")
@click.option("--input-path", "-in", "listpath", required=True, prompt="Path to query table", help="Path to query table/spreadsheet (.xls, .xlsx)", type=click.Path())
@click.option("--output-path", "-out", "path", required=True, prompt="PDF download path", type=click.Path(), help="Desired PDF output directory")
@click.option("--customer-id", "-c","cID", required=True, prompt="Alacourt Customer ID", help="Customer ID on Alacourt.com")
@click.option("--user-id", "-u","uID", required=True, prompt="Alacourt User ID", help="User ID on Alacourt.com")
@click.option("--password", "-p","pwd", required=True, prompt="Alacourt Password", help="Password on Alacourt.com", hide_input=True)
@click.option("--max", "-max","qmax", required=False, type=int, help="Maximum queries to conduct on Alacourt.com",default=0)
@click.option("--skip", "-skip", "qskip", required=False, type=int, help="Skip entries at top of query file",default=0)
@click.option("--no-mark","-n","no_update", is_flag=True, default=False, help="Do not update query template after completion")
@click.option("--debug","-d", is_flag=True, default=False, help="Print detailed runtime information to console")
def cli_fetch(listpath, path, cID, uID, pwd, qmax, qskip, no_update, debug=False):
    """
    Fetch cases from Alacourt.com with input query spreadsheet headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE.
    Args:
        listpath (str): Path to query table/spreadsheet (.xls, .xlsx)
        path (str): Path to PDF output directory
        cID (str): Customer ID on Alacourt.com
        uID (str): User ID on Alacourt.com
        pwd (str): Password on Alacourt.com
        qmax (int): Maximum queries to conduct on Alacourt.com
        qskip (int): Skip entries at top of query file
        no_update (bool): Do not update query template after completion
        debug (bool): Print detailed runtime information to console
    """
    if debug:
        sys.tracebacklimit = 10
        pl.Config.set_verbose(True)
    else:
        sys.tracebacklimit = 1
        pl.Config.set_verbose(False)

    rq = readPartySearchQuery(listpath, qmax, qskip)

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
    click.secho("Starting browser... Do not close while in progress!",bold=True)

    login(driver, cID=cID, uID=uID, pwd=pwd)

    click.secho("Authentication successful. Fetching cases via party search...",bold=True)

    for i, n in enumerate(query.index):
        if debug:
            click.secho(driver.current_url)
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                login(driver, cID=cID, uID=uID, pwd=pwd)
        driver.implicitly_wait(4)
        results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], debug=debug)
        driver.implicitly_wait(4)
        if len(results) == 0:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = "0"
            click.secho(f"Found no results for query: {query.NAME[n]}")
            continue
        for url in tqdm.rich.tqdm(results, desc=f"#{n}: {query.NAME[n]}"):
            downloadPDF(driver, url)
            driver.implicitly_wait(0.5)
            time.sleep(1)
        if not no_update:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = str(len(results))
            query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)

@cli.command(name="table", help="Export data tables from archive or directory")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt="Input Path", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt="Output Path")
@click.option('--table', '-t', default='', help="Table (all, cases, fees, charges)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (Excel files not supported)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-prompt','-s', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path")
@click.option('--debug','-d', default=False, is_flag=True, help="Print debug logs to console")
@click.version_option(package_name='alacorder', prog_name=name, message='%(prog)s beta %(version)s')
def cli_table(input_path, output_path, count, table, overwrite, no_write, no_prompt, debug, compress): 
    """
    Write data tables to output path from archive or directory input.
    
    Args:
        input_path (str): PDF directory or archive input
        output_path (str): Path to table output
        count (int): Total cases to pull from input
        table (str): Table (all, cases, fees, charges)
        overwrite (bool): Overwrite existing files at output path
        no_write (bool): Do not export to output path
        no_prompt (bool): Skip user input / confirmation prompts
        debug (bool): Print verbose logs to console
        compress (bool): Compress exported file (archives compress with or without flag
    """
    cf = set(input_path, output_path, count=count, table=table, overwrite=overwrite,  no_write=no_write, no_prompt=no_prompt, debug=debug, compress=compress)
    if cf['DEBUG']:
        print(cf)
    o = init(cf)
    return o

@cli.command(name="archive", help="Create full text archive from case PDFs")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt="PDF directory or archive input")
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt="Path to archive output")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path")
@click.option('--no-prompt', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print verbose logs to console")
@click.version_option(package_name=name.lower(), prog_name=name.upper(), message='%(prog)s %(version)s')
def cli_archive(input_path, output_path, count, overwrite, no_write, no_prompt, debug, compress):
    """
    Write a full text archive from a directory of case detail PDFs.
    
    Args:
        input_path (str): PDF directory or archive input
        output_path (str): Path to archive output
        count (int): Total cases to pull from input
        overwrite (bool): Overwrite existing files at output path
        no_write (bool): Do not export to output path
        no_prompt (bool): Skip user input / confirmation prompts
        debug (bool): Print verbose logs to console for developers
        compress (bool): Compress exported file (archives compress with or without flag)
    
    """
    cf = set(input_path, output_path, archive=True, count=count, overwrite=overwrite, no_write=no_write, no_prompt=no_prompt, debug=debug, compress=compress)
    if debug:
        click.echo(cf)
    o = archive(cf)
    return o

def set(inputs, outputs=None, count=0, table='', archive=False, no_prompt=True, debug=False, overwrite=False, no_write=False, fetch=False, cID='', uID='', pwd='', qmax=0, qskip=0, append=False, compress=False, window=None, force=False, no_update=False, now=False):
     """
     Check inputs and outputs and return a configuration object for Alacorder table parser functions to receive as parameter and complete task, or set `now = True` to run upon set() call.

     Args:
         inputs (Path | DataFrame): PDF directory, query, archive path, or DataFrame input
         outputs (Path | DataFrame, optional): Path to archive, directory, or file output
         count (int, optional): Max cases to pull from input
         table (str, optional): Table (all, cases, fees, charges)
         archive (bool, optional): Write a full text archive from a directory of case detail PDFs
         no_prompt (bool, optional): Skip user input / confirmation prompts
         debug (bool, optional): Print verbose logs to console for developers
         overwrite (bool, optional): Overwrite existing files at output path
         no_write (bool, optional): Do not export to output path
         no_update (bool, optional): Do not mark input query when fetching cases
         fetch (bool, optional): Retrieve case detail PDFs from Alacourt.com
         cID (str, optional): Customer ID on Alacourt.com
         uID (str, optional): User ID on Alacourt.com
         pwd (str, optional): Password on Alacourt.com
         qmax (int, optional): Maximum queries to conduct on Alacourt.com
         qskip (int, optional): Skip entries at top of query file
         append (bool, optional): Append one archive to another
         compress (bool, optional): Compress outputs 
         force (bool, optional): Do not raise exceptions
         now (bool, optional): Start Alacorder upon successful configuration
     """
     # flag checks
     good = True
     outputs = None if no_write else outputs
     no_write = True if outputs == None else no_write
     found = 0

     # check output
     if no_write:
          outputext = "none"
          existing_output = False
     elif os.path.isdir(outputs):
          outputext = "directory"
          existing_output = False
     elif os.path.isfile(outputs):
          assert overwrite or append # Existing file at output path!
          outputext = os.path.splitext(outputs)[1]
          existing_output = True
     else:
          outputext = os.path.splitext(str(outputs))[1]
          existing_output = False

     # flag checks - compression
     if outputext == ".zip":
          outputs, outputext = os.path.splitext(outputs)
     if outputext in (".xz",".parquet",".zip"):
          compress = True

     #flag checks - output extension
     support_multitable = True if outputext in (".xls",".xlsx","none") else False
     support_singletable = True if outputext in (".xls",".xlsx","none",".json",".dta",".parquet", ".csv") else False
     support_archive = True if outputext in (".xls",".xlsx",".csv",".parquet",".zip",".json",".dta",".pkl",".xz",".zip","none") else False
     compress = False if outputext in (".xls",".xlsx","none") else compress
     assert force or outputext in (".xls",".xlsx",".csv",".parquet",".zip",".json",".dta",".pkl",".xz",".zip","none","directory")
     if support_multitable == False and archive == False and fetch == False and table not in ("cases","charges","fees"):
          raise Exception("Single table export choice required! (cases, charges, fees)")
     if archive and append and existing_output and not no_write:
          try:
               old_archive = read(outputs)
          except:
               print("Append failed! Archive at output path could not be read.")

     ## DIRECTORY INPUTS
     if os.path.isdir(inputs):
          queue = glob.glob(inputs + '**/*.pdf', recursive=True)
          found = len(queue)
          assert force or found > 0
          is_full_text = False
          itype = "directory"

     ## FILE INPUTS
     elif os.path.isfile(inputs):
          queue = read(inputs)
          found = queue.shape[0]
          fetch = True if os.path.splitext(inputs)[1] in (".xls",".xlsx") else False
          is_full_text = True
          itype = "query" if os.path.splitext(inputs)[1] in (".xls",".xlsx") else "archive"

     ## OBJECT INPUTS 
     elif isinstance(inputs, pl.dataframe.frame.DataFrame):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = inputs
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pl.series.series.Series):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = inputs
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pd.core.frame.DataFrame):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = pl.from_pandas(inputs)
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pd.core.series.Series):
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = pl.DataFrame({'AllPagesText':pl.from_pandas(inputs)})
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     else:
          raise Exception("Failed to determine input type.")

     if count == 0:
          count = found
     if count > found:
          count = found
     if found > count:
          queue = queue[0:count]

     out = {
          'QUEUE': queue,
          'INPUTS': inputs,
          'NEEDTEXT': bool(not is_full_text),
          'INPUT_TYPE': itype,
          'FOUND': found,
          'COUNT': count,
          'OUTPUT_PATH': outputs,
          'OUTPUT_EXT': outputext,

          'TABLE': table,
          'SUPPORT_MULTITABLE': support_multitable,
          'SUPPORT_SINGLETABLE': support_singletable,
          'SUPPORT_ARCHIVE': support_archive,

          'ARCHIVE': archive,
          'APPEND': append,
          'NO_UPDATE': no_update,

          'FETCH': fetch,
          'ALA_CUSTOMER_ID': cID,
          'ALA_USER_ID': uID,
          'ALA_PASSWORD': pwd,
          'FETCH_SKIP': qskip,
          'FETCH_MAX': qmax,

          'COMPRESS': compress,
          'NO_WRITE': no_write,
          'NO_PROMPT': no_prompt,
          'OVERWRITE': overwrite,
          'EXISTING_OUTPUT': existing_output,
          'DEBUG': debug,
          'WINDOW': window
     }
     dlog(debug, out)
     print("Successfully configured.")
     if now:
          return init(out, window=window, debug=debug)
     return out

def getPDFText(path) -> str:
     """
     From path, return full text of PDF as string (PyMuPdf engine required!)
     """
     try:
          doc = fitz.open(path)
     except:
          return ''
     text = ''
     for pg in doc:
          try:
               text += ' \n '.join(x[4].replace("\n"," ") for x in pg.get_text(option='blocks'))
          except:
               pass
     text = re.sub(r'(<image\:.+?>)','', text).strip()
     return text

def archive(cf, window=None):
     """
     Write a full text archive from inputs in accordance with `cf` configuration.
     """
     a = read(cf, window)
     write(cf, a)
     if window:
          window.write_event_value("COMPLETE-MA",True)
     return a

def read(cf='', window=None):
     """
     Read `cf` input PDF directory or case text archive into memory.
     """
     if isinstance(cf, dict):
          if cf['NEEDTEXT'] == False or "ALABAMA" in cf['QUEUE'][0]:
               return cf['QUEUE']
          if cf['NEEDTEXT'] == True:
               queue = cf['QUEUE']
               aptxt = []
               print("Extracting text...")
               if window:
                    window.write_event_value("PROGRESS_TOTAL",len(queue))
                    for i, pp in enumerate(queue):
                         aptxt += [getPDFText(pp)]
                         window.write_event_value("PROGRESS",i+1)
               else:
                    for pp in tqdm.tqdm(queue):
                         aptxt += [getPDFText(pp)]
          archive = pl.DataFrame({
               'Timestamp': time.time(),
               'AllPagesText': aptxt,
               'Path': queue
               })
          return archive
     elif os.path.isdir(cf):
          queue = glob.glob(path + '**/*.pdf', recursive=True)
          aptxt = []
          print("Extracting text...")
          if window:
               window.write_event_value("PROGRESS_TOTAL",len(queue))
               for i, pp in enumerate(queue):
                    aptxt += [getPDFText(pp)]
                    window.write_event_value("PROGRESS",i+1)
          else:
               for pp in tqdm.tqdm(queue):
                    aptxt += [getPDFText(pp)]
          archive = pl.DataFrame({
          'Timestamp': time.time(),
          'AllPagesText': aptxt,
          'Path': queue
          })
          return archive
     
     elif os.path.isfile(cf):
          ext = os.path.splitext(cf)[1]
          nzext = os.path.splitext(cf.replace(".zip","").replace(".xz","").replace(".gz","").replace(".tar","").replace(".bz",""))[1]
          if nzext in (".xls",".xlsx") and ext in (".xls",".xlsx"):
               parchive = pd.read_excel(cf)
               archive = pl.from_pandas(parchive)
               return archive
          if nzext == ".pkl" and ext == ".xz":
               parchive = pd.read_pickle(cf, compression="xz")
               archive = pl.from_pandas(parchive)
               return archive
          if nzext == ".pkl" and ext == ".pkl":
               parchive = pd.read_pickle(cf)
               archive = pl.from_pandas(parchive)
               return archive
          elif nzext == ".json" and ext == ".zip":
               parchive = pd.read_json(cf, orient='table', compression="zip")
               archive = pl.from_pandas(parchive)
               return archive
          elif nzext == ".json" and ext == ".json":
               try:
                    archive = pl.read_json(cf)
                    return archive
               except:
                    dlog(cf, "Warning: Read JSON with pandas after polars exception.")
                    parchive = pd.read_json(cf, orient='table')
                    archive = pl.from_pandas(parchive)
          elif nzext == ".csv" and ext == ".zip":
               archive = pd.read_csv(cf, compression="zip")
               return archive
          elif nzext == ".csv" and ext == ".csv":
               try:
                    archive = pl.read_csv(cf)
                    return archive
               except:
                    dlog(cf, "Warning: Read CSV with pandas after polars exception.")
                    parchive = pd.read_csv(cf)
                    archive = pl.from_pandas(parchive)
                    return archive
          elif nzext == ".parquet" and ext == ".parquet":
               try:
                    archive = pl.read_parquet(cf)
                    return archive
               except:
                    dlog(cf, "Warning: Read Parquet with pandas after polars exception.")
                    parchive = pd.read_parquet(cf)
                    archive = pl.from_pandas(parchive)
                    return archive
     else:
          return None

def append_archive(inpath='', outpath='', conf=None, window=None):
     """
     Append the contents of one archive to another.
     
     Args:
         inpath (str): Input archive 
         outpath (str): Output archive
         conf (dict): Configuration object
     
     Returns:
         DataFrame: Appended archive object
     """
     if conf and inpath == '':
          inpath = conf['INPUTS']
     if conf and outpath == '':
          outpath = conf['OUTPUT_PATH']

     assert os.path.isfile(inpath) and os.path.isfile(outpath)
     try:
          inarc = read(inpath).select("AllPagesText","Path","Timestamp")
          outarc = read(outpath).select("AllPagesText","Path","Timestamp")
     except:
          try:
               print("Could not find column Timestamp in archive.")
               inarc = read(inpath).select("AllPagesText","Path")
               outarc = read(outpath).select("AllPagesText","Path")
          except:
               print("Could not find column Path in archive.")
               inarc = read(inpath).select("AllPagesText")
               outarc = read(outpath).select("AllPagesText")

     out = pl.concat([inarc, outarc])
     if window:
               window.write_event_value("COMPLETE-AA",True)
     write(conf, out)
     return out

def multi(cf, window=None):
     """
     Start multitable collection using configuration object `cf`.
     """
     df = read(cf, window)
     print("Extracting case info...")
     ca, ac, af = splitCases(df, debug=cf['DEBUG'])
     print("Parsing charges...")
     ch = splitCharges(ac, debug=cf['DEBUG'])
     print("Parsing fees tables...")
     fs = splitFees(af, debug=cf['DEBUG'])
     if not cf['NO_WRITE']:
          print("Writing to export...")
     write(cf, [ca, ch, fs], sheet_names=["cases","charges","fees"])
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ca, ch, fs
     
def charges(cf, window=None):
     """
     Start charges table collection using configuration object `cf`.
     """
     df = read(cf, window)
     print("Extracting charges...")
     ca, ac, af = splitCases(df)
     print("Parsing charges...")
     ch = splitCharges(ac)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     write(cf, ch)
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ch

def cases(cf, window=None):
     """
     Start cases table collection using configuration object `cf`.
     """
     df = read(cf, window)
     print("Extracting case info...")
     ca, ac, af = splitCases(df)
     write(cf, ca)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ca

def fees(cf, window=None):
     """
     Start fee sheet collection using configuration object `cf`.
     """
     df = read(cf, window)
     print("Extracting fee sheets...")
     ca, ac, af = splitCases(df)
     print("Parsing fees tables...")
     fs = splitFees(af)
     write(cf, fs)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return fs

def write(cf, outputs, sheet_names=[]):
     """Write `outputs` to output path at `cf` in accordance with configuration settings.
     
     Args:
         cf (dict): Configuration object
         outputs ([DataFrame]): DataFrame(s) to write to output
         sheet_names (List[str], optional): Output Excel worksheet names
     
     """
     if isinstance(outputs, list):
          assert len(outputs) == len(sheet_names) or len(outputs) == 1
     if cf['NO_WRITE']==True:
          return outputs
     elif not cf['OVERWRITE'] and os.path.isfile(cf['OUTPUT_PATH']):
          raise Exception("Could not write to output path because overwrite mode is not enabled.")
     elif cf['OUTPUT_EXT'] in (".xlsx",".xls"):
          try:
               with xlsxwriter.Workbook(cf['OUTPUT_PATH']) as workbook:
                    if len(sheet_names) > 1:
                         for i, x in enumerate(outputs):
                              x.write_excel(workbook=workbook,worksheet=sheet_names[i], autofit=True, float_precision=2)
                    elif len(sheet_names) == 1:
                         outputs.write_excel(workbook=workbook,worksheet=sheet_names[0], autofit=True, float_precision=2)
                    elif len(sheet_names) == 0:
                         try:
                              outputs.write_excel(workbook=workbook, autofit=True, float_precision=2)
                         except:
                              outputs.to_pandas().to_excel(cf['OUTPUT_PATH'], engine="openpyxl")
          except:
               print("Write xls(x) with polars / xlsxwriter failed. Falling back to pandas / openpyxl...")
               if len(sheet_names) == 0:
                    po = outputs.to_pandas()
                    po.to_excel(engine="openpyxl")
               if len(sheet_names) == 1:
                    po = outputs.to_pandas()
                    po.to_excel(engine="openpyxl", sheet_name=sheet_names[0])
               elif sheet_names == ["cases","charges","fees"]:
                    ca = outputs[0].to_pandas()
                    ca.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="cases")
                    ch = outputs[1].to_pandas()
                    ch.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="charges")
                    fs = outputs[2].to_pandas()
                    fs.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="fees")
               elif len(sheet_names) > 1:
                    with pd.ExcelWriter(cf['OUTPUT_PATH']) as writer:
                         for i, x in enumerate(outputs):
                              x.to_excel(writer, sheet_name=sheet_names[0], engine="openpyxl")
               else:
                    newpath = cf['OUTPUT_PATH'].replace(".xls","").replace(".xlsx","") + "-" + sheet_names[i] + ".xlsx"
                    for i, x in enumerate(outputs):
                         try:
                              x.write_excel(workbook=newpath, autofit=True)
                         except:
                              x.to_pandas().to_excel(newpath, engine="openpyxl")

     elif cf['COMPRESS'] and cf['OUTPUT_EXT'] == ".parquet":
          try:
               outputs.write_parquet(cf['OUTPUT_PATH'], compression='brotli') # add int flag for compress - 0min-11max
          except:
               try:
                     outputs.write_parquet(cf['OUTPUT_PATH'], compression='snappy')
               except:
                     outputs.to_parquet(cf['OUTPUT_PATH'])
     elif not cf['COMPRESS'] and cf['OUTPUT_EXT'] == ".parquet":
          outputs.write_parquet(cf['OUTPUT_PATH'], compression="uncompressed")
     elif cf['OUTPUT_EXT'] == ".json":
          outputs.write_json(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] == ".csv":
          outputs.write_csv(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] == ".dta":
          import pandas as pd
          outputs_pd = outputs.to_pandas()
          outputs_pd.to_stata(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] not in ("none","","directory",None):
          outputs.write_csv(cf['OUTPUT_PATH'])
     else:
          pass
     return outputs

def tables(cf, window=None, debug=False):
    """
    Start Alacorder table export using configuration object `cf`.
    
    Args:
        cf (dict): Configuration object
        debug (bool, optional): Print detailed logs
    
    Returns:
        DataFrame returned from table parser
    """
    return init(cf, window=window)

def init(cf, window=None, debug=False):
     """
     Start Alacorder using configuration object `cf`.
     
     Args:
         cf (dict): Configuration dict object
         debug (bool, optional): Print verbose logs
     
     Returns:
         DataFrame: outputs from specified table parser
     """
     if cf['ARCHIVE'] == True:
          ar = archive(cf, window=window)
          return ar
     elif cf['TABLE'] == "charges" and cf['SUPPORT_SINGLETABLE']:
          ch = charges(cf, window=window)
          return ch
     elif cf['TABLE'] == "cases" and cf['SUPPORT_SINGLETABLE']:
          ca = cases(cf, window=window)
          return ca
     elif cf['TABLE'] == "fees" and cf['SUPPORT_SINGLETABLE']:
          fs = fees(cf, window=window)
          return fs
     elif cf['TABLE'] in ("all","","multi","multitable") and cf['SUPPORT_MULTITABLE']:
          ca, ch, fs = multi(cf, window=window)
          return ca, ch, fs
     else:
          print("Job not specified. Select a mode and reconfigure to start.")
          return None

def dlog(cf=None, text=""):
     if cf == None or cf == False:
          return None
     if cf == True:
          print(text)
     else:
          if cf['DEBUG'] == True:
               print(text)
               return text
          else:
               return None

def splitCases(df, debug=False):
     cases = df.with_columns([
          pl.col("AllPagesText").str.extract(r'(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*',group_index=1).str.replace_all("Case Number:","",literal=True).str.replace(r'C$','').str.strip().alias("Name"),
          pl.col("AllPagesText").str.extract(r'(?:SSN)(.{5,75})(?:Alias)', group_index=1).str.replace_all(":","",literal=True).str.strip().alias("Alias"),
          pl.col("AllPagesText").str.extract(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)', group_index=1).str.replace_all(r'[^\d/]','').str.strip().alias("DOB"),
          pl.col("AllPagesText").str.extract(r'(\w{2}\-\d{4}\-\d{6}\.\d{2})').alias("SHORTCASENO"),
          pl.col("AllPagesText").str.extract(r'(?:County: )(\d{2})').alias("SHORTCOUNTY"),
          pl.col("AllPagesText").str.extract(r'(Phone: )(.+)', group_index=2).str.replace_all(r'[^0-9]','').str.slice(0,10).alias("RE_Phone"),
          pl.col("AllPagesText").str.extract(r'(B|W|H|A)/(?:F|M)').alias("Race"),
          pl.col("AllPagesText").str.extract(r'(?:B|W|H|A)/(F|M)').alias("Sex"),
          pl.col("AllPagesText").str.extract(r'(?:Address 1:)(.+)(?:Phone)*?', group_index=1).str.replace(r'(Phone.+)','').str.strip().alias("Address1"),
          pl.col("AllPagesText").str.extract(r'(?:Address 2:)(.+)').str.strip().alias("Address2"),
          pl.col("AllPagesText").str.extract(r'(?:Zip: )(.+)',group_index=1).str.replace_all(r'[A-Z].+','').alias("ZipCode"),
          pl.col("AllPagesText").str.extract(r'(?:City: )(.*)(?:State: )(.*)', group_index=1).alias("City"),
          pl.col("AllPagesText").str.extract(r'(?:City: )(.*)(?:State: )(.*)', group_index=2).alias("State"),
          pl.col("AllPagesText").str.extract_all(r'(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}.{10,75})').alias("RE_Charges"),
          pl.col("AllPagesText").str.extract_all(r'(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^\n]*)').alias('RE_Fees'),
          pl.col("AllPagesText").str.extract(r'(Total:.+\$[^\n]*)').str.replace_all(r'[^0-9|\.|\s|\$]', "").str.extract_all(r'\s\$\d+\.\d{2}').alias("TOTALS"),
          pl.col("AllPagesText").str.extract(r'(ACTIVE[^\n]+D999[^\n]+)').str.extract_all(r'\$\d+\.\d{2}').arr.get(-1).str.replace(r'[\$\s]','').cast(pl.Float64, strict=False).alias("D999"),
          pl.col("AllPagesText").str.extract_all(r'(\w{2}\d{12})').arr.join("/").alias("RelatedCases"),
          pl.col("AllPagesText").str.extract(r'Filing Date: (\d\d?/\d\d?/\d\d\d\d)').alias("FilingDate"),
          pl.col("AllPagesText").str.extract(r'Case Initiation Date: (\d\d?/\d\d?/\d\d\d\d)').alias("CaseInitiationDate"),
          pl.col("AllPagesText").str.extract(r'Arrest Date: (\d\d?/\d\d?/\d\d\d\d)').alias("ArrestDate"),
          pl.col("AllPagesText").str.extract(r'Offense Date: (\d\d?/\d\d?/\d\d\d\d)').alias("OffenseDate"),
          pl.col("AllPagesText").str.extract(r'Indictment Date: (\d\d?/\d\d?/\d\d\d\d)').alias("IndictmentDate"),
          pl.col("AllPagesText").str.extract(r'Youthful Date: (\d\d?/\d\d?/\d\d\d\d)').alias("YouthfulDate"),
          pl.col("AllPagesText").str.extract(r'AL Institutional Service Num: ([^\na-z])').str.strip().alias("ALInstitutionalServiceNum"),
          pl.col("AllPagesText").str.extract(r'Alacourt\.com (\d\d?/\d\d?/\d\d\d\d)').alias("Retrieved"),
          pl.col("AllPagesText").str.extract(r'Court Action: (BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)').alias("CourtAction"),
          pl.col("AllPagesText").str.extract(r'Court Action Date: (\d\d?/\d\d?/\d\d\d\d)').alias("CourtActionDate"),
          pl.col("AllPagesText").str.extract(r'Charge: ([A-Z\.0-9\-\s]+)').str.rstrip("C").str.strip().alias("Description"),
          pl.col("AllPagesText").str.extract(r'Jury Demand: ([A-Z]+)').str.strip().alias("JuryDemand"),
          pl.col("AllPagesText").str.extract(r'Inpatient Treatment Ordered: ([YES|NO]?)').str.strip().alias("InpatientTreatmentOrdered"),
          pl.col("AllPagesText").str.extract(r'Trial Type: ([A-Z]+)').str.replace(r'[S|N]$','').str.strip().alias("TrialType"),
          pl.col("AllPagesText").str.extract(r'Case Number: (\d\d-\w+) County:').str.strip().alias("County"),
          pl.col("AllPagesText").str.extract(r'Judge: ([A-Z\-\.\s]+)').str.rstrip("T").str.strip().alias("Judge"),
          pl.col("AllPagesText").str.extract(r'Probation Office \#: ([0-9\-]+)').alias("PROBATIONOFFICENUMBERRAW"),
          pl.col("AllPagesText").str.extract(r'Defendant Status: ([A-Z\s]+)').str.rstrip("J").str.strip().alias("DefendantStatus"),
          pl.col("AllPagesText").str.extract(r'([^0-9]+) Arresting Agency Type:').str.replace(r'\n','').str.strip().alias("ArrestingAgencyType"),
          pl.col("AllPagesText").str.extract(r'Arresting Officer: ([A-Z\s]+)').str.rstrip("S").str.rstrip("P").str.strip().alias("ArrestingOfficer"),
          pl.col("AllPagesText").str.extract(r'Probation Office Name: ([A-Z0-9]+)').alias("ProbationOfficeName"),
          pl.col("AllPagesText").str.extract(r'Traffic Citation \#: ([A-Z0-9]+)').alias("TrafficCitationNumber"),
          pl.col("AllPagesText").str.extract(r'Previous DUI Convictions: (\d{3})').str.strip().cast(pl.Int64, strict=False).alias("PreviousDUIConvictions"),
          pl.col("AllPagesText").str.extract(r'Case Initiation Type: ([A-Z\s]+)').str.rstrip("J").str.strip().alias("CaseInitiationType"),
          pl.col("AllPagesText").str.extract(r'Domestic Violence: ([YES|NO])').str.strip().alias("DomesticViolence"),
          pl.col("AllPagesText").str.extract(r'Agency ORI: ([A-Z\s]+)').str.rstrip("C").str.strip().alias("AgencyORI"),
          pl.col("AllPagesText").str.extract(r'Driver License N°: ([A-Z0-9]+)').str.strip().alias("DLRAW"),
          pl.col("AllPagesText").str.extract(r'SSN: ([X\d]{3}\-[X\d]{2}-[X\d]{4})').alias("SSN"),
          pl.col("AllPagesText").str.extract(r'([A-Z0-9]{11}?) State ID:').alias("SIDRAW"),
          pl.col("AllPagesText").str.extract(r'Weight: (\d+)').cast(pl.Int64, strict=False).alias("Weight"),
          pl.col("AllPagesText").str.extract(r"Height : (\d'\d{2})").alias("RAWHEIGHT"),
          pl.col("AllPagesText").str.extract(r'Eyes/Hair: (\w{3})/(\w{3})', group_index=1).alias("Eyes"),
          pl.col("AllPagesText").str.extract(r'Eyes/Hair: (\w{3})/(\w{3})', group_index=2).alias("Hair"),
          pl.col("AllPagesText").str.extract(r'Country: (\w*+)').str.replace(r'(Enforcement|Party)','').str.strip().alias("Country"),
          pl.col("AllPagesText").str.extract(r'(\d\d?/\d\d?/\d\d\d\d) Warrant Issuance Date:').str.strip().alias("WarrantIssuanceDate"),
          pl.col("AllPagesText").str.extract(r'Warrant Action Date: (\d\d?/\d\d?/\d\d\d\d)').str.strip().alias("WarrantActionDate"),
          pl.col("AllPagesText").str.extract(r'Warrant Issuance Status: (\w)').str.strip().alias("WarrantIssuanceStatus"),
          pl.col("AllPagesText").str.extract(r'Warrant Action Status: (\w)').str.strip().alias("WarrantActionStatus"),
          pl.col("AllPagesText").str.extract(r'Warrant Location Status: (\w)').str.strip().alias("WarrantLocationStatus"),
          pl.col("AllPagesText").str.extract(r'Number Of Warrants: (\d{3}\s\d{3})').str.strip().alias("NumberOfWarrants"),
          pl.col("AllPagesText").str.extract(r'Bond Type: (\w)').str.strip().alias("BondType"),
          pl.col("AllPagesText").str.extract(r'Bond Type Desc: ([A-Z\s]+)').str.strip().alias("BondTypeDesc"),
          pl.col("AllPagesText").str.extract(r'([\d\.]+) Bond Amount:').str.replace_all(r'[^0-9\.\s]','').cast(pl.Float64,strict=False).alias("BondAmt"),
          pl.col("AllPagesText").str.extract(r'Bond Company: ([A-Z0-9]+)').str.rstrip("S").str.strip().alias("BondCompany"),
          pl.col("AllPagesText").str.extract(r'Surety Code: ([A-Z0-9]{4})').str.strip().alias("SuretyCode"),
          pl.col("AllPagesText").str.extract(r'Release Date: (\d\d?/\d\d?/\d\d\d\d)').str.strip().alias("BondReleaseDate"),
          pl.col("AllPagesText").str.extract(r'Failed to Appear Date: (\d\d?/\d\d?/\d\d\d\d)').str.strip().alias("FailedToAppearDate"),
          pl.col("AllPagesText").str.extract(r'Bondsman Process Issuance: ([^\n]*?) Bondsman Process Return:').str.strip().alias("BondsmanProcessIssuance"),
          pl.col("AllPagesText").str.extract(r'Bondsman Process Return: (.*?) Number of Subponeas').str.strip().alias("BondsmanProcessReturn"),
          pl.col("AllPagesText").str.extract(r'([\n\s/\d]*?) Appeal Court:').str.replace_all(r'[\n\s]','').str.strip().alias("AppealDate"),
          pl.col("AllPagesText").str.extract(r'([A-Z\-\s]+) Appeal Case Number').str.strip().alias("AppealCourt"),
          pl.col("AllPagesText").str.extract(r'Orgin Of Appeal: ([A-Z\-\s]+)').str.rstrip("L").str.strip().alias("OriginOfAppeal"),
          pl.col("AllPagesText").str.extract(r'Appeal To Desc: ([A-Z\-\s]+)').str.rstrip("D").str.rstrip("T").str.strip().alias("AppealToDesc"),
          pl.col("AllPagesText").str.extract(r'Appeal Status: ([A-Z\-\s]+)').str.rstrip("A").str.strip().alias("AppealStatus"),
          pl.col("AllPagesText").str.extract(r'Appeal To: (\w?) Appeal').str.strip().alias("AppealTo"),
          pl.col("AllPagesText").str.extract(r'LowerCourt Appeal Date: (\d\d?/\d\d?/\d\d\d\d)').str.replace_all(r'[\n\s:\-]','').str.strip().alias("LowerCourtAppealDate"),
          pl.col("AllPagesText").str.extract(r'Disposition Date Of Appeal: (\d\d?/\d\d?/\d\d\d\d)').str.replace_all(r'[\n\s:\-]','').str.strip().alias("DispositionDateOfAppeal"),
          pl.col("AllPagesText").str.extract(r'Disposition Type Of Appeal: [^A-Za-z]+').str.replace_all(r'[\n\s:\-]','').str.strip().alias("DispositionTypeOfAppeal"),
          pl.col("AllPagesText").str.extract(r'Number of Subponeas: (\d{3})').str.replace_all(r'[^0-9]','').str.strip().cast(pl.Int64, strict=False).alias("NumberOfSubpoenas"),
          pl.col("AllPagesText").str.extract(r'Updated By: (\w{3})').str.strip().alias("AdminUpdatedBy"),
          pl.col("AllPagesText").str.extract(r'Transfer to Admin Doc Date: (\d\d?/\d\d?/\d\d\d\d)').str.strip().alias("TransferToAdminDocDate"),
          pl.col("AllPagesText").str.extract(r'Transfer Desc: ([A-Z\s]{0,15} \d\d?/\d\d?/\d\d\d\d)').str.replace_all(r'(Transfer Desc:)','').str.strip().alias("TransferDesc"),
          pl.col("AllPagesText").str.extract(r'Date Trial Began but No Verdict \(TBNV1\): ([^\n]+)').str.strip().alias("TBNV1"),
          pl.col("AllPagesText").str.extract(r'Date Trial Began but No Verdict \(TBNV2\): ([^\n]+)').str.strip().alias("TBNV2")])
     cases.with_columns([
          pl.concat_str([pl.col("RAWHEIGHT"), pl.lit('"')]).alias("Height"),
          pl.col("AllPagesText").str.extract_all(r'(?:Requrements Completed: )([YES|NO]?)').arr.join(", ").str.replace_all(r'[\n:]|Requrements Completed','').str.strip().alias("SentencingRequirementsCompleted"),
          pl.col("AllPagesText").str.extract_all(r'(?:Sentence Date: )(\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.replace_all(r'(Sentence Date: )','').str.strip().alias("SentenceDate"),
          pl.col("AllPagesText").str.extract_all(r'Probation Period: ([^\.]+)').arr.join(", ").str.strip().alias("ProbationPeriod"),
          pl.col("AllPagesText").str.extract_all(r'License Susp Period: ([^\.]+)').arr.join(", ").str.replace_all(r'(License Susp Period:)','').str.strip().alias("LicenseSuspPeriod"),
          pl.col("AllPagesText").str.extract_all(r'Jail Credit Period: ([^\.]+)').arr.join(", ").str.replace_all(r'(Jail Credit Period:)','').str.strip().alias("JailCreditPeriod"),
          pl.col("AllPagesText").str.extract_all(r'Sentence Provisions: ([Y|N]?)').arr.join(", ").str.replace_all(r'(Sentence Provisions:)','').str.strip().alias("SentenceProvisions"),
          pl.col("AllPagesText").str.extract_all(r'Sentence Start Date: (\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.replace_all(r'(Sentence Start Date:)','').str.strip().alias("SentenceStartDate"),
          pl.col("AllPagesText").str.extract_all(r'Sentence End Date: (\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.replace_all(r'(Sentence End Date:)','').str.strip().alias("SentenceEndDate"),
          pl.col("AllPagesText").str.extract_all(r'Probation Begin Date: (\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.replace_all(r'(Probation Begin Date:)','').str.strip().alias("ProbationBeginDate"),
          pl.col("AllPagesText").str.extract_all(r'Updated By: (\w{3}?)').arr.join(", ").str.replace_all(r'(Updated By:)','').str.strip().alias("SentenceUpdatedBy"),
          pl.col("AllPagesText").str.extract_all(r'Last Update: (\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.strip().alias("SentenceLastUpdate"),
          pl.col("AllPagesText").str.extract_all(r'Probation Revoke: (\d\d?/\d\d?/\d\d\d\d)').arr.join(", ").str.replace_all(r'Probation Revoke: ','').str.strip().alias("ProbationRevoke")])

     dlog(debug, [cases.columns, cases.shape, "alac 899"])

     # clean columns, unnest totals 
     cases = cases.with_columns(
          pl.col("RE_Phone").str.replace_all(r'[^0-9]','').alias("CLEAN_Phone"),
          pl.concat_str([pl.col("SHORTCOUNTY"),pl.lit("-"),pl.col("SHORTCASENO")]).alias("CaseNumber"),
          pl.concat_str([pl.col("Address1"), pl.lit(" "), pl.col("Address2")]).str.replace_all(r'JID: \w{3} Hardship.*|Defendant Information.*','').str.strip().alias("StreetAddress"),
          pl.col("Name"),
          pl.when(pl.col("PROBATIONOFFICENUMBERRAW")=="0-000000-00").then(pl.lit('')).otherwise(pl.col("PROBATIONOFFICENUMBERRAW")).alias("ProbationOfficeName"),
          pl.when(pl.col("DLRAW")=="AL").then(pl.lit('')).otherwise(pl.col("DLRAW")).alias("DriverLicenseNo"),
          pl.when(pl.col("SIDRAW")=="AL000000000").then(pl.lit('')).otherwise(pl.col("SIDRAW")).alias("StateID"),
          pl.col("TOTALS").arr.get(0).str.replace_all(r'[^0-9\.]','').cast(pl.Float64, strict=False).alias("TotalAmtDue"),
          pl.col("TOTALS").arr.get(1).str.replace_all(r'[^0-9\.]','').cast(pl.Float64, strict=False).alias("TotalAmtPaid"),
          pl.col("TOTALS").arr.get(2).str.replace_all(r'[^0-9\.]','').cast(pl.Float64, strict=False).alias("TotalBalance"),
          pl.col("TOTALS").arr.get(3).str.replace_all(r'[^0-9\.]','').cast(pl.Float64, strict=False).alias("TotalAmtHold"))
     cases = cases.with_columns(
          pl.when(pl.col("CLEAN_Phone").str.n_chars()<7).then(None).otherwise(pl.col("CLEAN_Phone")).alias("Phone"),
          pl.when(True).then((pl.col("TotalBalance") - pl.col("D999"))).otherwise(None).alias("PaymentToRestore"))

     # clean Charges strings
     # explode Charges for table parsing
     all_charges = cases.explode("RE_Charges").select([
          pl.col("CaseNumber"),
          pl.col("RE_Charges").str.replace_all(r'[A-Z][a-z][A-Za-z\s\$]+.+','').str.strip().alias("Charges")])
     cases.drop_in_place("RE_Charges")

     # clean Fees strings
     # explode Fees for table parsing
     all_fees = cases.explode("RE_Fees").select([
          pl.col("CaseNumber"),
          pl.col("RE_Fees").str.replace_all(r"[^A-Z0-9|\.|\s|\$|\n]"," ").str.strip().alias("Fees")])
     cases.drop_in_place("RE_Fees")

     dlog(debug, [cases.columns, cases.shape, "alac 931"])

     # add Charges, Fees [str] to cases table
     clean_ch_list = all_charges.groupby("CaseNumber").agg(pl.col("Charges"))
     clean_fs_list = all_fees.groupby("CaseNumber").agg(pl.col("Fees"))
     cases = cases.join(clean_ch_list, on="CaseNumber", how="left")
     cases = cases.join(clean_fs_list, on="CaseNumber", how="left")
     cases = cases.with_columns(pl.col("Charges").arr.join("; ").str.replace_all(r'(null;?)',''))
     cases = cases.with_columns(pl.col("Fees").arr.join("; ").str.replace_all(r'(null;?)',''))
     cases = cases.fill_null('')
     cases = cases.select("Retrieved","CaseNumber","Name","DOB","Race","Sex","Description","CourtAction","CourtActionDate","TotalAmtDue","TotalAmtPaid","TotalBalance","TotalAmtHold","PaymentToRestore","Phone", "StreetAddress","City","State","ZipCode",'County',"Country","Alias", 'SSN','Weight','Eyes','Hair',"FilingDate","CaseInitiationDate","ArrestDate","OffenseDate","IndictmentDate","JuryDemand","InpatientTreatmentOrdered","TrialType","Judge","DefendantStatus","ArrestingAgencyType",'ArrestingOfficer','ProbationOfficeName','PreviousDUIConvictions','CaseInitiationType','DomesticViolence','AgencyORI','WarrantIssuanceDate', 'WarrantActionDate', 'WarrantIssuanceStatus', 'WarrantActionStatus', 'WarrantLocationStatus', 'NumberOfWarrants', 'BondType', 'BondTypeDesc', 'BondAmt', 'BondCompany', 'SuretyCode', 'BondReleaseDate', 'FailedToAppearDate', 'BondsmanProcessIssuance', 'AppealDate', 'AppealCourt', 'OriginOfAppeal', 'AppealToDesc', 'AppealStatus', 'AppealTo', 'NumberOfSubpoenas', 'AdminUpdatedBy', 'TransferDesc', 'TBNV1', 'TBNV2','DriverLicenseNo','StateID')
     return cases, all_charges, all_fees

def splitCharges(df, debug=False):
     dlog(debug, [df.columns, df.shape, "alac 945"])
     charges = df.with_columns([
          pl.col("Charges").str.slice(0,3).alias("Num"),
          pl.col("Charges").str.slice(4,4).alias("Code"),
          pl.col("Charges").str.slice(9,1).alias("Sort"), # 0-9: disposition A-Z: filing else: None
          pl.col("Charges").str.extract(r'(\d{1,2}/\d\d/\d\d\d\d)', group_index=1).alias("CourtActionDate"),
          pl.col("Charges").str.extract(r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}\({0,1}[A-Z]{0,1}\){0,1}\.{0,1}\d{0,1}',group_index=0).alias("Cite"),
          pl.col("Charges").str.extract(r'(BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', group_index=1).alias("CourtAction"),
          pl.col("Charges").apply(lambda x: re.split(r'[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\({0,1}?[A-Z]{0,1}?\){0,1}?\.{0,1}?\d{0,1}?',str(x))).alias("Split")
          ])
     charges = charges.with_columns([
          pl.col("Charges").str.contains(pl.col("CourtActionDate")).alias("Disposition"),
          pl.col("Charges").str.contains(pl.col("CourtActionDate")).is_not().alias("Filing"),
          pl.col("Charges").str.contains(pl.lit("FELONY")).alias("Felony"),
          pl.col("Charges").str.contains("GUILTY PLEA").alias("GUILTY_PLEA"),
          pl.col("Charges").str.contains("CONVICTED").alias("CONVICTED")
          ])
     charges = charges.with_columns([
          pl.when(pl.col("Disposition")).then(pl.col("Split").arr.get(1)).otherwise(pl.col("Split").arr.get(0).str.slice(9)).str.strip().alias("Description"),
          pl.when(pl.col("Disposition")).then(pl.col("Split").arr.get(0).str.slice(19)).otherwise(pl.col("Split").arr.get(1)).str.strip().alias("SEG_2")
          ])
     dlog(debug, [charges.columns, charges.shape, "alac 965"])
     charges = charges.with_columns([
          pl.col("SEG_2").str.extract(r'(TRAFFIC MISDEMEANOR|BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', group_index=1).str.replace("TRAFFIC MISDEMEANOR","MISDEMEANOR").alias("TypeDescription"),
          pl.col("SEG_2").str.extract(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', group_index=1).alias("Category"),
          pl.col("Description").str.contains(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)').is_not().alias("A_S_C_DISQ"),
          pl.col("Code").str.contains('(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)').alias("CERV_DISQ_MATCH"),
          pl.col("Code").str.contains(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)').alias("PARDON_DISQ_MATCH"),
          pl.col("Charges").str.contains(r'(CM\d\d|CMUR)|(CAPITAL)').alias("PERM_DISQ_MATCH")
          ])
     charges = charges.with_columns(
          pl.when(pl.col("GUILTY_PLEA") | pl.col("CONVICTED")).then(pl.lit(True)).otherwise(False).alias("Conviction")
          )
     charges = charges.with_columns([
          pl.when(pl.col("CERV_DISQ_MATCH") & pl.col("Felony") & pl.col("Conviction") & pl.col("A_S_C_DISQ")).then(True).otherwise(False).alias("CERVDisqConviction"),
          pl.when(pl.col("CERV_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ")).then(True).otherwise(False).alias("CERVDisqCharge"),
          pl.when(pl.col("PARDON_DISQ_MATCH") & pl.col("A_S_C_DISQ") & pl.col("Conviction") & pl.col("Felony")).then(True).otherwise(False).alias("PardonDisqConviction"),
          pl.when(pl.col("PARDON_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ")).then(True).otherwise(False).alias("PardonDisqCharge"),
          pl.when(pl.col("PERM_DISQ_MATCH") & pl.col("A_S_C_DISQ") & pl.col("Felony") & pl.col("Conviction")).then(True).otherwise(False).alias("PermanentDisqConviction"),
          pl.when(pl.col("PERM_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ")).then(True).otherwise(False).alias("PermanentDisqCharge")
          ])

     charges = charges.select("Num","Code","Description","TypeDescription","Category","CourtAction","CourtActionDate","Conviction","Felony","CERVDisqCharge","CERVDisqConviction","PardonDisqCharge","PardonDisqConviction","PermanentDisqCharge","PermanentDisqConviction")

     dlog(debug, [charges.columns, charges.shape, "alac 989"])

     charges = charges.drop_nulls()
     charges = charges.fill_null(pl.lit(''))

     dlog(debug, [charges.columns, charges.shape, "alac 994"])

     return charges

def splitFees(df, debug=False):
     df = df.select([
          pl.col("CaseNumber"),
          pl.col("Fees").str.replace(r'(?:\$\d{1,2})( )','\2').str.split(" ").alias("SPACE_SEP"),
          pl.col("Fees").str.strip().str.replace(" ","").str.extract_all(r'\s\$\d+\.\d{2}').alias("FEE_SEP")
          ])
     dlog(debug, [df.columns, df.shape, "alac 1004"])
     df = df.select([
          pl.col("CaseNumber"),
          pl.col("SPACE_SEP").arr.get(0).alias("AdminFee1"), # good
          pl.col("SPACE_SEP").arr.get(1).alias("FeeStatus1"), # good
          pl.col("FEE_SEP").arr.get(0).str.replace(r'\$','').alias("AmtDue"), # good
          pl.col("FEE_SEP").arr.get(1).str.replace(r'\$','').alias("AmtPaid"), # good
          pl.col("FEE_SEP").arr.get(-1).str.replace(r'\$','').alias("AmtHold1"),
          pl.col("SPACE_SEP").arr.get(5).alias("Code"), # good
          pl.col("SPACE_SEP").arr.get(6).alias("Payor2"), # good
          pl.col("SPACE_SEP").arr.get(7).alias("Payee2"), # good
          pl.col("FEE_SEP").arr.get(-1).str.replace(r'\$','').alias("Balance") # good
          ])
     out = df.with_columns([
          pl.col("CaseNumber"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then(True).otherwise(False).alias("Total"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then('').otherwise(pl.col("AdminFee1")).alias("AdminFee"),
          pl.when(pl.col("Payor2").str.contains(r"[^R0-9]\d{3}").is_not()).then(pl.lit('')).otherwise(pl.col("Payor2")).alias("Payor1"),
          pl.when(pl.col("Payor2").str.contains(r"[^R0-9]\d{3}").is_not()).then(pl.col("Payor2")).otherwise(pl.col("Payee2")).alias("Payee1"),
          pl.when(pl.col("AdminFee1")=="Total:").then(pl.lit(None)).otherwise(pl.col("FeeStatus1")).alias("FeeStatus2"),
          pl.when(pl.col("AmtHold1")=="L").then("$0.00").otherwise(pl.col("AmtHold1").str.replace_all(r'[A-Z]|\$','')).alias("AmtHold")
          ])
     dlog(debug, [out.columns, out.shape, "alac 1026"])
     out = out.select([
          pl.col("CaseNumber"),
          pl.col("Total"),
          pl.col("AdminFee"),
          pl.when(pl.col("FeeStatus2").str.contains("$", literal=True)).then(pl.lit(None)).otherwise(pl.col("FeeStatus2")).alias("FeeStatus"),
          pl.col("Code"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then('').otherwise(pl.col("Payor1")).alias("Payor"),
          pl.when(pl.col("Payee1").str.contains(r'\$|\.')).then('').otherwise(pl.col("Payee1")).alias("Payee"),
          pl.col("AmtDue").str.strip().cast(pl.Float64, strict=False),
          pl.col("AmtPaid").str.strip().cast(pl.Float64, strict=False),
          pl.col("Balance").str.strip().cast(pl.Float64, strict=False),
          pl.col("AmtHold").str.strip().cast(pl.Float64, strict=False)
          ])
     dlog(debug, [out.columns, out.shape, "alac 1040"])
     out = out.drop_nulls("Balance")
     return out

def map(conf, *args, bar=True, names=[], window=None):
     """
     Return DataFrame from config object and custom column 'getter' functions like below:
     
          def getter(full_case_text: str):
               out = re.search(...)
               ...
               return out
     
     Creates DataFrame with cols: CaseNumber, getter_1(), getter_2(), ...
     Getter functions must take case text as first parameter. Subsequent paramters can be set in map() after the getter parameter. Getter functions must return string, float, or int outputs to map().
     
     Example:
          >>  a = alac.map(conf,
                               alac.getAmtDueByCode, 'D999', 
                               alac.getAmtPaidByCode, 'D999', 
                               alac.getName, 
                               alac.getDOB)
          >>  print(a)
     
     Args:
         conf (pd.Series): Configuration object with paths and settings
     
         *args: def getter(text: str) -> float, 
                   def getter(text: str) -> int,
                   def getter(text: str) -> str,
                   def getter(text: str) -> bool, # check / debug
          
     Returns:
         out = pd.DataFrame({
                   'CaseNumber': (str) full case number with county,
                   'getter_1': (float) outputs of getter_1(),
                   'getter_2': (int) outputs of getter_2(),
                   'getter_3': (str) outputs of getter_2() 
              })
     
     """
     start_time = time.time()
     df_out = pd.DataFrame()
     temp_no_write_tab = False

     # q = read(conf['QUEUE'])
     queue = pd.DataFrame(conf['QUEUE'])

     # sort args into functions and their parameters
     func = pd.Series(args).map(lambda x: 1 if inspect.isfunction(x) else 0)
     funcs = func.index.map(lambda x: args[x] if func[x] > 0 else pd.NaT)
     no_funcs = func.index.map(lambda x: args[x] if func[x] == 0 else pd.NaT)
     countfunc = func.sum()
     column_getters = pd.DataFrame(columns=['Name', 'Method', 'Arguments'], index=(range(0, countfunc)))

     # call methods, return outputs with pandas-friendly dtype
     def ExceptionWrapper(getter, text, *args):
          if args:
               outputs = pd.Series(getter(text, args))
          else:
               outputs = pd.Series(getter(text))
          return outputs.values

     # set name of methods to name w/o "get", i.e. getName() -> 'Name' column in df_out
     for i, x in enumerate(funcs):
          if inspect.isfunction(x):
               try:
                    if len(names)>=i:
                         column_getters.Name[i] = names[i]
                    else:
                         column_getters.Name[i] = str(x.__name__).replace("get","").upper()
               except:
                    column_getters.Name[i] = str(x.__name__).replace("get","").upper()
               column_getters.Method[i] = x

     for i, x in enumerate(args):
          if not inspect.isfunction(x):
               column_getters.Arguments[i] = x

     # run batch
     b = pd.DataFrame()
     # print(type(queue), queue.to_dict())
     allpagestext = queue.transpose()[0]
     print(allpagestext)
 
     # retrieve getter
     for i in column_getters.index:
        name = column_getters.Name[i]
        arg = column_getters.Arguments[i]
        getter = column_getters.Method[i]

     # map getter 
     for i, getter in enumerate(column_getters.Method.tolist()):
        arg = column_getters.Arguments[i]
        name = column_getters.Name[i]
        if arg == pd.NaT: 
             col = allpagestext.map(lambda x: getter(x, arg))
        else: 
             col = allpagestext.map(lambda x: getter(x))
        new_df_to_concat = pd.DataFrame({name: col})
        df_out = pd.concat([df_out, new_df_to_concat], axis=1)
        df_out = df_out.dropna(axis=1)
        df_out = df_out.dropna(axis=0)
        df_out = df_out.convert_dtypes()

     # fix empty -> str error
     for col in column_getters.columns:
        column_getters[col] = column_getters[col].dropna()
        column_getters[col] = column_getters[col].map(lambda x: "" if x == "Series([], Name: AmtDue, dtype: float64)" or x == "Series([], Name: AmtDue, dtype: object)" else x)

     df_out = pl.from_pandas(df_out)

     # write
     if conf['NO_WRITE'] == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(conf['QUEUE']) - 1):
        write(conf, df_out)  

     if not conf['NO_WRITE']:
          return df_out
     else:
          write(conf, df_out)
          return df_out

def fetch(listpath, path, cID, uID, pwd, qmax=0, qskip=0, debug=False, window=None):
     """
     Fetch cases from Alacourt.com with input query spreadsheet headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE.
     Args:
        listpath (str): Path to query table/spreadsheet (.xls, .xlsx)
        path (str): Path to PDF output directory
        cID (str): Customer ID on Alacourt.com
        uID (str): User ID on Alacourt.com
        pwd (str): Password on Alacourt.com
        qmax (int): Maximum queries to conduct on Alacourt.com
        qskip (int): Skip entries at top of query file
        no_update (bool): Do not update query template after completion
        debug (bool): Print detailed runtime information to console
     """
     rq = readPartySearchQuery(listpath, qmax, qskip)

     query = pd.DataFrame(rq[0]) # for fetch - only search columns
     query_writer = pd.DataFrame(rq[1]) # original sheet for write completion 
     incomplete = query.RETRIEVED_ON.map(lambda x: True if x == "" else False)
     query = query[incomplete]

     options = webdriver.ChromeOptions()
     options.add_experimental_option('prefs', {
          "download.default_directory": path, #Change default directory for downloads
          "download.prompt_for_download": False, #To auto download the file
          "download.directory_upgrade": True,
          "plugins.always_open_pdf_externally": True #It will not display PDF directly in chrome
     })

     # start browser session, login
     print("Starting browser... Do not close while in progress!")
     driver = webdriver.Chrome(options=options)
     login(driver, cID, uID, pwd, window=window)
     print("Authentication successful. Fetching cases via party search...")

     # search, retrieve from URL, download to path
     for i, n in enumerate(query.index):
          if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                    login(driver, cID, uID, pwd, window=window)
          driver.implicitly_wait(2)
          results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], window=window)
          print(f'#{n}/{query.shape[0]} {query.NAME[n]} ({len(results)} records returned)')
          driver.implicitly_wait(2)
          if len(results) == 0:
               query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
               query_writer['CASES_FOUND'][n] = "0"
               print(f"{query.NAME[n]}: Found no results.")
               continue
          if window != None:
               window.write_event_value('PROGRESS-TEXT',0)
               window.write_event_value('PROGRESS-TEXT-TOTAL',100)

               for i, url in enumerate(results):
                    window.write_event_value('PROGRESS-TEXT', i+1)
                    downloadPDF(driver, url)
          if window == None:
               for i, url in enumerate(tqdm.rich.tqdm(results)):
                    downloadPDF(driver, url)
          if not no_update:
               query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
               query_writer['CASES_FOUND'][n] = str(len(results))
               query_writer['RETRIEVED_ON'] = query_writer['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
               query_writer['CASES_FOUND'] = query_writer['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
               query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)
          if window != None:
               window.write_event_value('COMPLETE-MA',time.time())
     return [driver, query_writer]

def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", filed_before="", filed_after="", debug=False, cID="", uID="", pwd="", window=None):
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
         debug (bool, optional): Print detailed logs.
         cID (str, optional): Customer ID on Alacourt.com
         uID (str, optional): User ID on Alacourt.com
         pwd (str, optional): Password on Alacourt.com
     
     Returns:
         List[str] of URLs to PDF
     """

     if "frmIndexSearchForm" not in driver.current_url:
          driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

     driver.implicitly_wait(5)

     has_window = False if window == "None" else True


     # connection error 
     try:
          party_name_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtName")
     except selenium.common.exceptions.NoSuchElementException:
          if debug:
               print("""NoSuchElementException on alac.py 2173: party_name_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtName")""")
          if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
               time.sleep(10)
               login(driver,cID=cID,uID=uID,pwd=pwd)
               driver.implicitly_wait(1)
          driver.get("https:v2.alacourt.com/frmIndexSearchForm.aspx")
          print("Successfully connected and logged into Alacourt!")

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

     driver.implicitly_wait(1)

     # submit search
     search_button = driver.find_element(by=By.ID,value="searchButton")

     driver.implicitly_wait(1)
     try:
          search_button.click()
     except:
          driver.implicitly_wait(5)
          time.sleep(5)

     if debug:
          print("Submitted party search form...")

     driver.implicitly_wait(1)

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
     except:
          pass

     if debug:
          print(f"Found {results_count} results, fetching URLs and downloading PDFs...")


     # get PDF links from each page
     pdflinks = []
     i = 0
     for i in range(0,pages):
          driver.implicitly_wait(0.5)
          hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
          for x in hovers:
               try:
                    a = x.get_attribute("href")
                    if "PDF" in a:
                         pdflinks.append(a)
               except:
                    pass
          driver.implicitly_wait(0.5)
          try:
               pager_select = Select(driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"))
               next_pg = int(pager_select.text) + 1
               driver.implicitly_wait(0.5)
          except:
               try:
                    driver.implicitly_wait(0.5)
                    time.sleep(0.5)
                    next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
                    next_button.click()
               except:
                    continue
     return pdflinks

def downloadPDF(driver, url, cID="", uID="", pwd="", window=None):
     """
     With sg.WebDriver `driver`, download PDF at `url`.
     
     Args:
         driver (WebDriver): Google Chrome selenium.WebDriver() object
         url (str): URL to Alacourt case detail PDF download
         cID (str, optional): Customer ID on Alacourt.com
         uID (str, optional): User ID on Alacourt.com
         pwd (str, optional): Password on Alacourt.com
     
     """
     if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx" and cID != "" and uID != "" and pwd != "":
          login(driver,cID=cID,uID=uID,pwd=pwd,window=window)
     a = driver.get(url)
     driver.implicitly_wait(0.5)

def login(driver, cID, uID="", pwd="", path="", window=None):
     """Login to Alacourt.com using (driver) and auth (cID, username, pwd) for browser download to directory at (path)
     
     Args:
         driver (WebDriver): Google Chrome selenium.WebDriver() object
         cID (str): Alacourt.com Customer ID
         uID (str): Alacourt.com User ID
         pwd (str): Alacourt.com Password
         path (str, optional): Set browser download path 
     
     Returns:
         driver (WebDriver): selenium engine
     """
     if driver == None:
          options = webdriver.ChromeOptions()
          options.add_experimental_option('prefs', {
               "download.default_directory": path, #Change default directory for downloads
               "download.prompt_for_download": False, #To auto download the file
               "download.directory_upgrade": True,
               "plugins.always_open_pdf_externally": True #It will not display PDF directly in chrome
          })
          driver = webdriver.Chrome(options=options)

     print("Connecting to Alacourt...")

     login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

     print("Logging in...")

     driver.implicitly_wait(1)
     
     cID_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtCusid")
     username_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId")
     pwd_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword")
     login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

     cID_box.send_keys(cID)
     username_box.send_keys(uID)
     pwd_box.send_keys(pwd)

     driver.implicitly_wait(1)

     login_button.click()

     driver.implicitly_wait(1)

     try:
          continueLogIn = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$btnContinueLogin")
          continueLogIn.click()
     except:
          pass


     driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

     print("Successfully connected and logged into Alacourt!")

     driver.implicitly_wait(1)

     return driver

def makeQueryTemplate(path):
     """Create empty query worksheet to submit search list for Alacorder to retrieve matching case records from Alacourt.com. 
     
     Args:
         path (str): Desired output path (.xls, .xlsx)
     
     """
     success = True
     empty = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"])
     try:
          empty.to_excel(path, sheet_name="queries")
     except:
          success = False
     return success

def readPartySearchQuery(path, qmax=0, qskip=0, window=None):
     """Reads and interprets query template spreadsheets for `alacorder fetch` to queue from. Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in an Excel spreadsheet, CSV, or JSON file to submit a list of queries for Alacorder to fetch.
     
     Args:
         path (str): Path to query template (.xls, .xlsx)
         qmax (int, optional): Maximum queries to conduct on Alacourt.com
         qskip (int, optional): Skip entries at top of query file
     
     Returns:
         [query_out, writer_df]: query_out: (pd.DataFrame) queue object for alac.fetch()
              writer_df: (pd.DataFrame) progress log to be written back to (path)

     """
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

     writer_df = pd.DataFrame(query)
     

     if "RETRIEVED_ON" not in writer_df.columns:
          writer_df['RETRIEVED_ON'] = pd.NaT
          writer_df['CASES_FOUND'] = pd.NaT

     query_out = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"])

     clist = []
     for c in query.columns:
          if str(c).upper().strip().replace(" ","_") in ["NAME", "PARTY", "DATE_OF_BIRTH", "BIRTHDATE", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"]:
               ce = str(c).replace("DATE_OF_BIRTH","DOB").replace("BIRTHDATE","DOB").replace("PARTY","PARTY_TYPE").replace("PARTY_TYPE_TYPE","PARTY_TYPE").strip()
               clist += [ce]
               query_out[str(c).upper().strip().replace(" ","_")] = query[str(c)]
               query_out[ce] = query[str(c)]
     clist = pd.Series(clist).drop_duplicates().tolist()
     if clist == []:
          raise Exception("Invalid template! Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in a spreadsheet or JSON file to submit a list of queries for Alacorder to fetch.")
          print(f"Field columns {clist} identified in query file.")

     query_out = query_out.fillna('')
     return [query_out, writer_df]

if __name__ == "__main__":
     cli()

#   #   #   #           GETTER METHODS         #   #   #   #

def getName(text):
    try:
        return re.sub(r'Case Number:','',re.search(r'(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*', str(text)).group(1)).rstrip("C").strip()
    except:
        return ''
def getAlias(text):
    try:
        return re.sub(r':','',re.search(r'(?:SSN)(.{5,75})(?:Alias)', str(text)).group(1)).strip()
    except:
        return ''
def getDOB(text):
    try:
        return re.sub(r'[^\d/]','',re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)', str(text)).group(1)).strip()
    except:
        return ''
def getPhone(text):
    try:
        m = re.sub(r'[^0-9]','',re.search(r'(Phone: )(.+)', str(text)).group(2)).strip()
        if len(m) < 7:
            return ''
        elif m[0:10] == "2050000000":
            return ''
        elif len(m) > 10:
            return m[0:10]
    except:
        return ''
def getRace(text):
    try:
        return re.search(r'(B|W|H|A)/(F|M)', str(text)).group(1)
    except:
        return ''
def getSex(text):
    try:
        return re.search(r'(B|W|H|A)/(F|M)', str(text)).group(2)
    except:
        return ''
def getAddress1(text):
    try:
        return re.sub(r'Phone.+','',re.search(r'(?:Address 1:)(.+)(?:Phone)*?', str(text)).group(1)).strip()
    except:
        return ''
def getAddress2(text):
    try:
        return re.sub(r'Defendant Information|JID:.+','',re.search(r'(?:Address 2:)(.+)', str(text)).group(1).strip())
    except:
        return ''
def getCity(text):
    try:
        return re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(1)
    except:
        return ''
def getState(text):
    try:
        return re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(2)
    except:
        return ''
def getCountry(text):
    try:
        return re.sub(r'Country:','',re.sub(r'(Enforcement|Party|Country)','',re.search(r'Country: (\w*+)', str(text)).group()).strip())
    except:
        return ''
def getZipCode(text):
    try:
        return re.sub(r'-0000$|[A-Z].+','',re.search(r'(Zip: )(.+)', str(text)).group(2)).strip()
    except:
        return ''
def getAddress(text):
    try:
        street1 = re.sub(r'Phone.+','',re.search(r'(?:Address 1:)(.+)(?:Phone)*?',str(text)).group(1)).strip()
    except:
        street1 = ''
    try:
        street2 = getAddress2(text).strip()
    except:
        street2 = ''
    try:
        zipcode = re.sub(r'[A-Z].+','',re.search(r'(Zip: )(.+)',str(text)).group(2)).strip()
    except:
        zipcode = ''
    try:
        city = re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(1).strip()
    except:
        city = ''
    try:
        state = re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(2).strip()
    except:
        state = ''
    if len(city)>3:
        return f"{street1} {street2} {city}, {state} {zipcode}".strip()
    else:
        return f"{street1} {street2} {city} {state} {zipcode}".strip()
def getChargesRows(text):
    m = re.findall(r'(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{10,75})', str(text))
    return m
def getFeeSheetRows(text):
    m = re.findall(r'(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^A-Za-z\n]*)', str(text))
    return m
def getTotalRow(text):
    try:
        mmm = re.search(r'(Total:.+\$[^\n]*)', str(text)).group()
        mm = re.sub(r'[^0-9|\.|\s|\$]', '', str(mmm))
        m = re.findall(r'\d+\.\d{2}', str(mm))
        return m
    except:
        return ["0.00","0.00","0.00","0.00"]
def getTotalAmtDue(text):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[0]))
    except:
        return 0.00
def getTotalAmtPaid(text):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[1]))
    except:
        return 0.00
def getTotalBalance(text):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[2]))
    except:
        return 0.00
def getTotalAmtHold(text):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[3]))
    except:
        return 0.00
def getPaymentToRestore(text):
    try:
        tbal = getTotalBalance(text)
    except:
        return 0.0
    try:
        d999mm = re.search(r'(ACTIVE[^\n]+D999[^\n]+)',str(text)).group()
        d999m = re.findall(r'\$\d+\.\d{2}',str(d999mm))
        d999 = float(re.sub(r'[\$\s]','',d999m[-1]))
    except:
        d999 = 0.0
    return float(tbal - d999)
def getShortCaseNumber(text):
    try:
        return re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group()
    except:
        return ''
def getCounty(text):
    try:
        return re.search(r'Case Number: (\d\d-\w+) County:', str(text)).group(1)
    except:
        return ''
def getCaseNumber(text):
    try:
        return re.search(r'Case Number: (\d\d-\w+) County:', str(text)).group(1)[0:2] + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group()
    except:
        return ''
def getCaseYear(text):
    try:
        return re.search(r'\w{2}\-(\d{4})-\d{6}\.\d{2}', str(text)).group(1)
    except:
        return ''
def getLastName(text):
    try:
        return getName(text).split(" ")[0].strip()
    except:
        return ''
def getFirstName(text):
    try:
        return getName(text).split(" ")[-1].strip()
    except:
        return ''
def getMiddleName(text):
    try:
        if len(getName(text).split(" ")) > 2:
            return " ".join(getName(text).split(" ")[1:-2]).strip()
        else:
            return ''
    except:
        return ''
def getRelatedCases(text):
    return re.findall(r'(\w{2}\d{12})',str(text))
def getFilingDate(text):
    try:
        return re.sub(r'Filing Date: ','',re.search(r'Filing Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group()).strip()
    except:
        return ''
def getCaseInitiationDate(text):
    try:
        return re.sub(r'Case Initiation Date: ','',re.search(r'Case Initiation Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group())
    except:
        return ''
def getArrestDate(text):
    try:
        return re.search(r'Arrest Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getOffenseDate(text):
    try:
        return re.search(r'Offense Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getIndictmentDate(text):
    try:
        return re.search(r'Indictment Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getYouthfulDate(text):
    try:
        return re.search(r'Youthful Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getRetrieved(text):
    try:
        return re.search(r'Alacourt\.com (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getCourtAction(text):
    try:
        return re.search(r'Court Action: (BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', str(text)).group(1)
    except:
        return ''
def getCourtActionDate(text):
    try:
        return re.search(r'Court Action Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)
    except:
        return ''
def getDescription(text):
    try:
        return re.search(r'Charge: ([A-Z\.0-9\-\s]+)', str(text)).group(1).rstrip("C").strip()
    except:
        return ''
def getJuryDemand(text):
    try:
        return re.search(r'Jury Demand: ([A-Z]+)', str(text)).group(1).strip()
    except:
        return ''
def getInpatientTreatmentOrdered(text):
    try:
        return re.search(r'Inpatient Treatment Ordered: ([YES|NO]?)', str(text)).group(1).strip()
    except:
        return ''
def getTrialType(text):
    try:
        return re.sub(r'[S|N]$','',re.search(r'Trial Type: ([A-Z]+)', str(text)).group(1)).strip()
    except:
        return ''
def getJudge(text):
    try:
        return re.search(r'Judge: ([A-Z\-\.\s]+)', str(text)).group(1).rstrip("T").strip()
    except:
        return ''
def getProbationOfficeNumber(text):
    try:
        return re.sub(r'(0-000000-00)','',re.search(r'Probation Office \#: ([0-9\-]+)', str(text)).group(1).strip())
    except:
        return ''
def getDefendantStatus(text):
    try:
        return re.search(r'Defendant Status: ([A-Z\s]+)', str(text)).group(1).rstrip("J").strip()
    except:
        return ''
def getArrestingAgencyType(text):
    try:
        return re.sub(r'\n','',re.search(r'([^0-9]+) Arresting Agency Type:', str(text)).group(1)).strip()
    except:
        return ''
def getArrestingOfficer(text):
    try:
        return re.search(r'Arresting Officer: ([A-Z\s]+)', str(text)).group(1).rstrip("S").rstrip("P").strip()
    except:
        return ''
def getProbationOfficeName(text):
    try:
        return re.search(r'Probation Office Name: ([A-Z0-9]+)', str(text)).group(1).strip()
    except:
        return ''
def getTrafficCitationNumber(text):
    try:
        return re.search(r'Traffic Citation \#: ([A-Z0-9]+)', str(text)).group(1).strip()
    except:
        return ''
def getPreviousDUIConvictions(text):
    try:
        return int(re.search(r'Previous DUI Convictions: (\d{3})', str(text)).group(1).strip())
    except:
        return ''
def getCaseInitiationType(text):
    try:
        return re.search(r'Case Initiation Type: ([A-Z\s]+)', str(text)).group(1).rstrip("J").strip()
    except:
        return ''
def getDomesticViolence(text):
    try:
        return re.search(r'Domestic Violence: ([YES|NO])', str(text)).group(1).strip()
    except:
        return ''
def getAgencyORI(text):
    try:
        return re.search(r'Agency ORI: ([A-Z\s]+)', str(text)).group(1).rstrip("C").strip()
    except:
        return ''
def getDriverLicenseNo(text):
    try:
        m = re.search(r'Driver License N°: ([A-Z0-9]+)', str(text)).group(1).strip()
        if m == "AL":
            return ''
        else:
            return m
    except:
        return ''
def getSSN(text):
    try:
        return re.search(r'SSN: ([X\d]{3}\-[X\d]{2}-[X\d]{4})', str(text)).group(1).strip()
    except:
        return ''
def getStateID(text):
    try:
        m = re.search(r'([A-Z0-9]{11}?) State ID:', str(text)).group(1).strip()
        if m == "AL000000000":
            return ''
        else:
            return m
    except:
        return ''
def getWeight(text):
    try:
        return int(re.search(r'Weight: (\d+)', str(text)).group(1).strip())
    except:
        return ''
def getHeight(text):
    try:
        return re.search(r"Height : (\d'\d{2})", str(text)).group(1).strip() + "\""
    except:
        return ''
def getEyes(text):
    try:
        return re.search(r'Eyes/Hair: (\w{3})/(\w{3})',str(text)).group(1).strip()
    except:
        return ''
def getHair(text):
    try:
        return re.search(r'Eyes/Hair: (\w{3})/(\w{3})',str(text)).group(2).strip()
    except:
        return ''
def getCountry(text):
    try:
        return re.sub(r'(Enforcement|Party|Country:)','',re.search(r'Country: (\w*+)',str(text)).group(1).strip())
    except:
        return ''
def getWarrantIssuanceDate(text):
    try:
        return re.search(r'(\d\d?/\d\d?/\d\d\d\d) Warrant Issuance Date:',str(text)).group(1).strip()
    except:
        return ''
def getWarrantActionDate(text):
    try:
        return re.search(r'Warrant Action Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantIssuanceStatus(text):
    try:
        return re.search(r'Warrant Issuance Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantActionStatus(text):
    try:
        return re.search(r'Warrant Action Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantLocationStatus(text):
    try:
        return re.search(r'Warrant Location Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getNumberOfWarrants(text):
    try:
        return re.search(r'Number Of Warrants: (\d{3}\s\d{3})',str(text)).group(1).strip()
    except:
        return ''
def getBondType(text):
    try:
        return re.search(r'Bond Type: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getBondTypeDesc(text):
    try:
        return re.search(r'Bond Type Desc: ([A-Z\s]+)',str(text)).group(1).strip()
    except:
        return ''
def getBondAmt(text):
    try:
        return float(re.sub(r'[^0-9\.\s]','',re.search(r'([\d\.]+) Bond Amount:',str(text)).group(1).strip()))
    except:
        return ''
def getSuretyCode(text):
    try:
        return re.search(r'Surety Code: ([A-Z0-9]{4})',str(text)).group(1).strip()
    except:
        return ''
def getBondReleaseDate(text):
    try:
        return re.search(r'Release Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getFailedToAppearDate(text):
    try:
        return re.search(r'Failed to Appear Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getBondsmanProcessIssuance(text):
    try:
        return re.search(r'Bondsman Process Issuance: ([^\n]*?) Bondsman Process Return:',str(text)).group(1).strip()
    except:
        return ''
def getBondsmanProcessReturn(text):
    try:
        return re.search(r'Bondsman Process Return: (.*?) Number of Subponeas',str(text)).group(1).strip()
    except:
        return ''
def getAppealDate(text):
    try:
        return re.sub(r'[\n\s]','',re.search(r'([\n\s/\d]*?) Appeal Court:',str(text)).group(1).strip())
    except:
        return ''
def getAppealCourt(text):
    try:
        return re.search(r'([A-Z\-\s]+) Appeal Case Number',str(text)).group(1).strip()
    except:
        return ''
def getOriginOfAppeal(text):
    try:
        return re.search(r'Orgin Of Appeal: ([A-Z\-\s]+)',str(text)).group(1).rstrip("L").strip()
    except:
        return ''
def getAppealToDesc(text):
    try:
        return re.search(r'Appeal To Desc: ([A-Z\-\s]+)',str(text)).group(1).rstrip("D").rstrip("T").strip()
    except:
        return ''
def getAppealStatus(text):
    try:
        return re.search(r'Appeal Status: ([A-Z\-\s]+)',str(text)).group(1).rstrip("A").strip()
    except:
        return ''
def getAppealTo(text):
    try:
        return re.search(r'Appeal To: (\w?) Appeal',str(text)).group(1).strip()
    except:
        return ''
def getLowerCourtAppealDate(text):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'LowerCourt Appeal Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)).strip()
    except:
        return ''
def getDispositionDateOfAppeal(text):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'Disposition Date Of Appeal: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)).strip()
    except:
        return ''
def getDispositionTypeOfAppeal(text):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'Disposition Type Of Appeal: [^A-Za-z]+',str(text)).group(1)).strip()
    except:
        return ''
def getNumberOfSubpoenas(text):
    try:
        return int(re.sub(r'[\n\s:\-]','',re.search(r'Number of Subponeas: (\d{3})',str(text)).group(1)).strip())
    except:
        return ''
def getAdminUpdatedBy(text):
    try:
        return re.search(r'Updated By: (\w{3})',str(text)).group(1).strip()
    except:
        return ''
def getTransferToAdminDocDate(text):
    try:
        return re.search(r'Transfer to Admin Doc Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getTransferDesc(text):
    try:
        return re.search(r'Transfer Desc: ([A-Z\s]{0,15} \d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getTBNV1(text):
    try:
        return re.search(r'Date Trial Began but No Verdict \(TBNV1\): ([^\n]+)',str(text)).group(1).strip()
    except:
        return ''
def getTBNV2(text):
    try:
        return re.search(r'Date Trial Began but No Verdict \(TBNV2\): ([^\n]+)',str(text)).group(1).strip()
    except:
        return ''
def getSentencingRequirementsCompleted(text):
    try:
        return re.sub(r'[\n:]|Requrements Completed','', ", ".join(re.findall(r'(?:Requrements Completed: )([YES|NO]?)',str(text))))
    except:
        return ''
def getSentenceDate(text):
    try:
        return re.search(r'(Sentence Date: )(\d\d?/\d\d?/\d\d\d\d)',str(text)).group(2).strip()
    except:
        return ''
def getProbationPeriod(text):
    try:
        return "".join(re.search(r'Probation Period: ([^\.]+)',str(text)).group(1).strip()).strip()
    except:
        return ''
def getLicenseSuspPeriod(text):
    try:
        return "".join(re.sub(r'(License Susp Period:)','',re.search(r'License Susp Period: ([^\.]+)',str(text)).group(1).strip()))
    except:
        return ''
def getJailCreditPeriod(text):
    try:
        return "".join(re.search(r'Jail Credit Period: ([^\.]+)',str(text)).group(1).strip())
    except:
        return ''
def getSentenceProvisions(text):
    try:
        return re.search(r'Sentence Provisions: ([Y|N]?)',str(text)).group(1).strip()
    except:
        return ''
def getSentenceStartDate(text):
    try:
        return re.sub(r'(Sentence Start Date:)','',", ".join(re.findall(r'Sentence Start Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getSentenceEndDate(text):
    try:
        return re.sub(r'(Sentence End Date:)','',", ".join(re.findall(r'Sentence End Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getProbationBeginDate(text):
    try:
        return re.sub(r'(Probation Begin Date:)','',", ".join(re.findall(r'Probation Begin Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getSentenceUpdatedBy(text):
    try:
        return re.sub(r'(Updated By:)','',", ".join(re.findall(r'Updated By: (\w{3}?)',str(text)))).strip()
    except:
        return ''
def getSentenceLastUpdate(text):
    try:
        return re.sub(r'(Last Update:)','',", ".join(re.findall(r'Last Update: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getProbationRevoke(text):
    try:
        return re.sub(r'(Probation Revoke:)','',", ".join(re.findall(r'Probation Revoke: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''

