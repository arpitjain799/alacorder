
#         ___    __                          __         
#        /   |  / /___  _________  _________/ /__  _____
#       / /| | / / __ `/ ___/ __ \/ ___/ __  / _ \/ ___/
#      / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
#     /_/  |_/_/\__,_/\___/\____/_/   \__,_/\___/_/     
#
#
#       ALACORDER beta 7.4.9.9.7
#       by Sam Robson
#

import os
import sys
import glob
import re
import math
import numexpr
import xarray
import bottleneck
import numpy as np
import pandas as pd
import xlrd
import openpyxl
import datetime
import time
import warnings
import PyPDF2
from io import StringIO

# CONFIG
#conf = pd.Series({'in_path': in_path, 'out_path': out_path, 'in_ext': in_ext, 'out_ext': out_ext, 'archive': fromArchive, 'origin': origin, 'make': make, 'contents': contents, 'batches': batches, 'case_max': case_max, 'tot_batches': tot_batches, 'batchsize': batchsize, 'print_log': print_log, 'warnings': warn, 'flags': flags, 'save_archive': save_archive})

def config(in_path, out_path="", flags="", print_log=True, warn=False, save_archive=False, set_batch=0, max_cases=0): 

	path_input = True if isinstance(in_path,str) else False
	input_cap = True if max_cases > 0 else False
	out_ext: str = out_path.split(".")[-1].strip()
	
	if path_input == True:
		in_ext: str = in_path.split(".")[-1].strip() if len(in_path.split(".")[-1])<5 else "directory" 
	else:
		in_ext = "object"
		in_path = "no_import"
		origin = "archive"
		make = "table"

	if out_ext == "txt":
		print("Warning: Text files cannot be reimported to alacorder!")

	if out_path == "":
		out_ext = "no_export"

	# Check if input path is valid
	if in_ext != "directory" and in_ext != "pkl" and in_ext != "csv" and in_ext != "xls" and in_ext != "json" and in_ext != "xz" and in_ext != "pdf":
		raise Exception("Input path must be to/pdf/directory/, (archive).csv, (archive).xls, (archive).json, (archive).pkl, or (archive).pkl.xz")
	if os.path.exists(in_path) == False and in_ext != "object":
		raise Exception("Input path does not exist!")

	# Check if output path is valid
	if out_ext != "pkl" and out_ext != "txt" and out_ext != "csv" and out_ext != "xls" and out_ext != "json" and out_ext != "dta" and out_ext != "xz" and out_ext != "no_export":
		raise Exception("Output path must be .csv, .xls, .json, or .pkl.xz! (.pkl.xz only for full text archives)")

	fromArchive = False
	make = ""
	origin = ""
	contents = []
	paths = []

	# Set read, write modes, contents
	if in_ext == "directory" and bool(out_ext == "pkl" or out_ext == "xz" or out_ext == "txt"): 
		make = "archive"
		origin = "directory"
		paths = glob.glob(in_path + '**/*.pdf', recursive=True)
		if print_log == True:
			print(paths)
	if in_ext == "pdf":
		in_ext = "directory"
		paths = [in_path]
		origin = "directory"
		make = "archive"
		if print_log == True:
			print(paths)
	if in_ext == "txt":
		origin = "archive"
		make = "table"
		with open(in_path,'r') as textfile:
			contents = textfile.read()
			if print_log == True:
				print(contents)
	if in_ext == "directory" and bool(out_ext == "xls" or  out_ext == "no_export" or out_ext == "json" or out_ext == "csv" or out_ext == "txt" or out_ext == "dta"):
		make = "table"
		origin = "directory"
		paths = glob.glob(in_path + '**/*.pdf', recursive=True)
		if print_log == True:
			print(paths)
	if in_ext == "pkl":
		make = "table"
		origin = "archive"
		try:
			contents = pd.read_pickle(in_path)['AllPagesText']
			fromArchive = True
			if print_log == True:
				print(contents)
		except KeyError:
			pass
	if in_ext == "xz":
		make = "table"
		origin = "archive"
		contents = pd.read_pickle(in_path,compression="xz")['AllPagesText']
		fromArchive = True
		if print_log == True:
			print(contents)
	if in_ext == "object" and origin == "archive":
		contents = in_path['AllPagesText']
		if print_log == True:
			print(contents)
	if out_ext == "no_export" and origin == "archive":
		try:
			contents = in_path['AllPagesText']
			if print_log == True:
				print(contents)
		except KeyError:
			try:
				contents = str(in_path)
				if print_log == True:
					print(contents)
			except (KeyError, TypeError):
				raise Exception("Could not find series \'All Pages Text\' in archive file. Create new archive, check version compatability, or edit pickle archive using pandas to reattempt.")

	if input_cap == True:
		contents = contents[0:max_cases]

	case_max = len(contents)

	if pd.Series(contents).shape == 0:
		raise Exception("No cases found in input path! (" + in_path + ")")

	if origin == "archive" and set_batch == 0: # set batch
		batchsize = 1000
	if origin == "directory" and set_batch == 0:
		batchsize = 500
	if set_batch > 0:
		batchsize = set_batch

	tot_batches = math.ceil(case_max / batchsize)
	try:
		batches = np.array_split(contents, tot_batches)
	except ValueError:
		pass
	batchsize = len(batches[0])
	
	write = True if out_ext != "no_export" else False

	if print_log == True:
		print(f"\nInitial configuration succeeded!\n\nIn:   {in_path} \nOut:    {out_path}\n\n{case_max} cases...\n")

	conf = pd.Series({
		'in_path': in_path,
		'out_path': out_path,
		'in_ext': in_ext,
		'out_ext': out_ext,
		'is_text': fromArchive,
		'origin': origin,
		'make': make,
		'contents': contents,
		'paths': paths,
		'batches': batches,
		'case_max': case_max,
		'write': write,
		'tot_batches': tot_batches,
		'batchsize': batchsize,
		'print_log': print_log,
		'warnings': warn,
		'flags': flags,
		'save_archive': save_archive
	})
	
	return conf

