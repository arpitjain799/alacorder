# alacorder main 71
# sam robson

import os
import sys
import glob
import re
import math
import numexpr
import xarray
import bottleneck
import numpy as np
import xlrd
import openpyxl
import datetime
import pandas as pd
import time
from alacorder import alac
import warnings
import PyPDF2
from io import StringIO

warnings.filterwarnings("ignore")

print('''
        ___    __                          __
       /   |  / /___  _________  _________/ /__  _____
      / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
     / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /
    /_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/

    ALACORDER beta 71
    by Sam Robson

|------------------------------------------------------|
|  INPUTS:       /pdfs/path/   PDF directory           |
|                .pkl.xz       Compressed archive      |
|------------------------------------------------------|
|  ALL TABLE     .xlsx         Excel spreadsheet       |
|  OUTPUTS:      .xls          Excel \'97-\'03         |
|------------------------------------------------------|
|  SINGLE        .csv          Comma-separated values  |
|  TABLE         .json         JavaScript obj. not.    |
|  OUTPUTS:      .dta          Stata dataset           |
|                .txt          Text file - no reimport!|
|------------------------------------------------------|
|  ARCHIVE:      .pkl.xz       Compressed archive      |
|------------------------------------------------------|

>>  Enter full path to input directory or archive file path:

''')

input_path = "".join(input())

if os.path.isdir(input_path):
        print('''
    >>  To process this PDF directory into a full text archive (recommended),
        provide archive path below with file extension .pkl.xz.")

        Or press [RETURN] to skip...

            ''')
        archive_accident = False
        archive_path = "".join(input())
        if archive_path.strip() != "":
            arc_head = os.path.split(archive_path)[0]
            if os.path.exists(arc_head) == False:
                raise Exception("Invalid input!")
            else:
                makeArchive = True
            arc_tail = os.path.split(archive_path)[1]
            arc_ext = os.path.splitext(arc_tail)[1]
            if arc_ext == ".xz": 
                if os.path.isfile(archive_path):
                    appendArchive = True
                else:
                    appendArchive = False
            else:
                print('''\n
        >>  Invalid archive extension! Archives must export to .pkl.xz. Press [ENTER] to attempt TABLES export to the provided path or [CTRL-C] to quit.\n''')
                press_enter = "".join(input())
                archive_accident = True
                makeArchive = False
        if archive_path.strip() == "":
            makeArchive=False
        if archive_accident:
            tables_path = archive_path
        else:
            print('''

        >>  DATA TABLE OUTPUTS:
        
                .xls/.xlsx  Excel Spreadsheet 
                .pkl.xz     Compressed Archive 
                .csv        Comma-separated values 
                .json       JSON 
                .dta        Stata 
                .txt        Plain text

        >>  To export data tables from PDF directory, provide 
            full output path. Use .xls or .xlsx to export all
            tables, or select a table if using another format
            after providing the output path.

            Or press [RETURN] to skip...

                ''')

            tables_path = "".join(input())
    
        if tables_path.strip() == "" and makeArchive:
            a = alac.config(input_path, archive_path=archive_path, GUI_mode=True)
            alac.parseTables(a)
        if tables_path.strip() != "":
            tab_head = os.path.split(tables_path)[0]
            if os.path.exists(tab_head) is False:
                raise Exception(f"Invalid table output path!")
            tab_tail = os.path.split(tables_path)[1]
            tab_ext = os.path.splitext(tab_tail)[1]
            tab = ""
            if archive_accident and tables_path.strip() == "":
                tables_path = archive_path
            if tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".xz":
                tab = "all"
            if os.path.isfile(tables_path):
                print('''   WARNING: EXISTING FILE AT TABLE OUTPUT PATH\n   PRESS [CTRL-C] TO CANCEL OR PRESS RETURN TO OVERWRITE FILE.\n''')
                press_enter = "".join(input())

            if not (tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".xz"):
                print('''

    >>  Select preferred table output below:
            A: Case Details
            B: Fee Sheets
            C: Charges (all)
            D: Charges (disposition only)
            E: Charges (filing only)

    >>  Enter A, B, C, D, or E to continue:

                 ''')
                tab = "".join(input()).strip()
                print("\n\n...\n\n")

            if tab == "all":
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, GUI_mode=True)
                    alac.parseTables(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, GUI_mode=True)
                    alac.parseTables(a)
            if tab == "A" or tab == "":
                make = "cases"
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, tables="cases", GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, tables="cases", GUI_mode=True)
                    alac.parseTables(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, tables="cases", GUI_mode=True)
                    alac.parseTables(a)
            if tab == "B":
                make = "fees"
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, tables="fees", GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, tables="fees", GUI_mode=True)
                    alac.parseFees(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, tables="fees", GUI_mode=True)
                    alac.parseFees(a)
            if tab == "C":
                make = "charges"
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, tables="charges", GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, tables="charges", GUI_mode=True)
                    alac.parseCharges(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, tables="charges", GUI_mode=True)
                    alac.parseCharges(a)
            if tab == "D":
                make = "disposition"
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, tables="disposition", GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, tables="disposition", GUI_mode=True)
                    alac.parseCharges(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, tables="disposition", GUI_mode=True)
                    alac.parseCharges(a)
            if tab == "E":
                make = "filing"
                if makeArchive:
                    a = alac.config(input_path, archive_path=archive_path, tables_path=tables_path, tables="filing", GUI_mode=True)
                    alac.writeArchive(a)
                    print(f"\nCompleted archive export. Beginning table export... {time.time()}\n")
                    b = alac.config(archive_path, tables_path=tables_path, tables="filing", GUI_mode=True)
                    alac.parseCharges(b)
                else:
                    a = alac.config(input_path, tables_path=tables_path, tables="filing", GUI_mode=True)
                    alac.parseCharges(a)




