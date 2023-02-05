# alacorder beta 6.4

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
import PyPDF2 as pdfs
from alacorder import alac
import warnings

# -> dict {mode, batch_size, case_max, tot_batches, batches: List[List[paths: str]]} 
# -> start() takes one argument - Config() - sets global values, gets to work 
# -> Config:

def config(in_path: str, out_path: str, flags="", print_log=True, warn=False): 

	# Get extensions
	out_ext: str = out_path.split(".")[-1].strip()
	in_ext: str = in_path.split(".")[-1].strip() if len(in_path.split(".")[-1])<5 else "directory" 

	# Check if input path is valid
	if in_ext != "directory" and in_ext != "pkl" and in_ext != "csv" and in_ext != "xls" and in_ext != "json":
		raise Exception("Input path must be to/pdf/directory/, (archive).csv, (archive).xls, (archive).json, or (archive).pkl!")
	if os.path.exists(in_path) == False:
		raise Exception("Input path does not exist!")

	# Check if output path is valid
	if out_ext != "pkl" and out_ext != "txt" and out_ext != "csv" and out_ext != "xls" and out_ext != "json" and out_ext != "dta":
		raise Exception("Output path must be .csv, .xls, .json, or .pkl! (.pkl only for full text archives)")

	# Set read, write modes, contents
	if in_ext == "directory" and out_ext == "pkl": # from dir to pkl = make archive
		make = "archive"
		origin = "directory"
		contents = glob.glob(in_path + '**/*.pdf', recursive=True)
	elif in_ext == "directory" and bool(out_ext == "xls" or out_ext == "json" or out_ext == "csv" or out_ext == "txt" or out_ext == "dta"):
		make = "table"
		origin = "directory"
		contents = glob.glob(in_path + '**/*.pdf', recursive=True)
	elif in_ext == "pkl":
		make = "table"
		origin = "archive"
		contents = pd.read_pickle(in_path)['Path']
	elif in_ext == "csv":
		make = "table"
		origin = "archive"
		contents = pd.read_csv(in_path).tolist()
	elif in_ext == "xls":
		make = "table"
		origin = "archive"
		contents = pd.read_excel(in_path,sheet_name="text_from_pdf")
	elif in_ext == "json": 
		make = "table"
		origin = "archive"
		contents = pd.read_pickle(in_path)
	else:
		raise Exception("Not supported. Refer to alacorder documentation at https://github.com/sbrobson959/alacorder for supported input and outputs.")

	# verify directory input has content
	if len(contents)==0:
		raise Exception("No cases found in input path! (" + in_path + ")")

	if origin == "archive":
		batchsize = 250
	if origin == "directory":
		batchsize = 100

	case_max = len(contents)
	tot_batches = math.ceil(case_max / batchsize)

	batches = np.array_split(contents, tot_batches)

	if print_log == True:
		print(f"Initial confuration succeeded!\n\n{in_path} ----> {out_path}\n\n{case_max} cases in {tot_batches} batches")

	conf = pd.Series({
		'in_path': in_path,
		'out_path': out_path,
		'in_ext': in_ext,
		'out_ext': out_ext,
		'origin': origin,
		'make': make,
		'contents': contents,
		'batches': batches,
		'case_max': case_max,
		'tot_batches': tot_batches,
		'batchsize': batchsize,
		'print_log': print_log,
		'warnings': warn
	})
	
	return conf

def log_complete(conf, start_time):
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	bsize = conf['batchsize']
	completion_time = time.time()
	elapsed = completion_time - start_time
	cases_per_sec = case_max/elapsed
	print(f'''
    ___    __                          __         
   /   |  / /___ __________  _________/ /__  _____
  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																										
	
	ALACORDER beta 6.4
	by Sam Robson	

	Searching {path_in} 
	Writing to {path_out} 

	TASK SUCCEEDED ({case_max}/{case_max} cases)
	Completed export in {elapsed:.2f} seconds ({cases_per_sec:.2f}/sec)

''') 

def console_log(conf, on_batch: int, to_str: str):
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	bsize = conf['batchsize']
	plog = conf['print_log']
	if plog == True:
		print(to_str)
		print(f'''
	    ___    __                          __         
	   /   |  / /___ __________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																											
		
		ALACORDER beta 6.4
		by Sam Robson	

		Searching {path_in} 
		Writing to {path_out} 

		Text extracted from {on_batch*bsize} of {case_max}...
		Waiting for text extraction to process tables...

	''') 

	if plog == False:
		print(f'''\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
		    ___    __                          __         
		   /   |  / /___ __________  _________/ /__  _____
		  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
		 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
		/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																												
			
			ALACORDER beta 6.4
			by Sam Robson	

			Searching {path_in} 
			Writing to {path_out} 

			Text extracted from {on_batch*bsize} of {case_max}...
			Waiting for text extraction to process tables...
		''') 

def console_logTA(conf, on_batch: int, to_str: str):
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	bsize = conf['batchsize']
	plog = conf['print_log']
	if plog == True:
		print(to_str)
		print(f'''
	    ___    __                          __         
	   /   |  / /___ __________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																											
		
		ALACORDER beta 6.4
		by Sam Robson	

		Searching {path_in} 
		Writing to {path_out} 

		Text extracted from {on_batch*bsize} of {case_max}...
		Waiting for text extraction to process tables...

	''') 

	if plog == False:
		print(f'''\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
		    ___    __                          __         
		   /   |  / /___ __________  _________/ /__  _____
		  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
		 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
		/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     
																																												
			
			ALACORDER beta 6.4
			by Sam Robson	

			Searching {path_in} 
			Writing to {path_out} 

			Text extracted from {on_batch*bsize} of {case_max}...
			Waiting for text extraction to process tables...
		''') 