# WRITE METHODS: Map across paths/text in config

def writeArchive(conf):
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	tot_batches = conf['tot_batches']
	batchsize = conf['batchsize']
	batches = conf['batches']
	paths = conf['paths']
	contents = conf['contents']
	in_ext = conf['in_ext']
	out_ext = conf['out_ext']
	print_log = conf['print_log']
	warn = conf['warnings']

	if warn == False:
		warnings.filterwarnings("ignore")

	start_time = time.time()
	outputs = pd.DataFrame()

	exptime = time.time()
	paths = pd.Series(contents)
	allpagestext = paths.map(lambda x: getPDFText(x))
	timestamp = time.time()

	c = pd.DataFrame({
		'Path': paths,
		'AllPagesText': allpagestext,
		'Timestamp': timestamp
		})

	outputs = pd.concat([outputs, c],ignore_index=True)
	outputs.fillna('',inplace=True)

	if out_ext == "pkl":
		outputs.to_pickle(path_out+".xz",compression="xz")
	if out_ext == "xz":
		outputs.to_pickle(path_out,compression="xz")
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
	elif out_ext == "no_export" or print_log == True:
		print(outputs.to_string())
	log_complete(conf, start_time)
	return outputs

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
	paths = conf['paths']
	batches = conf['batches']
	save_archive = conf['save_archive']
	from_archive = conf['is_text']
	if warn == False:
		warnings.filterwarnings("ignore")
	start_time = time.time()
	outputs = pd.DataFrame()

	fees = pd.DataFrame({'CaseNumber': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
	charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
	arch = pd.DataFrame({'Path':'','AllPagesText':'','Timestamp':''},index=[0])

	b = pd.DataFrame()
	exptime = time.time()

	if from_archive == True:
		b['AllPagesText'] = contents
	else:
		b['AllPagesText'] = pd.Series(paths).map(lambda x: getPDFText(x))

	b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
	b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
	b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
	b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
	b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
	b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
	b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
	b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
	b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
	b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
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
	b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
	b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
	b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
	b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
	b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
	b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
	b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])

	fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
	fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'ignore'))
	fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'ignore'))
	fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'ignore'))
	charges['Num'] = charges['Num'].map(lambda x: pd.to_numeric(x,'ignore'))

	feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
	feesheet = feesheet.dropna() 
	fees = fees.dropna()
	feesheet = feesheet.tolist() # -> [df, df, df]
	
	try:
		feesheet = pd.concat(feesheet,axis=0,ignore_index=True) #  -> batch df
	except ValueError:
		pass
	try:
		fees = fees.append(feesheet, ignore_index=True) # -> all fees df
	except ValueError:
		pass

	if print_log == True:
		print(fees)

	chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
	chargetabs = chargetabs.dropna()
	charges = charges.dropna()
	chargetabs = chargetabs.tolist()
	
	try:
		chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
	except ValueError:
		pass
	try:
		charges = charges.append(chargetabs,ignore_index=True)
	except ValueError:
		pass

	if print_log == True:
		print(charges)


	b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
	b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
	b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'ignore'))
	b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
	b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))


	if save_archive == True:
		timestamp = exptime
		ar = pd.DataFrame({
			'Path': pd.Series(paths),
			'AllPagesText': b['AllPagesText'],
			'Timestamp': timestamp
			},index=range(0,pd.Series(paths).shape[0]))
		arch = pd.concat([arch, ar],ignore_index=True)
		arch.fillna('',inplace=True)
		arch.dropna(inplace=True)
		arch.to_pickle(path_out+".pkl.xz",compression="xz")


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
		outputs.to_pickle(path_out+".xz",compression="xz")
	elif out_ext == "xz":
		outputs.to_pickle(path_out,compression="xz")
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
	elif out_ext == "no_export" or print_log == True:
		print(outputs, charges, fees)
	else:
		raise Exception("Output file extension not supported! Please output to .xls, .pkl, .json, or .csv")
		
	log_complete(conf, start_time)
	return [outputs, fees, charges]

