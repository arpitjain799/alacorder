
# alacorder main 73
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
import time
from datetime import datetime
import pandas as pd
import datetime
from alacorder import alac
import warnings
import PyPDF2
from io import StringIO

tables = ""

pick_table = '''

>>  Select preferred table output below.
        A:  Case Details
        B:  Fee Sheets
        C:  Charges (all)
        D:  Charges (disposition only)
        E:  Charges (filing only)

Enter A, B, C, D, or E to continue:

             '''
just_table = '''

>>  EXPORT DATA TABLE:

        To export data tables from case inputs, enter 
        full output path. Use .xls or .xlsx to export all
        all tables, or, if using another format, select
        a table after entering output file path.

>>  Enter path:

        '''


both =  '''
>>  EXPORT FULL TEXT ARCHIVE:

        To process case inputs into a full text 
        archive (recommended), enter archive 
        path below with file extension .pkl.xz.

>>  EXPORT DATA TABLE:

        To export data tables from case inputs, enter 
        full output path. Use .xls or .xlsx to export all
        all tables, or, if using another format, select
        a table after entering output file path.

>>  Enter path:

        '''
title = '''
        ___    __                          __
       /   |  / /___  _________  _________/ /__  _____
      / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
     / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /
    /_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/

            ALACORDER beta 73
            by Sam Robson

        |------------------------------------------------------|
        |  INPUTS:       /pdfs/path/   PDF directory           |
        |                .pkl.xz       Compressed archive      |
        |------------------------------------------------------|
        |  ALL TABLE     .xlsx         Excel spreadsheet       |
        |  OUTPUTS:      .xls          Excel \'97-\'03           |
        |------------------------------------------------------|
        |  SINGLE        .csv          Comma-separated values  |
        |  TABLE         .json         JavaScript obj. not.    |
        |  OUTPUTS:      .dta          Stata dataset           |
        |                .txt          Text file - no reimport!|
        |------------------------------------------------------|
        |  ARCHIVE:      .pkl.xz       Compressed archive      |
        |------------------------------------------------------|

>>  Enter full path to input directory or archive file path...

'''

text_p = '''

>>  Enter path to output text file (must be .txt): 

'''
def wait():
        print("\nPress [ENTER] to start Alacorder or [CTRL-C] to quit...\n")
        a = input()
        print(f"\nTASK STARTED {datetime.datetime.now():%m/%d/%Y, %H:%M:%S}\n\n")

def pickTable():
        print(pick_table)
        pick = "".join(input())
        if pick == "A":
                tables = "cases"
        elif pick == "B":
                tables = "fees"
        elif pick == "C":
                tables = "charges"
        elif pick == "D":
                tables = "disposition"
        elif pick == "E":
                tables = "filing"
        else:
                print("Warning: invalid selection - defaulting to \'cases\'...")
                tables = "cases"
        return tables

def splitext(path: str):
    head = os.path.split(path)[0]
    tail = os.path.split(path)[1]
    ext = os.path.splitext(path)[1] 
    return pd.Series({
        'head': head,
        'tail': tail,
        'ext': ext
        })

warnings.filterwarnings("ignore")

print(title)

makeArchive = False
makeTable = False
makeAllTables = False
table_path = ""
archive_path = ""

input_path = "".join(input())
incheck = alac.checkPath(input_path)
inext = splitext(input_path)['ext']

if inext == ".pdf":
        text = alac.getPDFText(input_path)
        print(text_p)
        path = "".join(input())
        with open(path, 'w') as f:
                f.write(text)
        print("Exported full text to .txt")
        incheck = "NO"

if inext == ".txt":
        with open(input_path) as f:
                text = f.readlines()
        print(text_p)
        path = "".join(input())
        tp = alac.checkPath(path)
        with open(path, 'w') as f:
                f.write(text)
        print("Exported full text to .txt")
        incheck = "NO"

if incheck == "existing_archive":
        print(just_table)
        table_path = "".join(input())
        tp = alac.checkPath(table_path)
        if tp == "table":
                if tables == "":
                        tables = pickTable()
        elif tp == "overwrite_table":
                if tables == "":
                        tables = pickTable()
        elif tp == "overwrite_all_tables":
                tables = "all_tables"
        elif tp == "all_tables":
                tables = "all_tables"
        else:
                raise Exception("Invalid table output path!")
        ## settings flags will go here
        a = alac.config(input_path, table_path=table_path, tables=tables, GUI_mode = True)
        alac.parseTables(a)
if incheck == "pdf_directory":
        print(both)
        next_path = "".join(input())
        np = alac.checkPath(next_path)
        if np == "existing_archive":
                archive_path = next_path
                makeArchive = True
        if np == "archive":
                archive_path = next_path
                makeArchive = True
        if np == "overwrite_all_tables":
                makeArchive = False
                table_path = next_path
                makeAllTables = True
                a = alac.config(input_path, table_path=table_path, tables="all_tables")
                alac.parseTables(a)
        if np == "overwrite_table":
                makeArchive = False
                table_path = next_path
                makeTable = True
                if tables == "":
                        tables = pickTable()
                a = alac.config(input_path, table_path=table_path, tables=tables)
                alac.parseTables(a)
        if np == "table":
                makeArchive = False
                makeTable = True
                table_path = next_path
                if tables == "":
                        tables = pickTable()
                a = alac.config(input_path, table_path=table_path, tables=tables)
                alac.parseTables(a)
        if np == "all_tables":
                makeArchive = False
                makeAllTables = True
                tables = "all_tables"
                table_path = next_path
                a = alac.config(input_path, table_path=table_path, tables="all_tables")
                alac.parseTables(a)
        if makeArchive:
                print(just_table)
                last_path = "".join(input())
                tc = alac.checkPath(last_path)
                a = alac.config(input_path, archive_path=archive_path, GUI_mode = True)
                if tc == "overwrite_all_tables":
                        makeAllTables = True
                        table_path = last_path
                        tables = "all_tables"
                        alac.writeArchive(a)
                        b = alac.config(archive_path, table_path=table_path, tables="all_tables", GUI_mode=True, force_overwrite=True)
                        alac.parseTables(b)
                elif tc == "overwrite_table":
                        makeTable = True
                        if tables == "":
                                tables = pickTable()
                        table_path = last_path
                        alac.writeArchive(a)
                        b = alac.config(archive_path, table_path=table_path, tables=tables, GUI_mode=True, force_overwrite=True)
                        alac.parseTables(b)
                elif tc == "table":
                        makeTable = True
                        if tables == "":
                                tables = pickTable()
                        table_path = last_path
                        alac.writeArchive(a)
                        b = alac.config(archive_path, table_path=table_path, tables=tables, GUI_mode=True)
                        alac.parseTables(b)
                elif tc == "all_tables":
                        makeAllTables = True
                        table_path = last_path
                        tables = "all_tables"
                        alac.writeArchive(a)
                        b = alac.config(archive_path, table_path=table_path, tables="all_tables", GUI_mode=True)
                        alac.parseTables(b)
                else:
                        makeTable = False
                        makeAllTables = False
                        alac.writeArchive(a)
        if makeTable or makeAllTables:
                if makeArchive:
                        input_path = archive_path
                if makeTable and tables == "":
                        tables = pickTable()
                elif makeTable:
                        pass
                else:
                        tables = "all_tables"
                a = alac.config(input_path, table_path=table_path, tables=tables, GUI_mode = True)
                alac.parseTables(a, tables)








