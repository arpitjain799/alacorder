# test.py - new cites test
# alacorder beta 6.4

# - add parentheses and decimals to cite DONE 
# - clean up descriptions DONE
# - change phone number to int DONE
# - change num to int
# - make archive and tables at same time mode 

import cython
import cython
import pyximport; pyximport.install()
import os
import sys
from io import StringIO
import glob
import re
import xlrd
import openpyxl
import math
import datetime
import time
import pandas as pd
import numpy as np
import PyPDF2 as pypdf
import run
import alac



def newCites(path: str):
	text = alac.getPDFText(path)
	case_num: str = re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip() 
	ch = re.findall(r'(\d{3}\s{1}.{1,100}?.{3}-.{3}-.{3}.{10,75})', str(text), re.MULTILINE)
	c = []
	for a in ch:
		b = str(a).replace("Sentences","").replace("Sentence 1","").replace("SentencesSentence 1","").replace("Sentence","").replace("Financial","")
		if ":" in b:
			continue
		c.append(re.sub(r'[a-z]*','', b))
	cind = range(0, len(c))
	charges = pd.DataFrame({'Charges': c,'CiteFirst': '', 'CiteSecond': '', 'CaseNumber': case_num},index=cind)
	try:
		charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([^\s]{3}-[^\s]{3}-[^\s]{3}[^s]{0,3}?\)*)', x).group()) #if bool(re.search(r'([^\s]{3}-[^\s]{3}-[^\s]{3}[^s]{0,3}?\)*)', x)) else "")
	except (AttributeError, IndexError):
		try:
			charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'(.{3}-.{3}-.{3})',x).group())
		except (AttributeError, IndexError):
			print("MISSED CITE: " + charges.to_string()) 
	try:
		charges['parentheses'] = charges['Charges'].map(lambda x: re.search(r'(\([A-Z]\))', x).group())
		charges['Cite'] = charges['Cite'] + charges['parentheses']
	except (AttributeError, IndexError):
		pass
	try:
		charges['decimals'] = charges['Charges'].map(lambda x: re.search(r'(\.[0-9])', x).group())
		charges['Cite'] = charges['Cite'] + charges['decimals']
		#print("\n\n\n")
	except (AttributeError, IndexError):
		pass
	
	## START DESC TEST

	charges['TypeDescription'] = charges['Charges'].map(lambda x: re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x).group() if bool(re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x)) else "")
	charges['Category'] = charges['Charges'].map(lambda x: re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x).group() if bool(re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x)) else "")
	charges['Description'] = charges['Charges'].map(lambda x: x[9:-1])
	charges['Description'] = charges['Description'].str.split(r'([^s]{3}-.{3}-.{3})', regex=True)
	charges['Description'] = charges['Description'].map(lambda x: ascii(x[2]).strip() if bool(re.search(r'(\d{2}/\d{2}/\d{4})|\#|MISDEMEANOR|WAIVED|DISMISSED|CONVICTED|PROSS', ascii(x[0]))) else ascii(x[0]).strip())



	




desc_test = run.config("/Users/samuelrobson/Desktop/tutarchive.pkl", "/Users/samuelrobson/Desktop/tutarchive.xls")

run.writeTables(desc_test)