def writeFees(conf):
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
	paths = conf['paths']
	contents = conf['contents']
	batches = conf['batches']
	from_archive = conf['is_text']
	if warn == False:
		warnings.filterwarnings("ignore")
	start_time = time.time()
	outputs = pd.DataFrame()

	fees = pd.DataFrame({'CaseNumber': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
	for i, c in enumerate(batches):
		exptime = time.time()
		b = pd.DataFrame()

		if from_archive == True:
			b['AllPagesText'] = contents
		else:
			b['AllPagesText'] = pd.Series(paths).map(lambda x: getPDFText(x))

		b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
		b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
		b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText, b.loc[x].CaseNumber))

		fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'ignore'))
		fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'ignore'))

		feesheet = b['FeeOutputs'].map(lambda x: x[6]) 

		feesheet= feesheet.dropna() # drop empty 
		fees=fees.dropna()
		feesheet = feesheet.tolist() # convert to list -> [df, df, df]
		feesheet = pd.concat(feesheet,axis=0,ignore_index=True) # add all dfs in batch -> df
		fees = fees.append(feesheet, ignore_index=True) 


		fees.fillna('',inplace=True)

		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(path_out) as writer:
				fees.to_excel(writer, sheet_name="fees-table")
		elif out_ext == "pkl":
			fees.to_pickle(path_out+".xz",compression="xz")
		elif out_ext == "xz":
			fees.to_pickle(path_out,compression="xz")
		elif out_ext == "json":
			fees.to_json(path_out)
		elif out_ext == "csv":
			fees.to_csv(path_out,escapechar='\\')
		elif out_ext == "md":
			fees.to_markdown(path_out)
		elif out_ext == "txt":
			fees.to_string(path_out)
		elif out_ext == "dta":
			fees.to_stata(path_out)
		elif out_ext == "no_export" and print_log == True:
			print(fees.to_string())
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .json, or .csv")
	log_complete(conf, start_time)
	return fees