if os.path.isfile(input_path):
    in_head = os.path.split(input_path)[0]
    in_tail = os.path.split(input_path)[1]
    in_ext = os.path.splitext(in_tail)[1]
    if in_ext == ".xz":
        try:
            queue = pd.read_pickle(input_path,compression="xz")['AllPagesText']
        except KeyError:
            raise Exception("Could not identify Series \'AllPagesText\' in input archive!")
    elif in_ext == ".pdf": # if pdf get text
        queue = pd.Series([alac.getPDFText(input_path)])
    elif in_ext == ".txt": # if txt get text
        with open(input_path,'r') as textfile:
            queue = pd.Series([textfile.read()])
    else:
        raise Exception("Invalid input!")

    print('''

OUTPUTS:    .xls/.xlsx  Excel Spreadsheet 
            .pkl.xz     Compressed Archive 
            .csv        Comma-separated values 
            .json       JSON 
            .dta        Stata 
            .txt        Plain text


>>  To export data tables from archive, provide 
    full output path. Use .xls or .xlsx to export all
    tables, or select a table if using another format
    after providing the output path.

    OUTPUT PATH:
        ''')

    tables_path = "".join(input())
    if tables_path.strip() != "":
        tab_head = os.path.split(tables_path)[0]
        if os.path.exists(tab_head) is False:
            raise Exception(f"Invalid table output path!")
        tab_tail = os.path.split(tables_path)[1]
        tab_ext = os.path.splitext(tab_tail)[1]
        if os.path.isfile(tables_path):
            print('''\n>>   WARNING: EXISTING FILE AT TABLE OUTPUT PATH\n>>   PRESS [CTRL-C] TO CANCEL OR PRESS RETURN TO OVERWRITE FILE.\n''')
            press_enter = "".join(input())

        tab = ""
        if tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".xz":
            tab = "all"
        if not (tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".pkl.xz"):
            print('''

>>  Select preferred table output below.
        A: Case Details
        B: Fee Sheets
        C: Charges (all)
        D: Charges (disposition only)
        E: Charges (filing only)

Enter A, B, C, D, or E to continue:

             ''')

            tab = "".join(input()).strip()
            print("\n\n...\n\n")
        if tab == "all":
            a = alac.config(input_path, tables_path=tables_path, GUI_mode=True)
            alac.parseTables(a)
        if tab == "A":
            make = "cases"
            a = alac.config(input_path, tables_path=tables_path, tables="cases", GUI_mode=True)
            alac.parseTables(a)
        if tab == "B":
            make = "fees"
            a = alac.config(input_path, tables_path=tables_path, tables="fees", GUI_mode=True)
            alac.parseFees(a)
        if tab == "C":
            make = "charges"
            a = alac.config(input_path, tables_path=tables_path, tables="charges", GUI_mode=True)
            alac.parseCharges(a)
        if tab == "D":
            make = "disposition"
            a = alac.config(input_path, tables_path=tables_path, tables="disposition", GUI_mode=True)
            alac.parseCharges(a)
        if tab == "E":
            make = "filing"
            a = alac.config(input_path, tables_path=tables_path, tables="filing", GUI_mode=True)
            alac.parseCharges(a)




