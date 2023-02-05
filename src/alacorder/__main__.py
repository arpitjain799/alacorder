import cython
import pyximport; pyximport.install(pyimport=True)
import pandas as pd
import numpy as np
import xlrd
import openpyxl
import PyPDF2
import glob
import os
import sys
from io import StringIO
from math import floor
from alacorder import run
import re
from alacorder import alac
import warnings

warnings.filterwarnings("ignore")

print('''

	    ___    __                          __         
	   /   |  / /___ __________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																														
		
		ALACORDER beta 6.4
		by Sam Robson	


Welcome to Alacorder. Please select an operating mode:

A.	EXPORTING DETAILED CASE INFORMATION AS A TABLE

	Create detailed cases table with convictions, charges,
	fees, and voting rights restoration information. 

	Inputs:		PDF Directory (./path/to/pdfs) or Archive (.pkl, .csv, .xls, .json)
	Outputs:	Detailed Cases Table (.pkl, .csv, .xls, .dta, .json) or non-importable text file (.txt)

B.	CREATE A FULL TEXT ARCHIVE FROM PDF CASES

	Search directory for PDF files, collect full text and compress into archive.
	Archives can be processed into tables with mode A or manually with alac.

	Inputs:		PDF Directory (./path/to/pdfs)
	Outputs:	Archive (.pkl, .csv, .xls, .json) or non-importable text file (.txt)

>> Enter A or B:
''')

ab = "".join(input()).strip()

if ab == "A":
	print(f'''

	>>	Enter the input PDF directory or archive file path.
			ex.	/full/path/to/pdf/folder/
			ex.	/full/path/to/fulltextarchive.pkl

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
			ex.	/full/path/to/fulltextarchive.pkl
			ex.	/path/to/archive.csv

	>> Output path: 
''')
else:
	raise Exception("Not a valid input!")

xpath = "".join(input())
out_ext = xpath.split(".")[-1].strip()

if ab == "A" and in_ext == "directory":
	mode = "tables-from-directory"
	batch_size = 100
elif ab == "A" and in_ext == "pkl" or in_ext == "json" or in_ext == "csv" or in_ext == "xls":
	mode = "tables-from-archive"
	batch_size = 2000
elif ab == "B" and in_ext == "directory":
	mode = "archive-from-directory"
	batch_size = 100
else:
	raise Exception("Not a valid input.")


print(f'''

	.....

''')

if ab == "B":
	c = run.config(in_dir,xpath)
	run.writeArchive(c)
if ab == "A":
	c = run.config(in_dir,xpath)
	run.tempArchive(c)

if mode == "archive-from-directory":
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
		c = run.config(in_dir,xpath)
		run.writeTables(c)
	if info == "N":
		print(f'''
			Alacorder completed the task and will now quit.
			''')