def writeCharges(conf):
	batches = conf['batches']
	path_in = conf['in_path']
	path_out = conf['out_path']
	case_max = conf['case_max']
	tot_batches = conf['tot_batches']
	batchsize = conf['batchsize']
	in_ext = conf['in_ext']
	out_ext = conf['out_ext']
	print_log = conf['print_log']
	paths = conf['paths']
	warn = conf['warnings']
	contents = conf['contents']
	batches = conf['batches']
	flag = conf['flags']
	from_archive = conf['is_text']
	if warn == False:
		warnings.filterwarnings("ignore")
	start_time = time.time()
	outputs = pd.DataFrame()
	charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
	for i, c in enumerate(batches):
		exptime = time.time()
		b = pd.DataFrame()

		if from_archive == True:
			b['AllPagesText'] = contents
		else:
			b['AllPagesText'] = pd.Series(paths).map(lambda x: getPDFText(x))

		b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
		b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
		b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
		charges['Num'] = charges['Num'].map(lambda x: pd.to_numeric(x,'ignore'))

		
		chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
		chargetabs = chargetabs.dropna()

		charges = charges.dropna()
		chargetabs = chargetabs.tolist()
		chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
		charges = charges.append(chargetabs,ignore_index=True)
		charges.fillna('',inplace=True)

		if flag == "filing":
			is_disp = charges['Disposition']
			is_filing = is_disp.map(lambda x: False if x == True else True)
			charges = charges[is_disp]

		if flag == "disposition":
			is_disp = charges['Disposition']
			charges = charges[is_disp]

		# write 
		if out_ext == "xls":
			with pd.ExcelWriter(path_out) as writer:
				charges.to_excel(writer, sheet_name="charges-table")
		elif out_ext == "pkl":
			charges.to_pickle(path_out+".xz",compression="xz")
		elif out_ext == "xz":
			charges.to_pickle(path_out,compression="xz")
		elif out_ext == "json":
			charges.to_json(path_out)
		elif out_ext == "csv":
			charges.to_csv(path_out,escapechar='\\')
		elif out_ext == "md":
			charges.to_markdown(path_out)
		elif out_ext == "txt":
			charges.to_string(path_out)
		elif out_ext == "dta":
			charges.to_stata(path_out)
		elif out_ext == "no_export" or print_log == True:
			print(charges.to_string())
		else:
			raise Exception("Output file extension not supported! Please output to .xls, .json, or .csv")

	log_complete(conf, start_time)
	return charges


def parse(conf, method, status=''): 
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
	paths = conf['paths']
	batches = conf['batches']
	from_archive = conf['is_text']
	write = conf['write']
	if warn == False:
		warnings.filterwarnings("ignore")
	start_time = time.time()
	alloutputs = pd.Series()
	on_batch = 0
	uselist = False
	for i, c in enumerate(batches):
		exptime = time.time()
		b = pd.DataFrame()

		if from_archive == True:
			allpagestext = contents
		else:
			allpagestext = pd.Series(paths).map(lambda x: getPDFText(x))

		customoutputs = allpagestext.map(lambda x: method(x))
		alloutputs = alloutputs.append(customoutputs)
		
		if print_log == True or out_ext != "no_export":
			print(alloutputs)
		
		if write == True:
			if out_ext == "xls":
				with pd.ExcelWriter(path_out) as writer:
					alloutputs.to_excel(writer, sheet_name="output-table")
			elif out_ext == "pkl":
				alloutputs.to_pickle(path_out+".xz",compression="xz")
			elif out_ext == "xz":
				alloutputs.to_pickle(path_out,compression="xz")
			elif out_ext == "json":
				alloutputs.to_json(path_out)
			elif out_ext == "csv":
				alloutputs.to_csv(path_out,escapechar='\\')
			elif out_ext == "md":
				alloutputs.to_markdown(path_out)
			elif out_ext == "txt":
				alloutputs.to_string(path_out)
			elif out_ext == "dta":
				alloutputs.to_stata(path_out)
			elif out_ext == "no_export" or print_log == True:
				print(alloutputs.to_string())
			else:
				raise Warning("Batch export failed!")
		on_batch += 1
	log_complete(conf, start_time)
	on_batch = 0
	return alloutputs

# CASE METHODS 

def getPDFText(path: str) -> str:
	text = ""
	pdf = PyPDF2.PdfReader(path)
	for pg in pdf.pages:
		text += pg.extract_text()
	return text

def getCaseNumber(text: str):
	try:
		county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
		case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip() 
		return county + "-" + case_num
	except (IndexError, AttributeError):
		return ""

