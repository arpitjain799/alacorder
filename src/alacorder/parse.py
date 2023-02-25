
# parse 74
# Sam Robson

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
import warnings
import click
import inspect
from alacorder import get 
from alacorder import write 
from alacorder import config 
from alacorder import logs
import PyPDF2
try:
	import xlsxwriter
except ImportError:
	pass

pd.set_option("mode.chained_assignment",None)
pd.set_option("display.notebook_repr_html",True)
pd.set_option("display.width",None)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)

def table(conf):
	"""
	Route config to parse...() function corresponding to table attr 
	"""
	a = []
	if not conf.DEBUG:
		sys.tracebacklimit = 0
		warnings.filterwarnings('ignore')
	if conf.MAKE == "multiexport":
		a = cases(conf)
	if conf['TABLE'] == "cases":
		a = caseinfo(conf)
	if conf['TABLE'] == "fees":
		a = fees(conf)
	if conf['TABLE'] == "charges":
		a = charges(conf)
	if conf['TABLE'] == "disposition":
		a = charges(conf)
	if conf['TABLE'] == "filing":
		a = charges(conf)
	return a

def fees(conf):
	"""
	Return fee sheets with case number as DataFrame from batch
	fees = pd.DataFrame({'CaseNumber': '', 
		'Code': '', 'Payor': '', 'AmtDue': '', 
		'AmtPaid': '', 'Balance': '', 'AmtHold': ''})
	"""
	if not conf.DEBUG:
		sys.tracebacklimit = 0
		warnings.filterwarnings('ignore')
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	count = conf['COUNT']
	queue = conf['QUEUE']
	print_log = conf['LOG']
	warn = conf['WARN']
	no_write = conf['NO_WRITE']
	dedupe = conf['DEDUPE']
	from_archive = True if conf['IS_FULL_TEXT'] else False
	start_time = time.time()
	if warn == False:
		warnings.filterwarnings("ignore")
	fees = pd.DataFrame()
	# fees = pd.DataFrame({'CaseNumber': '', 
	  #  'Code': '', 'Payor': '', 'AmtDue': '', 
	   # 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
	if not conf['NO_BATCH']:
		batches = config.batcher(conf)
	else:
		batches = np.array_split(queue, 1)
	
	batchcount = len(batches)
	with click.progressbar(batches) as bar:
		for i, c in enumerate(bar):
			exptime = time.time()
			b = pd.DataFrame()

			if from_archive == True:
				b['AllPagesText'] = c
			else:
				b['AllPagesText'] = c.map(lambda x: get.PDFText(x))

			b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
			b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
			#try:
			b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(str(b.loc[x].AllPagesText)))
			feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
			#except (AttributeError,IndexError):
			 #   pass

			feesheet = feesheet.dropna() # drop empty 
			fees =fees.dropna()
			feesheet = feesheet.tolist() # convert to list -> [df, df, df]
			#try:
			feesheet = pd.concat(feesheet,axis=0,ignore_index=True) # add all dfs in batch -> df
			#except ValueError:
			 #   pass
			fees = fees.append(feesheet, ignore_index=True) 
			fees.fillna('',inplace=True)
			fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
			fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
			fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
			fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))
	if not no_write:
		write.now(conf, fees)
	logs.complete(conf)
	return fees
