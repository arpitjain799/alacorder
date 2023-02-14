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

            ALACORDER beta 71
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


def wait():
        print("\nPress [ENTER] to start Alacorder or [CTRL-C] to quit...\n")
        a = input()
        print(f"\nTASK STARTED {datetime.datetime.now():%m/%d/%Y, %H:%M:%S}\n\n")

def pickTable():
        print(pick_table)
        pick = "".join(input())
        match pick:
                case "A":
                        tables = "cases"
                case "B":
                        tables = "fees"
                case "C":
                        tables = "charges"
                case "D":
                        tables = "disposition"
                case "E":
                        tables = "filing"
                case other:
                        print("Warning: invalid selection - defaulting to \'cases\'...")
                        tables = "cases"
        return tables

def routeTables(config, tables): # aim to remove
        if tables == "cases":
                alac.parseTables(config)
        if tables == "fees":
                alac.parseFees(config)
        if tables == "charges":
                alac.parseCharges(config)
        if tables == "disposition":
                alac.parseCharges(config)
        if tables == "filing":
                alac.parseCharges(config)


# alacorder main 71
# sam robson


warnings.filterwarnings("ignore")

print(title)

makeArchive = False
makeTable = False
makeAllTables = False
table_path = ""
archive_path = ""

input_path = "".join(input())
incheck = alac.checkPath(input_path)

match incheck:
        case "existing_archive":
                print(just_table)
                table_path = "".join(input())
                match alac.checkPath(table_path):
                        case "table":
                                tables = pickTable()
                        case "overwrite_table":
                                tables = pickTable()
                        case "overwrite_all_tables":
                                tables = "all_tables"
                        case "all_tables":
                                tables = "all_tables"
                        case other:
                                raise Exception("Invalid table output path!")
                ## settings flags will go here
                a = alac.config(input_path, tables_path=table_path, tables=tables, GUI_mode = True)
                wait()
                match tables:
                        case "all_tables":
                                alac.parseTables(a)
                        case "fees":
                                alac.parseFees(a)
                        case "charges":
                                alac.parseCharges(a)
                        case "disposition":
                                alac.parseCharges(a)
                        case "filing":
                                alac.parseCharges(a)
                        case other:
                                warnings.warn("Warning: could not parse table selection. Defaulting to cases...")
                                alac.parseTables(a)
        case "pdf_directory":
                print(both)
                next_path = "".join(input())
                match alac.checkPath(next_path):
                        case "existing_archive":
                                archive_path = next_path
                                makeArchive = True
                        case "archive":
                                archive_path = next_path
                                makeArchive = True
                        case "overwrite_all_tables":
                                makeArchive = False
                                table_path = next_path
                                makeAllTables = True
                                a = alac.config(input_path, tables_path=table_path, tables="all_tables")
                                wait()
                                routeTables(a)
                        case "overwrite_table":
                                makeArchive = False
                                table_path = next_path
                                makeTable = True
                                tables = pickTable()
                                a = alac.config(input_path, tables_path=table_path, tables=tables)
                                wait()
                                routeTables(a)
                        case "table":
                                makeArchive = False
                                makeTable = True
                                table_path = next_path
                                tables = pickTable()
                                a = alac.config(input_path, tables_path=table_path, tables=tables)
                                wait()
                                routeTables(a)
                        case "all_tables":
                                makeArchive = False
                                makeAllTables = True
                                tables = "all_tables"
                                table_path = next_path
                                a = alac.config(input_path, tables_path=table_path, tables="all_tables")
                                wait()
                                routeTables(a)
                        case other:
                                raise Exception("Invalid input type!")
                if makeArchive:
                        print(just_table)
                        last_path = "".join(input())
                        tabcheck = alac.checkPath(last_path)
                        a = alac.config(input_path, archive_path=archive_path, GUI_mode = True)
                        match tabcheck:
                                case "overwrite_all_tables":
                                        makeAllTables = True
                                        table_path = last_path
                                        tables = "all_tables"
                                        wait()
                                        alac.writeArchive(a)
                                        b = alac.config(archive_path, tables_path=table_path, tables="all_tables", GUI_mode=True, force_overwrite=True)
                                        routeTables(b, tables)
                                case "overwrite_table":
                                        makeTable = True
                                        tables = pickTable()
                                        table_path = last_path
                                        wait()
                                        alac.writeArchive(a)
                                        b = alac.config(archive_path, tables_path=table_path, tables=table, GUI_mode=True, force_overwrite=True)
                                        routeTables(b, tables)
                                case "table":
                                        makeTable = True
                                        tables = pickTable()
                                        table_path = last_path
                                        wait()
                                        alac.writeArchive(a)
                                        b = alac.config(archive_path, tables_path=table_path, tables=tables, GUI_mode=True)
                                        routeTables(b, tables)
                                case "all_tables":
                                        makeAllTables = True
                                        table_path = last_path
                                        tables = "all_tables"
                                        wait()
                                        alac.writeArchive(a)
                                        b = alac.config(archive_path, tables_path=table_path, tables="all_tables", GUI_mode=True)
                                        routeTables(b, tables)
                                case other:
                                        makeTable = False
                                        makeAllTables = False
                                        wait()
                                        alac.writeArchive(a)
                if makeTable or makeAllTables:
                        if makeArchive:
                                input_path = archive_path
                        if makeTable:
                                tables = pickTable()
                        else:
                                tables = "all_tables"

                        a = alac.config(input_path, tables_path=table_path, tables=tables, GUI_mode = True)

                        wait()

                        routeTables(a, tables)
        case other:
                raise Exception("Invalid table input path!")