def getName(text: str):
	name = ""
	if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
		name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
	else:
		if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
			name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
	return name

def getDOB(text: str):
	dob = ""
	if bool(re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL)):
		dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
	return dob

def getFeeTotals(text: str):
	try:
		trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
		totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
		if len(totalrow.split("$")[-1])>5:
			totalrow = totalrow.split(" . ")[0]
		tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
		tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","")
		tpaid = totalrow.split("$")[2].strip().replace("$","").replace(",","").replace(" ","")
		thold = totalrow.split("$")[4].strip().replace("$","").replace(",","").replace(" ","")
	except IndexError:
		totalrow = ""
		tbal = ""
		tdue = ""
		tpaid = ""
		thold = ""
	return [totalrow,tdue,tpaid,tdue,thold]

def getCaseInfo(text: str):
	case_num = ""
	name = ""
	alias = ""
	race = ""
	sex = ""
	address = ""
	dob = ""
	phone = ""

	try:
		county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
		case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip() 
	except (IndexError, AttributeError):
		pass
 
	if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE)) == True:
		name = re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
	else:
		if bool(re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE)) == True:
			name = re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
	try:
		alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":","").replace("Alias 1","").strip()
	except (IndexError, AttributeError):
		pass
	else:
		pass
	try:
		dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
		phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
		phone = re.sub(r'[^0-9]','',phone)
		if len(phone) < 7:
			phone = ""
		if len(phone) > 10 and phone[-3:] == "000":
			phone = phone[0:9]
	except (IndexError, AttributeError):
		dob = ""
		phone = ""
	try:
		racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
		race = racesex.group(1).strip()
		sex = racesex.group(2).strip()
	except (IndexError, AttributeError):
		pass
	try:
		street_addr = re.search(r'(Address 1\:)(.+)(?:Phone)*?', str(text), re.MULTILINE).group(2).strip()
	except (IndexError, AttributeError):
		street_addr = ""
	try:
		zip_code = re.search(r'(Zip\: )(.+)', str(text), re.MULTILINE).group(2).strip() 
	except (IndexError, AttributeError):
		zip_code = ""
	try:
		city = re.search(r'(City\: )(.*)(State\: )(.*)', str(text), re.MULTILINE).group(2).strip()
	except (IndexError, AttributeError):
		city = ""
	try:
		state = re.search(r'(?:City\: ).*(?:State\: ).*', str(text), re.MULTILINE).group(4).strip()
	except (IndexError, AttributeError):
		state = ""
	
	address = street_addr + " " + city + ", " + state + " " + zip_code
	if len(address) < 5:
		address = ""
	address = address.replace("00000-0000","").replace("%","").strip()
	address = re.sub(r'([A-Z]{1}[a-z]+)','',address)
	case = [case_num, name, alias, dob, race, sex, address, phone]
	return case

