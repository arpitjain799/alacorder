import numpy as np
import pandas as pd
import xlrd
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


print('''

	    ___    __                          __         
	   /   |  / /___  _________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																														
		
		ALACORDER beta 7.3.7 (pure-python)
		by Sam Robson	


Welcome to Alacorder. Please select an operating mode:

	A.	MAKE A TABLE FROM DIRECTORY OR ARCHIVE

		Create detailed cases table with convictions, charges,
		fees, and voting rights restoration information. 

		Inputs:		Text Archive (.pkl.xz) or PDF directory
		Outputs:	Recommend .xls -> all tables in one file
					Also supports .csv, .dta, .json, .txt

	B.	ARCHIVE CASES

		Collect text from PDFs in directory and compress to archive.
		Archives can be processed into tables upon completion.

		Inputs:		PDF Directory (./path/to/pdfs)
		Outputs:	filename.pkl.xz

>> Enter A or B:
''')

ab = "".join(input()).strip()

if ab == "A":
	print(f'''

>>	Enter the input PDF directory or archive file path.
		ex.	/full/path/to/pdf/folder/
		ex.	/full/path/to/fulltextarchive.pkl.xz

>> Input path:
''')
elif ab == "B":
	print(f'''

>>	Enter the input PDF directory path, including a forward-slash.
		ex.	/full/path/to/pdf/folder/

>> Input path: 
''')
else:
	raise Exception("Not a valid input!")

in_dir = "".join(input())
if bool(re.search(r'(\.)', in_dir.split("/")[-1])):
	in_ext = in_dir.split(".")[-1].strip()
else:
	in_ext = "directory"

if ab == "A":
	print(f'''

>>	Enter the output file path.
		ex.	/full/path/to/casestable.xls
		ex.	/full/path/to/cases.csv

>> Output path: 
''')
elif ab == "B":
	print(f'''

>>	Enter the output archive file path.
		ex.	/full/path/to/archive.pkl.xz

>> Output path: 
''')
else:
	raise Exception("Not a valid input!")

xpath = "".join(input())
out_ext = xpath.split(".")[-1].strip()
tab = ""

if ab == "A":
	print(f'''

>>	Should Alacourt save a case text archive
	in the same directory as the output file?

>> Enter Y or N: 
''')
	savearc = "".join(input()).strip()
	if savearc == "Y":
		save_arc = True
	else:
		save_arc = False

if ab == "B" and in_ext == "directory":
	mode = "archive-from-directory"
	batch_size = 250

if ab == "A" and in_ext == "directory": # A dir -> 
	mode = "tables-from-directory"
	batch_size = 100
if ab == "A" and bool(in_ext == "pkl" or in_ext == "pkl.xz"): # A dir -> archive
	mode = "tables-from-archive"
	batch_size = 2000
if ab == "A" and bool(out_ext == "json" or out_ext == "csv" or out_ext == "txt"): #  
	print(f'''

>>	Select a table output, or repeat config with .xls extension to export all tables.
		A: Case Details
		B: Fee Sheets
		C: Charges

>> Enter A, B, or C:
''')
	tab = "".join(input()).strip()
	if tab == "A":
		tab = "cases"
	if tab == "B":
		tab = "fees"
	if tab == "C":
		tab = "charges"
if ab == "B" and in_ext == "directory":
	mode = "archive-from-directory"
	batch_size = 250

if ab != "A" and ab != "B":
	raise Exception("Not a valid input.")


print(f'''

	.....

''')

if ab == "B":
	c = alac.config(in_dir,xpath)
	alac.writeArchive(c)
if ab == "A" and bool(in_ext == "pkl" or in_ext == "xz") and out_ext == "xls":
	c = alac.config(in_dir,xpath,save_archive=save_arc)
	alac.writeTables(c)
if ab == "A" and out_ext != "xls":
	c = alac.config(in_dir,xpath,flags=tab,save_archive=save_arc)
	if tab == "cases":
		alac.writeTables(c)
	if tab == "fees":
		alac.writeFees(c)
	if tab == "charges":
		alac.writeCharges(c)

if ab == "A" and in_ext == "directory":
	c = alac.config(in_dir,xpath)
	alac.writeTables(c)
if ab == "B" and in_ext == "directory":
	print(f'''
>>		Would you like to create a detailed cases 
		information table from the 
		full text archive data?

Enter Y/N:	
''')
	info = "".join(input()).strip()
	if info == "Y":
		print(f'''
>>		Enter the output file path.
			ex.	/full/path/to/fulltextarchive.csv
			ex.	/path/to/archive.xls 

Output Path: 
''')
		in_dir = xpath
		xpath = "".join(input()).strip()
		c = alac.config(in_dir,xpath)
		alac.writeTables(c)
	if info == "N":
		print(f'''
Alacorder completed the task and will now quit.
			''')