def tempArchive(conf):

	path_in = conf['in_path']
	start_time = time.time()
	path_out = conf['in_path'] + "alac_temp_" + str(start_time) + ".pkl"
	case_max = conf['case_max']
	tot_batches = conf['tot_batches']
	batchsize = conf['batchsize']
	batches = conf['batches']
	contents = conf['contents']
	in_ext = conf['in_ext']
	out_ext = conf['out_ext']
	print_log = conf['print_log']
	warn = conf['warnings']

	if warn == False:
		warnings.filterwarnings("ignore")

	
	outputs = pd.DataFrame()
	on_batch = 0

	for b in batches:

		paths = pd.Series(b)
		allpagestext = pd.Series(b).map(lambda x: alac.getPDFText(x))
		timestamp = time.time()

		c = pd.DataFrame({
			'Path': paths,
			'AllPagesText': allpagestext,
			'Timestamp': timestamp
			})
		outputs = pd.concat([outputs, c],ignore_index=True)
		on_batch += 1
		outputs.fillna('',inplace=True)

		if out_ext == "pkl":
			outputs.to_pickle(path_out)

		console_logTA(conf, on_batch, "")
		outputs.to_pickle(path_out)

	log_complete(conf, start_time)
	on_batch = 0
	tab_conf = config(path_out, conf['out_path'])
	writeTables(tab_conf)

def writeArchive(conf):

	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	tot_batches = conf['tot_batches']
	batchsize = conf['batchsize']
	batches = conf['batches']
	contents = conf['contents']
	in_ext = conf['in_ext']
	out_ext = conf['out_ext']
	print_log = conf['print_log']
	warn = conf['warnings']

	if warn == False:
		warnings.filterwarnings("ignore")

	start_time = time.time()
	outputs = pd.DataFrame()
	on_batch = 0

	for b in batches:

		paths = pd.Series(b)
		allpagestext = pd.Series(b).map(lambda x: alac.getPDFText(x))
		timestamp = time.time()

		c = pd.DataFrame({
			'Path': paths,
			'AllPagesText': allpagestext,
			'Timestamp': timestamp
			})
		outputs = pd.concat([outputs, c],ignore_index=True)
		on_batch += 1
		outputs.fillna('',inplace=True)

		if out_ext == "pkl":
			outputs.to_pickle(path_out)
		elif out_ext == "json":
			outputs.to_json(path_out)
		elif out_ext == "csv":
			outputs.to_csv(path_out,escapechar='\\')
		elif out_ext == "md":
			outputs.to_markdown(path_out)
		elif out_ext == "txt":
			outputs.to_string(path_out)
		elif out_ext == "dta":
			outputs.to_stata(path_out)
		console_log(conf, on_batch, "")
	log_complete(conf, start_time)
	on_batch = 0

def writeTables(conf):
	batches = conf['batches']
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	tot_batches = conf['tot_batches']
	batchsize = conf['batchsize']
	in_ext = conf['in_ext']
	out_ext = conf['out_ext']
	print_log = conf['print_log']
	warn = conf['warnings']
	contents = conf['contents']
	batches = conf['batches']
	if warn == False:
		warnings.filterwarnings("ignore")
	start_time = time.time()
	on_batch = 0
	outputs = pd.DataFrame()

	fees = pd.DataFrame({'CaseNumber': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
	charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) # charges = pd.DataFrame() # why is this here
	for i, c in enumerate(batches):
		b = pd.DataFrame()
		b['AllPagesText'] = pd.Series(c).map(lambda x: alac.getPDFText(x))
		b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: alac.getCaseInfo(x))
		b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
		b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
		b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
		b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
		b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
		b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
		b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
		b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
		b['ChargesOutputs'] = b.index.map(lambda x: alac.getCharges(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
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
		b['FeeOutputs'] = b.index.map(lambda x: alac.getFeeSheet(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
		b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
		b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
		b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
		b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
		b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
		b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])


		feesheets = b['FeeOutputs'].map(lambda x: x[6]) # -> pd.Series(df, df, df)
		feesheets = feesheets.dropna() # drop empty 
		feesheets = feesheets.tolist() # convert to list -> [df, df, df]
		feesheets = pd.concat(feesheets,axis=0,ignore_index=True) # add all dfs in batch -> df
		fees = pd.concat([fees, feesheets],axis=0,ignore_index=True)
		fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'ignore'))


		chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
		chargetabs = chargetabs.dropna()
		chargetabs = chargetabs.tolist()
		chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
		charges = pd.concat([charges, chargetabs],axis=0,ignore_index=True)
		console_log(conf, on_batch, chargetabs.to_string())

		b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
		b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))
		b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','TotalD999','ChargesTable','FeeSheet'],inplace=True)
		outputs = pd.concat([outputs, b],ignore_index=True)
		
		outputs.fillna('',inplace=True)
		charges.fillna('',inplace=True)
		fees.fillna('',inplace=True)

		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(path_out) as writer:
				outputs.to_excel(writer, sheet_name="cases-table")
				fees.to_excel(writer, sheet_name="fees-table")
				charges.to_excel(writer, sheet_name="charges-table")
		elif out_ext == "pkl":
			outputs.to_pickle(path_out)
		elif out_ext == "json":
			outputs.to_json(path_out)
		elif out_ext == "csv":
			outputs.to_csv(path_out,escapechar='\\')
		elif out_ext == "md":
			outputs.to_markdown(path_out)
		elif out_ext == "txt":
			outputs.to_string(path_out)
		elif out_ext == "dta":
			outputs.to_stata(path_out)
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .pkl, .json, or .csv")
		on_batch += 1
		console_log(conf, on_batch,'')
	log_complete(conf, start_time)
	on_batch = 0