def charges(conf):
	"""
	Return charges with case number as DataFrame from batch
	charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''}) 
	"""
	if not conf.DEBUG:
		sys.tracebacklimit = 0
		warnings.filterwarnings('ignore')
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	count = conf['COUNT']
	queue = conf['QUEUE']
	print_log = conf['LOG']
	warn = conf['WARN']
	no_write = conf['NO_WRITE']
	dedupe = conf['DEDUPE']
	table = conf['TABLE']
	dedupe = conf['DEDUPE']
	from_archive = True if conf['IS_FULL_TEXT'] else False

	if warn == False:
		warnings.filterwarnings("ignore")

	if not conf['NO_BATCH']:
		batches = config.batcher(conf)
	else:
		batches = np.array_split(queue, 1)

	start_time = time.time()
	charges = pd.DataFrame()
	with click.progressbar(batches) as bar:
		for i, c in enumerate(bar):
			exptime = time.time()
			b = pd.DataFrame()

			if from_archive == True:
				b['AllPagesText'] = c
			else:
				b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))

			## b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
			b['CaseNumber'] = b['AllPagesText'].map(lambda x: get.CaseNumber(x))
			b['ChargesOutputs'] = b.index.map(lambda x: get.Charges(str(b.loc[x].AllPagesText)))

			
			chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
			chargetabs = chargetabs.dropna()
			chargetabs = chargetabs.tolist()
			charges = charges.append(chargetabs)
			charges.fillna('',inplace=True)

		if table == "filing":
			is_disp = charges['Disposition']
			is_filing = is_disp.map(lambda x: False if x == True else True)
			charges = charges[is_filing]
			charges.drop(columns=['CourtAction','CourtActionDate'],inplace=True)

		if table == "disposition":
			is_disp = charges.Disposition.map(lambda x: True if x == True else False)
			charges = charges[is_disp]
		if not no_write:
			write.now(conf, charges)

	logs.complete(conf)
	return charges
