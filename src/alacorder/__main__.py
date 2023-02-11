import numpy as np
import numexpr
import bottleneck
import pandas as pd
import xlrd
import xarray
import openpyxl
import PyPDF2
import glob
import os
import sys
from io import StringIO
from math import floor
from alacorder import alac
import re
import warnings

warnings.filterwarnings("ignore")

# INPUTS

print('''
        ___    __                          __         
       /   |  / /___  _________  _________/ /__  _____
      / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
     / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
    /_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
                                                                                                                                                                                        
        ALACORDER beta 7.4.9.9.7
        by Sam Robson   

    Alacorder processes case detail PDFs into data tables
    suitable for research purposes and generates compressed
    text archives from the source files to speed future
    data collection from the same set of cases.

    INPUTS:     /pdfs/path/ PDF Directory
                .pkl.xz     Compressed Archive

    OUTPUTS:    .xls    Excel Spreadsheet
                .pkl.xz     Compressed Archive 
                .csv        Comma-separated values 
                .json       JSON 
                .dta        Stata 
                .txt        Plain text

>>  Enter the input PDF directory or archive file path.
    If directory, include forward-slash ('/').

        ex. /full/path/to/input/PDF/folder/
        ex. /path/to/textarchive.pkl.xz

>>  Input path:
''')

in_dir = "".join(input())  # ask input path

origin = ""
# check if exists, sort by origin: pdf, directory, archive
if os.path.exists(in_dir) == True:
    if "." in in_dir:
        in_ext = in_dir.split(".")[-1]
        if in_ext == "pkl" or in_ext == "xz":  # i
            origin = "archive"
        elif in_ext == "pdf":
            origin = "pdf"
        elif in_ext == "directory":
            origin = "directory"
    else:
        in_ext = "directory"
else:
    raise Exception("Not a valid input path!")

# set PDF paths / case text if available
if origin == "directory":
    try:
        paths = glob.glob(
            in_dir + '**/*.pdf', recursive=True) if in_ext == "directory" else pd.read_pickle(in_dir, compression="xz")['Path']
    except KeyError:
        try:
            paths = glob.glob(
                in_dir + '**/*.pdf', recursive=True) if in_ext == "directory" else pd.read_pickle(in_dir)['Path']
            try:
                paths = glob.glob(
                    in_dir + '**/*.pdf', recursive=True) if in_ext == "directory" else ""
            except KeyError:
                raise Exception("Error: could not find path list!")
        except (KeyError, FileNotFoundError):
            pass


# OUTPUTS

print(f'''

>>  Enter the output file path.
        ex. /my/documents/casestable.xls
        ex. archivemay2022.pkl.xz
        ex.     /documents/projects/feesheets.dta
        ex.     /docs/prj/charges.json

>> Output path: 
''')

# prompt output path
out_dir = "".join(input())
xpath = out_dir
out_ext = out_dir.split(".")[-1]

# makeFirst = "table" | "archive" | "all_tables"
#              pick      tab aft?     arc aft?


if out_ext == "pkl" or out_ext == "xz" or out_ext == "txt":  # if output is archive
    if in_ext == "pkl" or in_ext == "xz":  # if input is also archive
        make = "table"
    elif in_ext == "directory" or in_ext == "pdf":  # dir -> pkl
        make = "archive"
    else:
        raise Exception("Not a valid output path!")
elif out_ext == "json" or out_ext == "csv" or out_ext == "dta":
    make = "table"
elif out_ext == "xls":
    make = "all_tables"
elif out_ext == "txt":
    make = "archive"
else:
    raise Exception("Not a valid output path!")

flag = ""

if make == "table":
    print(f'''

>>  Select a table output, or repeat config with 
    .xls extension to export all tables.
        A: Case Details
        B: Fee Sheets
        C: Charges (all)
        D: Charges (disposition only)
        E: Charges (filing only)

>> Enter A, B, C, D, or E:
''')
    tab = "".join(input()).strip()
    if tab == "A":
        make = "cases"
    if tab == "B":
        make = "fees"
    if tab == "C":
        make = "charges"
    if tab == "D":
        make = "charges"
        flag = "disposition"
    if tab == "E":
        make = "charges"
        flag = "filing"

# make afters?
if make == "archive" and bool(out_ext == "xz" or out_ext == "pkl"):
    print(f'''
>>      Would you like to create a detailed cases 
        information table from the full text 
        archive data once complete?
        
        YES:    Enter the output file path.
        
         NO:    Press [ENTER] or [RETURN] to 
                continue without.

Enter path or skip:
''')
    try:
        info = "".join(input()).strip()
    except EOFError:
        a = alac.config(in_dir, xpath)
        alac.writeArchive(a)
        pass

    if len(info) > 2:
        print(info)
        xpath_two = info
        in_dir_two = xpath

        a = alac.config(in_dir, xpath)
        alac.writeArchive(a)

        c = alac.config(in_dir_two, xpath_two)
        alac.writeTables(c)


if make == "cases" or make == "fees" or make == "charges" or make == "all_tables" or make == "table":
    savearc = ""
    if origin == "directory" or origin == "pdf":
        print(f'''

    >>  Should Alacorder save a case text archive
        in the same directory as the output file?

    >> Enter Y or N: 
    ''')
        savearc = "".join(input()).strip()

    if savearc == "Y":
        do_other_after = True
    else:
        do_other_after = False

    a = alac.config(in_dir, xpath, save_archive=do_other_after, flags=flag)

    if make == "cases":
        alac.writeTables(a)
    if make == "charges":
        alac.writeCharges(a)
    if make == "fees":
        alac.writeFees(a)
    if make == "all_tables":
        alac.writeTables(a)

if make == "archive" and out_ext == "txt":
    c = alac.config(in_dir, xpath)
    alac.writeArchive(c)
