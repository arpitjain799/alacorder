# conf 74
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
import alacorder as alac
from alacorder import __main__
from alacorder import get
from alacorder import parse
from alacorder import write
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass

def log_config(conf):
	e = f"""Reading cases from {conf.input_path}. Queued {conf['count']} cases of {conf.content_length} for{" table" if conf.table_out else " archive"} export to {conf.table_out if conf.table_out else conf.archive_out}. {"OVERWRITE MODE is enabled. Alacorder will overwrite existing files at output path!" if conf.overwrite else 'Overwrite mode is not enabled.'} {"APPEND MODE is enabled. Alacorder will attempt to append outputs to existing file at path. " if conf.overwrite == False and (conf.appendTable == True or conf.appendArchive == True) else ''}{"NO-WRITE MODE is enabled. Alacorder will NOT export outputs. " if conf.no_write else ''}{"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output." if conf.dedupe else ''} {"LAUNCH MODE is enabled. Upon completion, Alacorder will attempt to launch exported file in default viewing application." if conf.launch else ''} {"LOG MODE is enabled. Upon completion, Alacorder will print outputs to console." if conf.tablog else ''}
	"""
	return click.style(e, italic=True)
def config(input_path, table_path=None, archive_path=None, text_path=None, table="", print_log=True, warn=False, max_cases=0, overwrite=False, GUI_mode=False, drop_cols=True, dedupe=False, launch=False, no_write=False, mk_archive=False, tablog=False, drop=""): 
	"""
	Configures parse functions to run getters on a batch of cases. Returns config object accepted as argument by alac.parse...() functions. 
	"""
	tab_ext = ""
	arc_ext = ""
	in_ext = ""
	input_type = ""
	appendArchive = False
	appendTable = False
	stringInput = True
	pathMode = False
	old_archive = None
	old_table = None
	launch = True if GUI_mode == True else launch
	if warn == False:
		warnings.filterwarnings("ignore")
	if table_path == None and archive_path == None:
		no_write = True

 # Correct archive path provided as table path
	if table_path != None:
		if os.path.splitext(table_path)[1] == ".xz" and archive_path == None:
			archive_path = table_path
			table_path = None
			if print_log and warn:
				print(f"WARNING: alac.config() received archive file format for parameter table_path: Setting archive_path to {archive_path}. Reconfigure to export table.")
 # EXISTING FILE INPUT
	if os.path.isfile(input_path): 
		in_head = os.path.split(input_path)[0]
		in_tail = os.path.split(input_path)[1]
		in_ext = os.path.splitext(input_path)[1]
		if in_ext == ".xz": # if archive 
			try:
				queue = pd.read_pickle(input_path,compression="xz")['AllPagesText']
				pathMode = False
				input_type = "archive"
			except KeyError:
				raise Exception("Could not identify Series \'AllPagesText\' in input archive!")
		elif in_ext == ".pdf": # if pdf get text
			queue = pd.Series([get.PDFText(input_path)])
			pathMode = False
			input_type = "pdf"
		elif in_ext == ".txt": # if txt get text
			pathMode = False
			input_type = "text"
			with open(input_path,'r') as textfile:
				queue = pd.Series([textfile.read()])
		else:
			raise Exception("Invalid input!")
 # DIRECTORY INPUT
	elif os.path.isdir(input_path):
		queue = pd.Series(glob.glob(input_path + '**/*.pdf', recursive=True))
		input_type = "directory"
		pathMode = True
		if queue.shape[0] == 0:
			raise Exception("No PDFs found in input directory!")
 # DATAFRAME INPUT
	elif type(input_path) == pd.DataFrame:
		stringInput = False
		pathMode = False
		try:
			queue = input_path['AllPagesText']
		except KeyError:
			raise Exception("Could not identify Series \'AllPagesText\' in input path!")
 # SERIES INPUT
	elif type(input_path) == pd.Series:
		stringInput = False
		try:
			if os.path.exists(input_path.tolist()[0]):
				pathMode = True
				queue = input_path
			elif "ALABAMA SJIS CASE DETAIL" in input_path.tolist()[0]:
				pathMode = False
				queue = input_path
			else:
				raise Exception("Could not parse input object!")
		except (AttributeError, KeyError, IndexError):
			raise Exception("Could not parse input object!")
	try:
		content_length = queue.shape[0]
	except UnboundLocalError:
		content_length = 1
		queue = []
	if content_length > max_cases and max_cases > 0: # cap input at max
		queue = queue.sample(frac=1) # shuffle rows
		queue = queue[0:max_cases] # get max_cases 
	if max_cases > content_length or max_cases == 0: # cap max at input len
		max_cases = content_length

	if archive_path != None:
		arc_head = os.path.split(archive_path)[0]
		if os.path.exists(arc_head) == False:
			raise Exception("Invalid input!")
		arc_tail = os.path.split(archive_path)[1]
		arc_ext = os.path.splitext(arc_tail)[1]
		if arc_ext == ".xz": # if archive 
			try: # if exists at path, append
				old_archive = pd.read_pickle(archive_path,compression="xz")
				if print_log:
					try:
						click.secho(old_archive.columns, italic=True)
					except:
						pass
					appendArchive = True
			except: 
				pass
 
	if table_path != None:
		tab_head = os.path.split(table_path)[0]
		if os.path.exists(tab_head) is False:
			raise Exception(f"Invalid table output path!")
		tab_tail = os.path.split(table_path)[1]
		tab_ext = os.path.splitext(tab_tail)[1]
		if os.path.isfile(table_path):
			appendTable = True
			if tab_ext == ".xls" or tab_ext == ".xlsx":
				try:
					old_cases = pd.read_excel(table_path, sheet_name="cases")
					old_fees = pd.read_excel(table_path, sheet_name="fees")
					old_charges = pd.read_excel(table_path, sheet_name="charges")
					old_table = [old_cases, old_fees, old_charges]
					if print_log:
						for x in old_table:
							print(f"Existing table at output with columns: {x.columns}")
				except:
					appendTable = False
					pass
			elif tab_ext == ".json":
				old_table = pd.read_json(table_path)
			elif tab_ext == ".csv":
				old_table = pd.read_csv(table_path)
			elif tab_ext == ".dta":
				old_table = pd.read_stata(table_path)
			elif overwrite:
				appendTable = False
				if print_log or warn:
					click.secho("WARNING: Force overwrite mode is enabled. Existing file at table output path will be overwritten. Continue anyway?",bold=True,fg='yellow')
			else:
				raise Exception("ERROR: Existing file at output path! Provide valid table export path or use \'overwrite\' flag to replace existing file with task outputs.")
		elif os.path.exists(tab_head) == False or (tab_ext == ".xz" or tab_ext == ".pkl" or tab_ext == ".json" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".dta") == False:
			raise Exception("Table output invalid!")
		elif table == "" and tab_ext != ".xls" and tab_ext != ".xlsx" and tab_ext != ".pkl" and tab_ext != ".xz":
			click.secho(f"(DEFAULTING TO CASES TABLE) Must specify table export (cases, fees, charges) on table export to file extension {tab_ext}. Specify table or export to .xls or .xlsx to continue.",bold=True,fg='yellow')
		elif tab_ext == ".xz" or tab_ext == ".json" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".pkl" or tab_ext == ".dta":
			pass
		else:
			raise Exception("Invalid table output file extension! Must write to .xls, .xlsx, .csv, .json, or .dta.")
	conf_no_echo = pd.Series({'input_path': input_path, 'table_out': table_path, 'table_ext': tab_ext, 'table': table, 'archive_out': archive_path, 'archive_ext': arc_ext, 'appendArchive': appendArchive, 'appendTable': appendTable, 'old_archive': old_archive, 'old_table': old_table, 'warn': warn, 'log': print_log, 'overwrite': overwrite, 'queue': queue, 'count': max_cases, 'path_mode': pathMode, 'drop_cols': drop_cols, 'drop': drop, 'tablog': tablog, 'dedupe': dedupe, 'launch': launch, 'no_write': no_write, 'mk_archive': mk_archive, 'content_length': content_length }) 
	lc = log_config(conf_no_echo)
	conf = pd.Series({'input_path': input_path, 'table_out': table_path, 'table_ext': tab_ext, 'table': table, 'archive_out': archive_path, 'archive_ext': arc_ext, 'appendArchive': appendArchive, 'appendTable': appendTable, 'old_archive': old_archive, 'old_table': old_table, 'warn': warn, 'log': print_log, 'overwrite': overwrite, 'queue': queue, 'count': max_cases, 'path_mode': pathMode, 'drop_cols': drop_cols, 'drop': drop, 'tablog': tablog, 'dedupe': dedupe, 'launch': launch, 'echo': lc, 'no_write': no_write, 'mk_archive': mk_archive, 'content_length': content_length }) 
	return conf
