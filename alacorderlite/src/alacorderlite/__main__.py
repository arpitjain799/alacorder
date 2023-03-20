# main 78
# sam robson


import warnings
from alacorderlite import alac
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

@click.group(invoke_without_command=True)
@click.version_option("78.1.7", package_name="alacorder")
@click.pass_context
def cli(ctx):
    """
    ALACORDER beta 78.1

    Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.

    """
    if ctx.invoked_subcommand is None:
        import PySimpleGUI as sg
        sg.theme("SystemDefault")
        sg.set_options(font="Default 14")
        current_label = "Select a tab below to begin."
        fetch_layout = [
            [sg.Text("""Collect case PDFs in bulk from Alacourt.com\nfrom a list of names or search parameters.""",font="Default 22",pad=(10,10))],
            [sg.Text("""Use column headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to scrape. Each column corresponds to a search field in Party Search. Missing columns and entries will be left empty, i.e. if only the NAME's and CASE_YEAR's are relevant to the search, a file with two columns will work.""",size=(55,None))],
            [sg.Text("Input Path: "), sg.InputText(key="SQ-INPUTPATH-",focus=True)],
            [sg.Text("Output Path: "), sg.InputText(key="SQ-OUTPUTPATH-")],
            [sg.Text("Alacourt.com Credentials", font="Default 14")],
            [sg.Text("Customer ID: "), sg.Input(key="SQ-CUSTOMERID-")],
            [sg.Text("User ID: "), sg.Input(key="SQ-USERID-")],
            [sg.Text("Password: "), sg.InputText(key="SQ-PASSWORD-",password_char='*')],
            [sg.Text("Max queries: "), sg.Input(key="SQ-MAX-", default_text="0", size=[5,1]),sg.Text("Skip from top: "), sg.Input(key="SQ-SKIP-", default_text="0",size=[5,1]),sg.Text("Speed Multiplier: "), sg.Input(key="SQ-SPEED-", default_text="1",size=[5,1])],
            [sg.Button("Start Query",key="SQ")]] # "SQ"
        archive_layout = [
            [sg.Text("""Create full text archives from a\ndirectory with PDF cases.""", font="Default 22", pad=(10,10), size=(60,None))],
            [sg.Text("""Case text archives require a fraction of the storage capacity and processing time used to process PDF directories. Before exporting your data to tables, create an archive with supported file extensions .pkl.xz, .json(.zip), .parquet and .csv(.zip). Once archived, use your case text archive as an input for multitable or single table export.""",size=(50,None), font='Default 14')],
            [sg.Text("Input Path: "), sg.InputText(key="MA-INPUTPATH-")],
            [sg.Text("Output Path: "), sg.InputText(key="MA-OUTPUTPATH-")],
            [sg.Text("Skip Cases in Archive: "), sg.Input(key="MA-SKIP-")],
            [sg.Text("Max cases: "), sg.Input(key="MA-COUNT-", default_text="0", size=[10,1])],
            [sg.Checkbox("Try to Append",key="MA-APPEND-"), sg.Checkbox("Allow Overwrite",key="MA-OVERWRITE-")],
            [sg.Button("Make Archive",key="MA")]] # "MA"
        table_layout = [
            [sg.Text("""Export data tables from case archive or directory.""", font="Default 22", size=(50,1), pad=(10,10))],
            [sg.Text("""Alacorder processes case detail PDFs and case text archives into data tables suitable for research purposes. Export an Excel spreadsheet with detailed cases information (cases), fee sheets (fees), and charges information (charges, disposition, filing), or select a table to export to another format (.json, .csv, .parquet). Note: It is recommended that you create a case text archive from your target PDF directory before exporting tables. Case text archives can be processed into tables at a much faster rate and require far less storage.""", size=(50,None))],
            [sg.Text("Input Path: "), sg.InputText(key="TB-INPUTPATH-")],
            [sg.Text("Output Path: "), sg.InputText(key="TB-OUTPUTPATH-")],
            [sg.Text("Max cases: "), sg.Input(key="TB-COUNT-", default_text="0", size=[10,1])],
            [sg.Radio("All Tables (.xlsx, .xls)", "TABLE", key="TB-ALL-", default=True), 
                sg.Radio("Cases", "TABLE", key="TB-CASES-", default=False), 
                sg.Radio("All Charges", "TABLE", key="TB-CHARGES-", default=False)], 
            [sg.Radio("Disposition Charges", "TABLE", key="TB-DISPOSITION-",default=False), sg.Radio("Filing Charges", "TABLE", key="TB-FILING-",default=False),
                sg.Radio("Fee Sheets","TABLE",key="TB-FEES-",default=False)],
            [sg.Checkbox("Allow Overwrite", key="TB-OVERWRITE-"), sg.Checkbox("Compress", key="TB-COMPRESS-")],
            [sg.Button("Export Table",key="TB")]] # "TB"
        append_layout = [
            [sg.Text("""Append case text archive with the contents\nof a PDF directory or the contents of another archive.""", font="Default 22", size=(60,None), pad=(10,10))],
            [sg.Text("""Case text archives require a fraction of the storage capacity and processing time used to process PDF directories. Before exporting your data to tables, create an archive with supported file extensions .pkl.xz, .json(.zip), .parquet and .csv(.zip). Once archived, use your case text archive as an input for multitable or single table export.""",auto_size_text=True, font='Default 14', size=(50,None))],
            [sg.Text("Input Path: "), sg.InputText(key="AA-INPUTPATH-")],
            [sg.Text("Output Path: "), sg.InputText(key="AA-OUTPUTPATH-")],
            [sg.Button("Append Archives", key="AA")]] # "AA"
        mark_layout = [
            [sg.Text("""Mark query template with collected cases from input\narchive or directory.""", font="Default 22", size=(60,None), pad=(10,10))],
            [sg.Text("""Use column headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to scrape. Each column corresponds to a search field in Party Search. Missing columns and entries will be left empty, i.e. if only the NAME's and CASE_YEAR's are relevant to the search, a file with two columns will work.""", font='Default 14', size=(60,None))],
            [sg.Text("Input Path: "), sg.InputText(key="MQ-INPUTPATH-")],
            [sg.Text("Output Path: "), sg.InputText(key="MQ-OUTPUTPATH-")],
            [sg.Button("Mark Query",key="MQ")]] # "MQ"
        about_layout = [
            [sg.Text("""
    ___    __                          __         
   /   |  / /___  _________  _________/ /__  _____
  / /| | / / __ `/ ___/ __ \/ ___/ __  / _ \/ ___/
 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
/_/  |_/_/\__,_/\___/\____/_/   \__,_/\___/_/     

ALACORDER beta 78.1.7""",font="Courier 14", pad=(5,5))],[sg.Text("""Alacorder retrieves and processes case detail PDFs\ninto data tables suitable for research purposes.""",font="Default 22", pad=(10,10))],
            [sg.Text("""1.  fetch - Retrieve case detail PDFs in bulk from Alacourt.com\n2.  archive - Create full text archives from PDF directory\n3.  table - Export data tables from case archive or directory\n4.  append - Append contents of one archive to another\n5.  mark - Mark already collected cases on query template
            """, font="Courier 12", size=[65,None])],
            [sg.Text("View documentation, source code, and latest updates on GitHub (https://github.com/sbrobson959/alacorder) or PyPI (https://pypi.org/project/alacorder/). To use command line interface, run `% python -m alacorder --help` for guidance. \n\n© 2023 Sam Robson", font="Courier 12", size=[60,None])],
            ] # "ABOUT"
        current_container = [[sg.TabGroup(size=[220,None], expand_x=True,font="Courier",layout=[
                            [sg.Tab("fetch", layout=fetch_layout, pad=(10,10))],
                            [sg.Tab("archive", layout=archive_layout, pad=(10,10))],            
                            [sg.Tab("table", layout=table_layout, pad=(10,10))],
                            [sg.Tab("append", layout=append_layout, pad=(10,10))],
                            [sg.Tab("mark", layout=mark_layout, pad=(10,10))],
                            [sg.Tab("about", layout=about_layout, pad=(10,10))]])]]
        layout = [[sg.Multiline(size=(75,1),font="Courier 12", expand_x=False, expand_y=True, write_only=True, reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True, no_scrollbar=True, default_text=current_label, focus=False, reroute_cprint = False)],current_container,[sg.VSeperator(color=None, pad=(2,2))]]
        window = sg.Window(title="ALACORDER (graphical beta)", layout=layout)
        while True:
            event, values = window.read()
            if event == "TB":
                if bool(window["TB-ALL-"]) == True:
                    tabl = "all"
                    tpick = True
                elif bool(window["TB-CASES-"]) == True:
                    tabl = "cases"
                    tpick = True
                elif bool(window["TB-CHARGES-"]) == True:
                    tabl = "charges"
                    tpick = True
                elif bool(window["TB-DISPOSITION-"]) == True:
                    tabl = "disposition"
                    tpick = True
                elif bool(window["TB-FILING-"]) == True:
                    tabl = "filing"
                    tpick = True
                elif bool(window["TB-FEES-"]) == True:
                    tabl = "fees"
                    tpick = True
                else:
                    print("Invalid table input choice.")
                    tpick = False
                a = alac.setinit(window['TB-INPUTPATH-'].get(),window['TB-OUTPUTPATH-'].get(),count=int(window['TB-COUNT-'].get()),table=tabl,overwrite=window['TB-OVERWRITE-'].get(),compress=window['TB-COMPRESS-'].get(),no_prompt=True,log=False)
            if event == "MA":
                a = alac.setinit(window['MA-INPUTPATH-'].get(),window['MA-OUTPUTPATH-'].get(),count=int(window['MA-COUNT-'].get()),archive=True,overwrite=window['MA-OVERWRITE-'].get(), append=window['MA-APPEND-'].get(), no_prompt=True,log=False)
            if event == "SQ":
                pwd = window["SQ-PASSWORD-"].get()
                a = alac.fetch(window['SQ-INPUTPATH-'].get(),window['SQ-OUTPUTPATH-'].get(),cID=window['SQ-CUSTOMERID-'].get(),uID=window['SQ-USERID-'].get(),pwd=pwd,qmax=int(window['SQ-MAX-'].get()),speed=int(window['SQ-SPEED-'].get()),qskip=int(window['SQ-SKIP-'].get()),no_log=True)
            if event == "MQ":
                a = alac.mark(window['MQ-INPUTPATH-'].get(),window['MQ-OUTPUTPATH-'].get())
            if event == "AA":
                a = alac.append_archive(window['AA-INPUTPATH-'].get(),window['AA-OUTPUTPATH-'].get())
            if event == "Exit" or event == sg.WIN_CLOSED:
                break


if __name__ == "__main__":
    cli()