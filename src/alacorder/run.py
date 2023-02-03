# alacorder beta 0.5.72

import cython
import pyximport; pyximport.install()
import os
import sys
from io import StringIO
import glob
import re
import xlrd
import openpyxl
from math import floor
import datetime
import time
import pandas as pd
import numpy as np
import PyPDF2 as pdfs
from alacorder import alac

in_dir = ""
outp = ""
read = 0
tot_batches = 0
case_max = 0
batch = 0
plog = True
batches = pd.DataFrame()
bsize = 0
start_time = ""
m = ""

def start(in_path, out_path, mode, batch_size=10, print_log=True):

	global in_dir
	global outp
	global batch
	global read
	global plog
	global case_max
	global tot_batches
	global batches
	global start_time
	global bsize
	global m

	start_time = time.time()
	m = mode
	bsize = batch_size
	plog = print_log
	in_dir = in_path
	outp = out_path
	contents = pd.DataFrame()
	out_ext: str = out_path.split(".")[-1].strip()
	in_ext: str = in_path.split(".")[-1].strip() if len(in_path.split(".")[-1])<5 else "directory"
	# read directory
	if mode == "tables-from-directory" or mode == "archive-from-directory":
		contents['Path'] = glob.glob(in_dir + '**/*.pdf', recursive=True) # get all files
	elif mode == "tables-from-archive":
		contents['Path'] = glob.glob(in_dir + '**/*.pdf', recursive=True)
		batches = np.array_split(contents, 4)
		if in_ext == "pkl":
			contents = pd.read_pickle(in_dir)
		if in_ext == "xls":
			contents = pd.read_excel(in_dir, "text_from_pdf",names=['Path','AllPagesText'])
		if in_ext == "json":
			contents = pd.read_json(in_dir)
		if in_ext == "csv":
			contents = pd.read_csv(in_dir, escapechar='\\')
		contents = contents.drop_duplicates()
	else:
		raise Exception(f"Error: mode attribute {mode} not found!") 
	if len(contents) == 0:
		raise Exception(f"Error: no cases found in input directory!")

	case_max = contents.shape[0]
	try:
		batches = np.array_split(contents, case_max / batch_size)
	except ValueError:
		batches = [contents]
	tot_batches = len(batches)
	print(batches)
	
	# Print initial details: total exports, batch size, mode 

	if mode == "archive-from-directory":
		archive_from_directory(in_ext, out_ext)
	if mode == "tables-from-archive":
		tables_from_archive(in_ext, out_ext)
	if mode == "tables-from-directory":
		tables_from_directory(in_ext, out_ext)
	batch = 0

def log_complete(tostr=""):
	global batches
	global batch
	global start_time
	completion_time = time.time()
	elapsed = completion_time - start_time
	cases_per_sec = case_max/elapsed
	if m == "archive-from-directory":
		pmode = "Creating full text archive from PDF directory..."
	if m == "tables-from-archive":
		pmode = "Processing archive into detailed case information table..."
	if m == "tables-from-directory":
		pmode = "Collecting detailed case information from directory contents..."
	print(tostr)
	print(f'''
    ___    __                          __         
   /   |  / /___ __________  _________/ /__  _____
  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																										
	
	ALACORDER beta 0.5.72
	by Sam Robson	

	Searching {in_dir} 
	Writing to {outp} 
	{pmode}

	TASK SUCCEEDED ({case_max}/{case_max})
	Completed export in {elapsed:.2f} seconds ({cases_per_sec:.2f}/sec)

''') 

def console_log(tostr=""):
	global batches
	global batch
	total = len(batches)
	if plog == True:
		print(tostr)
		print(f'''
	    ___    __                          __         
	   /   |  / /___ __________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																											
		
		ALACORDER beta 0.5.72
		by Sam Robson	

		Searching {in_dir} 
		Writing to {outp} 

		Exported {batch*bsize} of {case_max}

	''') 

	if plog == False:
		print(f'''\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
		    ___    __                          __         
		   /   |  / /___ __________  _________/ /__  _____
		  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
		 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
		/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																												
			
			ALACORDER beta 0.5.72
			by Sam Robson	

			Searching {in_dir} 
			Writing to {outp} 

			Exported {batch*bsize} of {case_max}

		''') 