def splitext(path: str):
	head = os.path.split(path)[0]
	tail = os.path.split(path)[1]
	ext = os.path.splitext(path)[1] 
	return pd.Series({
		'head': head,
		'tail': tail,
		'ext': ext
	})
def checkPath(path: str, warn=False):
	PathType = ""
	if os.path.isdir(path):
		count = len(glob.glob(path + '**/*.pdf', recursive=True))
		if count == 0:
			PathType = "bad"
			warnings.warn("No PDFs found in input path!")
		if count > 0:
			PathType = "pdf_directory"
			if warn:
				click.echo(f"\nAlacorder found {count} PDFs in input directory.")
			return PathType
	else:
		head = os.path.split(path)[0]
		tail = os.path.split(path)[1]
		ext = os.path.splitext(path)[1]

		if not os.path.isdir(head):
			PathType = "bad"
			warnings.warn("ERROR: Invalid output path!")
			return PathType

		if os.path.isfile(path):
			if ext == ".txt":
				PathType = "text"
				if warn:
					click.echo(f"WARNING: text file input experimental!")
			if ext == ".pdf":
				PathType = "pdf"
			if ext == ".xz":
				test = pd.read_pickle(path,compression="xz")
				if "AllPagesText" in test.columns:
					PathType = "existing_archive"
					if warn:
						click.echo(f"Found existing archive with {test.shape[0]} cases.")
					return PathType
				else:
					PathType = "overwrite_archive"
					if warn:
						click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
					return PathType
			elif ext == ".xls" or ext == ".xlsx":
				if warn:
					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
				PathType = "overwrite_all_table"
				return PathType
			elif ext == ".csv" or ext == ".json" or ext == ".dta":
				if warn:
					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
				PathType = "overwrite_table"
				return PathType
			else:
				PathType = "bad"
				if warn:
					click.echo("Output file extension not supported!")
				if warn:
					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
				return PathType
		else:
			if ext == ".xls" or ext == ".xlsx":
				PathType = "all_table"
				return PathType
			elif ext == ".xz":
				PathType = "archive"
				return PathType
			elif ext == ".csv" or ext == ".json" or ext == ".dta" or ext == ".txt":
				PathType = "table"
				return PathType
			else:
				PathType = "bad"
				warnings.warn("Output file extension not supported!")
				return PathType
	return PathType
def pickTable():
	pick = "".join(input())
	if pick == "A":
		table = "cases"
	elif pick == "B":
		table = "fees"
	elif pick == "C":
		table = "charges"
	elif pick == "D":
		table = "disposition"
	elif pick == "E":
		table = "filing"
	else:
		print("Warning: invalid selection - defaulting to \'cases\'...")
		table = "cases"
	return table