def getFeeSheet(text: str, cnum: str):
	actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
	if len(actives) == 0:
		return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
	else:
		rind = range(0, len(actives)+1)
		try:
			trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
			totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
			if len(totalrow.split("$")[-1])>5:
				totalrow = totalrow.split(" . ")[0]
			tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
			tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","")
			tpaid = totalrow.split("$")[2].strip().replace("$","").replace(",","").replace(" ","")
			thold = totalrow.split("$")[4].strip().replace("$","").replace(",","").replace(" ","")
		except IndexError:
			totalrow = ""
			tbal = ""
			tdue = ""
			tpaid = ""
			thold = ""
		fees = pd.Series(actives,dtype=str)
		fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
		srows = fees.map(lambda x: x.strip().split(" "))
		drows = fees_noalpha.map(lambda x: x.replace(",","").split("$"))
		coderows = srows.map(lambda x: str(x[5]).strip() if len(x)>5 else "")
		payorrows = srows.map(lambda x: str(x[6]).strip() if len(x)>6 else "")
		amtduerows = drows.map(lambda x: str(x[1]).strip() if len(x)>1 else "")
		amtpaidrows = drows.map(lambda x: str(x[2]).strip() if len(x)>2 else "")
		balancerows = drows.map(lambda x: str(x[-1]).strip() if len(x)>5 else "")
		amtholdrows = drows.map(lambda x: str(x[3]).strip() if len(x)>5 else "")
		amtholdrows = amtholdrows.map(lambda x: x.split(" ")[0].strip() if " " in x else x)
		istotalrow = fees.map(lambda x: False if bool(re.search(r'(ACTIVE)',x)) else True)
		try:
			adminfeerows = pd.Series(actives).str.strip().str.split(" ")[1].str.strip()
		except (IndexError, AttributeError):
			adminfeerows = pd.Series()
		

		feesheet = pd.DataFrame({
			'CaseNumber': cnum,
			'Total': '',
			'FeeStatus': 'ACTIVE',
			'AdminFee': adminfeerows.tolist(),
			'Code': coderows.tolist(),
			'Payor': payorrows.tolist(),
			'AmtDue': amtduerows.tolist(),
			'AmtPaid': amtpaidrows.tolist(),
			'Balance': balancerows.tolist(),
			'AmtHold': amtholdrows.tolist()
			})

		totalrdf = {
			'CaseNumber': cnum,
			'Total': 'TOTAL',
			'FeeStatus': '',
			'AdminFee': '',
			'Code': '',
			'Payor': '',
			'AmtDue': tdue,
			'AmtPaid': tpaid,
			'Balance': tbal,
			'AmtHold': thold
		}


		feesheet = feesheet.append(totalrdf, ignore_index=True)
		feesheet['Code'] = feesheet['Code'].astype("category")
		feesheet['Payor'] = feesheet['Payor'].astype("category")

		try:
			d999 = feesheet[feesheet['Code']=='D999']['Balance']
		except (TypeError, IndexError):
			d999 = ""

		owe_codes = " ".join(feesheet['Code'][feesheet.Balance.str.len() > 0])
		codes = " ".join(feesheet['Code'])
		allrows = actives
		allrows.append(totalrow)
		allrowstr = "\n".join(allrows)
		
		cols = ['CaseNumber', 'Total', 'FeeStatus', 'AdminFee', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']
		feesheet = feesheet[cols]
		
		return [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]

def getCharges(text: str, cnum: str):

	rc = re.findall(r'(\d{3}\s{1}.{1,100}?.{3}-.{3}-.{3}.{10,75})', text, re.MULTILINE)
	unclean = pd.DataFrame({'Raw':rc})
	unclean['FailTimeTest'] = unclean['Raw'].map(lambda x: bool(re.search(r'([0-9]{1}\:[0-9]{2})', x)))
	unclean['FailNumTest'] = unclean['Raw'].map(lambda x: False if bool(re.search(r'([0-9]{3}\s{1}.{4}\s{1})',x)) else True)
	unclean['Fail'] = unclean.index.map(lambda x: unclean['FailTimeTest'][x] == True or unclean['FailNumTest'][x]== True)
	passed = pd.Series(unclean[unclean['Fail']==False]['Raw'].dropna().explode().tolist())
	passed = passed.explode()
	passed = passed.dropna()
	passed = pd.Series(passed.tolist())
	passed = passed.map(lambda x: re.sub(r'(\s+[0-1]{1}$)', '',x))
	passed = passed.map(lambda x: re.sub(r'([©|\w]{1}[a-z]+)', ' ',x))
	passed = passed.explode()
	c = passed.dropna().tolist()

	# print(c)
	cind = range(0, len(c))
	charges = pd.DataFrame({ 'Charges': c,'parentheses':'','decimals':''},index=cind)
	charges['CaseNumber'] = charges.index.map(lambda x: cnum)
	# find table fields
	split_charges = charges['Charges'].map(lambda x: x.split(" "))
	charges['Num'] = split_charges.map(lambda x: x[0].strip())
	charges['Code'] = split_charges.map(lambda x: x[1].strip()[0:4])
	charges['Felony'] = charges['Charges'].map(lambda x: bool(re.search(r'FELONY',x)))
	charges['Conviction'] = charges['Charges'].map(lambda x: bool(re.search(r'GUILTY|CONVICTED',x)))
	charges['VRRexception'] = charges['Charges'].map(lambda x: bool(re.search(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)',x)))
	charges['CERVCode'] = charges['Code'].map(lambda x: bool(re.search(r'(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)', x)))
	charges['PardonCode'] = charges['Code'].map(lambda x: bool(re.search(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)', x)))
	charges['PermanentCode'] = charges['Code'].map(lambda x: bool(re.search(r'(CM\d\d|CMUR)', x)))
	charges['CERV'] = charges.index.map(lambda x: charges['CERVCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
	charges['Pardon'] = charges.index.map(lambda x: charges['PardonCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
	charges['Permanent'] = charges.index.map(lambda x: charges['PermanentCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
	charges['Disposition'] = charges['Charges'].map(lambda x: bool(re.search(r'\d{2}/\d{2}/\d{4}', x)))
	charges['CourtActionDate'] = charges['Charges'].map(lambda x: re.search(r'(\d{2}/\d{2}/\d{4})', x).group() if bool(re.search(r'(\d{2}/\d{2}/\d{4})', x)) else "")
	charges['CourtAction'] = charges['Charges'].map(lambda x: re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x).group() if bool(re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x)) else "")
	# print(charges)
	try:
		charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([^a-z]{1,2}?.{1}-[^\s]{3}-[^\s]{3})', x).group())
	except (AttributeError, IndexError):
		pass    
		try:
			charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([0-9]{1,2}.{1}-.{3}-.{3})',x).group()) # TEST
		except (AttributeError, IndexError):
			charges['Cite'] = ""
	charges['Cite'] = charges['Cite'].astype(str)
	try:
		charges['decimals'] = charges['Charges'].map(lambda x: re.search(r'(\.[0-9])', x).group())
		charges['Cite'] = charges['Cite'] + charges['decimals']
	except (AttributeError, IndexError):
		charges['Cite'] = charges['Cite']
	try:
		charges['parentheses'] = charges['Charges'].map(lambda x: re.search(r'(\([A-Z]\))', x).group())
		charges['Cite'] = charges['Cite'] + charges['parentheses']
		charges['Cite'] = charges['Cite'].map(lambda x: x[1:-1] if bool(x[0]=="R" or x[0]=="Y" or x[0]=="C") else x)
	except (AttributeError, IndexError):
		pass

	charges['TypeDescription'] = charges['Charges'].map(lambda x: re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x).group() if bool(re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x)) else "")
	charges['Category'] = charges['Charges'].map(lambda x: re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x).group() if bool(re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x)) else "")
	charges['Charges'] = charges['Charges'].map(lambda x: x.replace("SentencesSentence","").replace("Sentence","").strip())
	charges.drop(columns=['PardonCode','PermanentCode','CERVCode','VRRexception','parentheses','decimals'], inplace=True)
	
	###
	###
	ch_Series = charges['Charges']
	noNumCode = ch_Series.str.slice(8)
	noNumCode = noNumCode.str.strip()
	noDatesEither = noNumCode.str.replace("\d{2}/\d{2}/\d{4}",'',regex=True)
	noWeirdColons = noDatesEither.str.replace("\:.+","",regex=True)

	descSplit = noWeirdColons.str.split(".{3}-.{3}-.{3}",regex=True)

	descOne = descSplit.map(lambda x: x[0])
	descTwo = descSplit.map(lambda x: x[1])

	descs = pd.DataFrame({
		 'One': descOne,
		 'Two': descTwo
		 })


	descs['TestOne'] = descs['One'].str.replace("TRAFFIC","")
	descs['TestOne'] = descs['TestOne'].str.replace("FELONY","")
	descs['TestOne'] = descs['TestOne'].str.replace("PROPERTY","")
	descs['TestOne'] = descs['TestOne'].str.replace("MISDEMEANOR","")
	descs['TestOne'] = descs['TestOne'].str.replace("PERSONAL","")
	descs['TestOne'] = descs['TestOne'].str.replace("FELONY","")
	descs['TestOne'] = descs['TestOne'].str.replace("DRUG","")
	descs['TestOne'] = descs['TestOne'].str.replace("GUILTY PLEA","")
	descs['TestOne'] = descs['TestOne'].str.replace("DISMISSED","")
	descs['TestOne'] = descs['TestOne'].str.replace("NOL PROSS","")
	descs['TestOne'] = descs['TestOne'].str.replace("CONVICTED","")
	descs['TestOne'] = descs['TestOne'].str.replace("WAIVED TO GJ","")
	descs['TestOne'] = descs['TestOne'].str.strip()

	descs['TestTwo'] = descs['Two'].str.replace("TRAFFIC","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("FELONY","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("PROPERTY","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("MISDEMEANOR","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("PERSONAL","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("FELONY","")
	descs['TestTwo'] = descs['TestTwo'].str.replace("DRUG","")
	descs['TestTwo'] = descs['TestTwo'].str.strip()

	descs['Winner'] = descs['TestOne'].str.len() - descs['TestTwo'].str.len()

	descs['DoneWon'] = descs['One']
	descs['DoneWon'][descs['Winner']<0] = descs['Two'][descs['Winner']<0]

	descs['DoneWon'] = descs['DoneWon'].str.strip()
	
	charges['Description'] = descs['DoneWon']
		
	###
	###

	charges['Category'] = charges['Category'].astype("category")
	charges['TypeDescription'] = charges['TypeDescription'].astype("category")
	charges['Code'] = charges['Code'].astype("category")
	charges['CourtAction'] = charges['CourtAction'].astype("category")

	# counts
	conviction_ct = charges[charges.Conviction == True].shape[0]
	charge_ct = charges.shape[0]
	cerv_ct = charges[charges.CERV == True].shape[0]
	pardon_ct = charges[charges.Pardon == True].shape[0]
	perm_ct = charges[charges.Permanent == True].shape[0]
	conv_cerv_ct = charges[charges.CERV == True][charges.Conviction == True].shape[0]
	conv_pardon_ct = charges[charges.Pardon == True][charges.Conviction == True].shape[0]
	conv_perm_ct = charges[charges.Permanent == True][charges.Conviction == True].shape[0]

	# summary strings
	convictions = "; ".join(charges[charges.Conviction == True]['Charges'].tolist())
	conv_codes = " ".join(charges[charges.Conviction == True]['Code'].tolist())
	charge_codes = " ".join(charges[charges.Disposition == True]['Code'].tolist())
	dcharges = "; ".join(charges[charges.Disposition == True]['Charges'].tolist())
	fcharges = "; ".join(charges[charges.Disposition == False]['Charges'].tolist())
	cerv_convictions = "; ".join(charges[charges.CERV == True][charges.Conviction == True]['Charges'].tolist())
	pardon_convictions = "; ".join(charges[charges.Pardon == True][charges.Conviction == True]['Charges'].tolist())
	perm_convictions = "; ".join(charges[charges.Permanent == True][charges.Conviction == True]['Charges'].tolist())

	allcharge = "; ".join(charges['Charges'])
	if charges.shape[0] == 0:
		charges = np.nan

	return [convictions, dcharges, fcharges, cerv_convictions, pardon_convictions, perm_convictions, conviction_ct, charge_ct, cerv_ct, pardon_ct, perm_ct, conv_cerv_ct, conv_pardon_ct, conv_perm_ct, charge_codes, conv_codes, allcharge, charges]

# LOG METHODS

def log_complete(conf, start_time):
	path_in = conf['in_path']
	path_out = conf['out_path']
	path_out = "Wrote to " + conf['out_path'] if conf['out_path'] != "" else "No export path provided - did not export!"
	case_max = conf['case_max']
	bsize = conf['batchsize']
	completion_time = time.time()
	elapsed = completion_time - start_time
	cases_per_sec = case_max/elapsed
	print(f'''
		  ___    __                          __         
		 /   |  / /___  _________  _________/ /__  _____
		/ /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	   / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	  /_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/     



	ALACORDER beta 7.4.9.9.7
	by Sam Robson   

	Searched {path_in} 
	{path_out} 

	TASK SUCCEEDED ({case_max}/{case_max} cases)
	Completed export in {elapsed:.2f} seconds ({cases_per_sec:.2f}/sec)

''') 