## BATCH WRITER FUNCTIONS
#  Each corresponds to a different mode - add more modes and settings via start()
#  Only one mode runs at a time
#  Process cases, print logs, concat to global, write

# in_exts: directory, pdf
# out_exts: xls, pkl, json, csv

def archive_from_directory(in_ext: str, out_ext: str):
	global batches
	global batch
	outputs = pd.DataFrame()
	if in_ext == "directory":
		for b in batches:
			# get all pages, add to all df, write to pickle
			b['AllPagesText'] = b['Path'].map(lambda x: str(alac.getPDFText(x)))
			b['Timestamp'] = time.time()
			outputs = pd.concat([outputs, b],ignore_index=False)
			batch += 1
			outputs.fillna('',inplace=True)
			if out_ext == "xls":
				with pd.ExcelWriter(outp) as writer:
					outputs.to_excel(writer, sheet_name="text_from_pdf")
			elif out_ext == "pkl":
				outputs.to_pickle(outp)
			elif out_ext == "json":
				outputs.to_json(outp)
			elif out_ext == "csv":
				outputs.to_csv(outp,escapechar='\\')
			elif out_ext == "md":
				outputs.to_markdown(outp)
			elif out_ext == "txt":
				outputs.to_string(outp)
			elif out_ext == "dta":
				outputs.to_stata(outp)
			else:
				raise Exception("Output file extension not supported! Must output to .xls, .pkl, .json, or .csv")
			console_log(b['Path'])
		log_complete()
		batch = 0
	else:
		raise Exception("Input path not supported! Must include full path to directory of PDF cases")