def cases(conf):
	"""
	Return [cases, fees, charges] tables as List of DataFrames from batch
	See API docs for table specific outputs
	"""
	if not conf.DEBUG:
		sys.tracebacklimit = 0
		warnings.filterwarnings('ignore')
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	count = conf['COUNT']
	queue = conf['QUEUE']
	print_log = conf['LOG']
	warn = conf['WARN']
	no_write = conf['NO_WRITE']
	dedupe = conf['DEDUPE']
	table = conf['TABLE']
	overwrite = conf['OVERWRITE']
	path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
	archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
	from_archive = True if conf['IS_FULL_TEXT'] else False
	start_time = time.time()
	arc_ext = conf['OUTPUT_EXT']
	cases = pd.DataFrame()
	fees = pd.DataFrame()
	charges = pd.DataFrame()
	if not conf['NO_BATCH']:
		batches = config.batcher(conf)
	else:
		batches = np.array_split(queue, 1)
	if warn == False:
		warnings.filterwarnings("ignore")
	temp_no_write_arc = False
	temp_no_write_tab = False
	with click.progressbar(batches) as bar:
		for i, c in enumerate(bar):
			b = pd.DataFrame()
			if from_archive == True:
				b['AllPagesText'] = c
			else:
				b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))
			b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
			b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
			b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
			b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
			b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
			b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
			b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
			b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
			b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
			b['ChargesOutputs'] = b.index.map(lambda x: get.Charges(str(b.loc[x].AllPagesText)))
			b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
			b['Dispositioncharges'] = b['ChargesOutputs'].map(lambda x: x[1])
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
			b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(str(b.loc[x].AllPagesText)))
			b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
			b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
			b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
			# b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
			b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
			b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
			b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])
			logs.debug(conf, b['FeeSheet'])

			feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
			feesheet = feesheet.dropna() 
			feesheet = feesheet.tolist() # -> [df, df, df]
			
			#try:
			feesheet = pd.concat(feesheet,axis=0,ignore_index=True) #  -> batch df
			#except:
			 #   pass
			#try:
			fees = fees.append(feesheet)
			#except:
			 #   pass
			logs.debug(conf, fees)
			chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
			chargetabs = chargetabs.dropna()
			# charges = charges.dropna()
			chargetabs = chargetabs.tolist()
			
			#try:
			chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
			#except:
			 #   pass
			#try:
			charges = charges.append(chargetabs,ignore_index=True)
			#except:
			 #   pass
			
			feesheet['AmtDue'] = feesheet['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
			feesheet['AmtPaid'] = feesheet['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
			feesheet['Balance'] = feesheet['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
			feesheet['AmtHold'] = feesheet['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))

			b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
			b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['PaymentToRestore'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))

			if bool(archive_out) and len(arc_ext) > 2 and i > 0 and not no_write:
				if os.path.getsize(archive_out) > 1000:
					temp_no_write_arc = True
			if bool(path_out) and i > 0 and not no_write:
				if os.path.getsize(path_out) > 1000:
					temp_no_write_tab = True
			if i == len(batches) - 1:
				temp_no_write_arc = False
				temp_no_write_tab = False

			if (i % 5 == 0 or i == len(batches) - 1) and not no_write and temp_no_write_arc == False:
				if bool(archive_out) and len(arc_ext) > 2:
					timestamp = start_time
					q = pd.Series(queue) if conf.IS_FULL_TEXT == False else pd.NaT
					ar = pd.DataFrame({
						'Path': q,
						'AllPagesText': b['AllPagesText'],
						'Timestamp': timestamp
						},index=range(0,conf.COUNT))
					try:
						arch = pd.concat([arch, ar],ignore_index=True,axis=0)
					except:
						pass
					arch.fillna('',inplace=True)
					arch.dropna(inplace=True)
					arch.to_pickle(archive_out,compression="xz")

			b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','ChargesTable','FeeSheet'],inplace=True)

			if dedupe == True:
				outputs.drop_duplicates(keep='first',inplace=True)
			
			b.fillna('',inplace=True)
			# newcases = [cases, b]
			cases = cases.append(b, ignore_index=True)

			if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
				if out_ext == ".xls":
					try:
						with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
							cases.to_excel(writer, sheet_name="cases")
							fees.to_excel(writer, sheet_name="fees")
							charges.to_excel(writer, sheet_name="charges")
					except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
						click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
						with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
							cases.to_excel(writer, sheet_name="cases")
							fees.to_excel(writer, sheet_name="fees")
							charges.to_excel(writer, sheet_name="charges")
				elif out_ext == ".xlsx":
					try:
						with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
							cases.to_excel(writer, sheet_name="cases")
							fees.to_excel(writer, sheet_name="fees")
							charges.to_excel(writer, sheet_name="charges")
					except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
						try:
							if warn:
								click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
							with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
								cases.to_excel(writer, sheet_name="cases")
								fees.to_excel(writer, sheet_name="fees")
								charges.to_excel(writer, sheet_name="charges")
						except (ImportError, FileNotFoundError, IndexError, ValueError, ModuleNotFoundError):
							try:
								cases.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
								fees.to_json(os.path.splitext(path_out)[0] + "-fees.json.zip",orient='table')
								charges.to_json(os.path.splitext(path_out)[0] + "-charges.json.zip",orient='table')
								logs.echo(conf,"Fallback export to " + os.path.splitext(path_out)[0] + "-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
							except (ImportError, FileNotFoundError, IndexError, ValueError):
								click.echo("Failed to export!")
							
				elif out_ext == ".json":
					cases.to_json(path_out,orient='table')
				elif out_ext == ".csv":
					cases.to_csv(path_out,escapechar='\\')
				elif out_ext == ".md":
					cases.to_markdown(path_out)
				elif out_ext == ".txt":
					cases.to_string(path_out)
				elif out_ext == ".dta":
					cases.to_stata(path_out)
				elif out_ext == ".parquet":
					cases.to_parquet(path_out)
				else:
					pd.Series([cases, fees, charges]).to_string(path_out)
				try:
					if dedupe == True and outputs.shape[0] < queue.shape[0]:
						click.echo(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
				except:
					pass

		logs.complete(conf)
		return [cases, fees, charges]

def caseinfo(conf):
	"""
	Return [cases, fees, charges] tables as List of DataFrames from batch
	See API docs for table specific outputs
	"""
	if not conf.DEBUG:
		sys.tracebacklimit = 0
		warnings.filterwarnings('ignore')
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	count = conf['COUNT']
	queue = conf['QUEUE']
	print_log = conf['LOG']
	warn = conf['WARN']
	no_write = conf['NO_WRITE']
	dedupe = conf['DEDUPE']
	table = conf['TABLE']
	overwrite = conf['OVERWRITE']
	path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
	archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
	from_archive = True if conf['IS_FULL_TEXT'] else False
	start_time = time.time()
	arc_ext = conf['OUTPUT_EXT']
	cases = pd.DataFrame()
	if not conf['NO_BATCH']:
		batches = config.batcher(conf)
	else:
		batches = np.array_split(queue, 1)
	if warn == False:
		warnings.filterwarnings("ignore")
	temp_no_write_arc = False
	temp_no_write_tab = False
	with click.progressbar(batches) as bar:
		for i, c in enumerate(bar):
			b = pd.DataFrame()
			if from_archive == True:
				b['AllPagesText'] = c
			else:
				b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))
			b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
			b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
			b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
			b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
			b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
			b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
			b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
			b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
			b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
			b['ChargesOutputs'] = b.index.map(lambda x: get.Charges(str(b.loc[x].AllPagesText)))
			b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
			b['Dispositioncharges'] = b['ChargesOutputs'].map(lambda x: x[1])
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
			b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(str(b.loc[x].AllPagesText)))
			b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
			b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
			b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
			# b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
			b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
			b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
			b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])
			

			b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
			b['PaymentToRestore'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))

			if bool(archive_out) and len(arc_ext) > 2 and i > 0 and not no_write:
				if os.path.getsize(archive_out) > 1000:
					temp_no_write_arc = True
			if bool(path_out) and i > 0 and not no_write:
				if os.path.getsize(path_out) > 1000:
					temp_no_write_tab = True
			if i == len(batches) - 1:
				temp_no_write_arc = False
				temp_no_write_tab = False

			if (i % 5 == 0 or i == len(batches) - 1) and not no_write and temp_no_write_arc == False:
				if bool(archive_out) and len(arc_ext) > 2:
					timestamp = start_time
					q = pd.Series(queue) if conf.IS_FULL_TEXT == False else pd.NaT
					ar = pd.DataFrame({
						'Path': q,
						'AllPagesText': b['AllPagesText'],
						'Timestamp': timestamp
						},index=range(0,conf.COUNT))
					try:
						arch = pd.concat([arch, ar],ignore_index=True,axis=0)
					except:
						pass
					arch.fillna('',inplace=True)
					arch.dropna(inplace=True)
					arch.to_pickle(archive_out,compression="xz")

			b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','FeeSheet'],inplace=True)

			if dedupe == True:
				outputs.drop_duplicates(keep='first',inplace=True)
			
			b.fillna('',inplace=True)
			# newcases = [cases, b]
			cases = cases.append(b, ignore_index=True)

			if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
				if out_ext == ".xls":
					try:
						with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
							cases.to_excel(writer, sheet_name="cases")
					except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
						click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
						with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
							cases.to_excel(writer, sheet_name="cases")
				elif out_ext == ".xlsx":
					try:
						with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
							cases.to_excel(writer, sheet_name="cases")
					except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
						try:
							if warn:
								click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
							with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
								cases.to_excel(writer, sheet_name="cases")
						except (ImportError, FileNotFoundError, IndexError, ValueError, ModuleNotFoundError):
							try:
								cases.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
								logs.echo(conf,"Fallback export to " + os.path.splitext(path_out)[0] + "-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
							except (ImportError, FileNotFoundError, IndexError, ValueError):
								click.echo("Failed to export!")
							
				elif out_ext == ".json":
					cases.to_json(path_out,orient='table')
				elif out_ext == ".csv":
					cases.to_csv(path_out,escapechar='\\')
				elif out_ext == ".md":
					cases.to_markdown(path_out)
				elif out_ext == ".txt":
					cases.to_string(path_out)
				elif out_ext == ".dta":
					cases.to_stata(path_out)
				elif out_ext == ".parquet":
					cases.to_parquet(path_out)
				else:
					cases.to_string(path_out)
				try:
					if dedupe == True and outputs.shape[0] < queue.shape[0]:
						click.echo(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
				except:
					pass

		logs.complete(conf)
		return cases