def tables_from_archive(in_ext: str, out_ext: str):
	global batches
	global batch
	outputs = pd.DataFrame()
	fees = pd.DataFrame()
	charges = pd.DataFrame()
	if in_ext == "directory":
		raise Exception("Directories not supported in this mode!")
	else:
		pass
	for b in batches:
		b['AllPagesText'] = b['Path'].map(lambda x: alac.getPDFText(x))
		b['FastCaseInfo'] = b['AllPagesText'].map(lambda x: alac.getCaseInfo(x))
		b['CaseNumber'] = b['FastCaseInfo'].map(lambda x: x[0])
		b['Name'] = b['FastCaseInfo'].map(lambda x: x[1])
		b['Alias'] = b['FastCaseInfo'].map(lambda x: x[2])
		b['DOB'] = b['FastCaseInfo'].map(lambda x: x[3])
		b['Race'] = b['FastCaseInfo'].map(lambda x: x[4])
		b['Sex'] = b['FastCaseInfo'].map(lambda x: x[5])
		b['Address'] = b['FastCaseInfo'].map(lambda x: x[6])
		b['Phone'] = b['FastCaseInfo'].map(lambda x: x[7])
		b['ChargesOutputs'] = b.index.map(lambda x: alac.getCharges(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
		b['DispositionCharges'] = b['ChargesOutputs'].map(lambda x: x[1])
		b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
		b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
		b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
		b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
		b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
		b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
		b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
		b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
		b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
		b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
		b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
		b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
		b['ChargeCodes'] = b['ChargesOutputs'].map(lambda x: x[14])
		b['ConvictionCodes'] = b['ChargesOutputs'].map(lambda x: x[15])
		b['FeeOutputs'] = b.index.map(lambda x: alac.getFeeSheet(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
		b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
		b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
		b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
		b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
		b['FeeSheet'] = b.index.map(lambda x: b['FeeOutputs'][x][5])
		feesheet = b[['CaseNumber','FeeSheet']]
		b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
		chargestab = b[['CaseNumber','ChargesTable']]
		b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))
		console_log(feesheet)
		console_log(chargestab)
		b.drop(columns=['AllPagesText','FastCaseInfo','ChargesOutputs','FeeOutputs','TotalD999','ChargesTable','FeeSheet'],inplace=True)
		outputs = pd.concat([outputs, b],ignore_index=True)
		fees = pd.concat([fees, feesheet],ignore_index=True)
		charges = pd.concat([charges, chargestab],ignore_index=True)
		outputs = outputs.infer_objects()
		outputs.fillna('',inplace=True)
		batch += 1
		console_log(outputs[['CaseNumber','Name','DispositionCharges']])
		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(outp) as writer:
				outputs.to_excel(writer, sheet_name="cases-table")
				fees.to_excel(writer, sheet_name="fees-table")
				charges.to_excel(writer, sheet_name="charges-table")
		elif out_ext == "pkl":
			outputs.to_pickle(outp)
		elif out_ext == "json":
			outputs.to_json(outp)
		elif out_ext == "csv":
			outputs.to_csv(outp,escapechar='\\')
		elif out_ext == "md":
			outputs.to_markdown(outp)
		elif out_ext == "txt":
			outputs.to_string(outp)
		elif out_ext == "dta":
			outputs.to_stata(outp)
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .pkl, .json, or .csv")
			'''
		b['AllPagesText'] = b['Path'].map(lambda x: alac.getPDFText(x))
		b['FastCaseInfo'] = b['AllPagesText'].map(lambda x: alac.getCaseInfo(x))
		b['CaseNumber'] = b['FastCaseInfo'].map(lambda x: x[0])
		b['Name'] = b['FastCaseInfo'].map(lambda x: x[1])
		b['Alias'] = b['FastCaseInfo'].map(lambda x: x[2])
		b['DOB'] = b['FastCaseInfo'].map(lambda x: x[3])
		b['Race'] = b['FastCaseInfo'].map(lambda x: x[4])
		b['Sex'] = b['FastCaseInfo'].map(lambda x: x[5])
		b['Address'] = b['FastCaseInfo'].map(lambda x: x[6])
		b['Phone'] = b['FastCaseInfo'].map(lambda x: x[7])
		b['ChargesOutputs'] = b.index.map(lambda x: alac.getCharges(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
		b['DispositionCharges'] = b['ChargesOutputs'].map(lambda x: x[1])
		b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
		b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
		b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
		b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
		b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
		b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
		b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
		b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
		b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
		b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
		b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
		b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
		b['ChargeCodes'] = b['ChargesOutputs'].map(lambda x: x[14])
		b['ConvictionCodes'] = b['ChargesOutputs'].map(lambda x: x[15])
		b['FeeOutputs'] = b.index.map(lambda x: alac.getFeeSheet(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
		b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
		b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
		b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
		b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
		b['FeesTable'] = b['FeeOutputs'].map(lambda x: x[5])
		b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[0])
		b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[6][0])
		b.drop(columns=['AllPagesText','FastCaseInfo','ChargesOutputs','FeeOutputs','TotalD999','FeesTable'],inplace=True)
		outputs = pd.concat([outputs, b],ignore_index=True)
		fees = pd.concat([fees, b['FeeSheet']],ignore_index=True)
		charges = pd.concat([charges, b['ChargesTable']],ignore_index=True)
		outputs = outputs.infer_objects()
		outputs.fillna('',inplace=True)
		batch += 1
		console_log("")
		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(outp) as writer:
				outputs.to_excel(writer, sheet_name="cases-table")
				# fees.to_excel(writer, sheet_name="fees-table")
				# charges.to_excel(writer, sheet_name="charges-table")
		elif out_ext == "pkl":
			outputs.to_pickle(outp)
		elif out_ext == "json":
			outputs.to_json(outp)
		elif out_ext == "csv":
			outputs.to_csv(outp,escapechar='\\')
		elif out_ext == "md":
			outputs.to_markdown(outp)
		elif out_ext == "txt":
			outputs.to_string(outp)
		elif out_ext == "dta":
			outputs.to_stata(outp)
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .pkl, .json, or .csv")
	log_complete()
	batch = 0
'''
def tables_from_directory(in_ext: str, out_ext: str):
	global batches
	global batch
	outputs = pd.DataFrame()
	fees = pd.DataFrame()
	charges = pd.DataFrame()
	for b in batches:
		b['AllPagesText'] = b['Path'].map(lambda x: alac.getPDFText(x))
		b['FastCaseInfo'] = b['AllPagesText'].map(lambda x: alac.getCaseInfo(x))
		b['CaseNumber'] = b['FastCaseInfo'].map(lambda x: x[0])
		b['Name'] = b['FastCaseInfo'].map(lambda x: x[1])
		b['Alias'] = b['FastCaseInfo'].map(lambda x: x[2])
		b['DOB'] = b['FastCaseInfo'].map(lambda x: x[3])
		b['Race'] = b['FastCaseInfo'].map(lambda x: x[4])
		b['Sex'] = b['FastCaseInfo'].map(lambda x: x[5])
		b['Address'] = b['FastCaseInfo'].map(lambda x: x[6])
		b['Phone'] = b['FastCaseInfo'].map(lambda x: x[7])
		b['ChargesOutputs'] = b.index.map(lambda x: alac.getCharges(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
		b['DispositionCharges'] = b['ChargesOutputs'].map(lambda x: x[1])
		b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
		b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
		b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
		b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
		b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
		b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
		b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
		b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
		b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
		b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
		b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
		b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
		b['ChargeCodes'] = b['ChargesOutputs'].map(lambda x: x[14])
		b['ConvictionCodes'] = b['ChargesOutputs'].map(lambda x: x[15])
		b['FeeOutputs'] = b.index.map(lambda x: alac.getFeeSheet(b['AllPagesText'][x], b['CaseNumber'][x]))
		b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
		b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
		b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
		b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
		b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
		b['FeeSheet'] = b.index.map(lambda x: b['FeeOutputs'][x][5])
		feesheet = b[['CaseNumber','FeeSheet']]
		b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
		chargestab = b[['CaseNumber','ChargesTable']]
		b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))
		console_log(feesheet)
		console_log(chargestab)
		b.drop(columns=['AllPagesText','FastCaseInfo','ChargesOutputs','FeeOutputs','TotalD999','ChargesTable','FeeSheet'],inplace=True)
		outputs = pd.concat([outputs, b],ignore_index=True)
		fees = pd.concat([fees, feesheet],ignore_index=True)
		charges = pd.concat([charges, chargestab],ignore_index=True)
		outputs = outputs.infer_objects()
		outputs.fillna('',inplace=True)
		batch += 1
		console_log(outputs[['CaseNumber','Name','DispositionCharges']])
		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(outp) as writer:
				outputs.to_excel(writer, sheet_name="cases-table")
				fees.to_excel(writer, sheet_name="fees-table")
				charges.to_excel(writer, sheet_name="charges-table")
		elif out_ext == "pkl":
			outputs.to_pickle(outp)
		elif out_ext == "json":
			outputs.to_json(outp)
		elif out_ext == "csv":
			outputs.to_csv(outp,escapechar='\\')
		elif out_ext == "md":
			outputs.to_markdown(outp)
		elif out_ext == "txt":
			outputs.to_string(outp)
		elif out_ext == "dta":
			outputs.to_stata(outp)
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .pkl, .json, or .csv")
	log_complete()
	batch = 0
'''
		b['AllPagesText'] = b['Path'].map(lambda x: alac.getPDFText(x))
		b['FastCaseInfo'] = b['AllPagesText'].map(lambda x: alac.getCaseInfo(x))
		b['CaseNumber'] = b['FastCaseInfo'].map(lambda x: x[0])
		b['Name'] = b['FastCaseInfo'].map(lambda x: x[1])
		b['Alias'] = b['FastCaseInfo'].map(lambda x: x[2])
		b['DOB'] = b['FastCaseInfo'].map(lambda x: x[3])
		b['Race'] = b['FastCaseInfo'].map(lambda x: x[4])
		b['Sex'] = b['FastCaseInfo'].map(lambda x: x[5])
		b['Address'] = b['FastCaseInfo'].map(lambda x: x[6])
		b['Phone'] = b['FastCaseInfo'].map(lambda x: x[7])
		b['ChargesOutputs'] = b['AllPagesText'].map(lambda x: alac.getCharges(x))
		b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
		b['DispositionCharges'] = b['ChargesOutputs'].map(lambda x: x[1])
		b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
		b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
		b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
		b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
		b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
		b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
		b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
		b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
		b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
		b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
		b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
		b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
		b['FeeOutputs'] = b['AllPagesText'].map(lambda x: alac.getFeeSheet(x))
		b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
		b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
		b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
		b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
		b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
		b['FeesTable'] = b['FeeOutputs'].map(lambda x: "\n".join(x[5]))
		b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))
		b.drop(columns=['AllPagesText','FastCaseInfo','ChargesOutputs','FeeOutputs','FeesTable','FeeSheet'],inplace=True)
		outputs = pd.concat([outputs, b],ignore_index=True)
		outputs.fillna('',inplace=True)
		# fees = pd.concat([fees, b['FeesTable']],ignore_index=False)
		# charges = pd.concat([charges, b['ChargesTable']],ignore_index=False)
		'''

