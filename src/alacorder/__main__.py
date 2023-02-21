# alacorder beta 73 CLI
from alacorder import alac
from alacorder import conf
import pandas as pd
import numpy as np
import click
import glob
import warnings
import os

table = ""
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

	To export data table from case inputs, enter 
	full output path. Use .xls or .xlsx to export all
	all table, or, if using another format, select
	a table after entering output file path.

Enter path:

'''
both =  '''
>>  EXPORT FULL TEXT ARCHIVE:

	To process case inputs into a full text 
	archive (recommended), enter archive 
	path below with file extension .pkl.xz.

>>  EXPORT DATA TABLE:

	To export data table from case inputs, enter 
	full output path. Use .xls or .xlsx to export all
	all table, or, if using another format, select
	a table after entering output file path.

Enter path:

'''
title = '''
		___    __                          __
	   /   |  / /___  _________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /
	/_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/

	ALACORDER beta 73
	(c) 2023 Sam Robson
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

Enter input path: 

'''

text_p = '''

Enter path to output text file (must be .txt): 

'''

# def log_config(conf):
# 	return f"""Reading cases from {conf.input_path}. Queued {conf['count']} cases of {conf.content_length} for export to {conf.table_out if conf.table_out else conf.archive_out}. {"OVERWRITE MODE is enabled. Alacorder will overwrite existing files at output path!" if conf.overwrite else 'Overwrite mode is not enabled.'} {"APPEND MODE is enabled. Alacorder will attempt to append outputs to existing file at path." if conf.overwrite == False and (conf.appendTable == True or conf.appendArchive == True) else 'Append mode is not enabled.'} {"NO-WRITE MODE is enabled. Alacorder will NOT export outputs." if conf.no_write else 'No-Write mode (--no-write) is not enabled.'} {"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output." if conf.dedupe else 'Remove Duplicates (--dedupe) is not enabled.'} {"LAUNCH MODE is enabled. Upon completion, Alacorder will attempt to launch exported file in default viewing application." if conf.launch else 'Launch mode (--launch) is not enabled.'} {"LOG MODE is enabled. Upon completion, Alacorder will print outputs to console." if conf.tablog else 'Log mode (--log) is not enabled.'}"""
# def config(input_path, table_path=None, archive_path=None, text_path=None, table="", print_log=True, warn=False, max_cases=0, overwrite=True, GUI_mode=False, drop_cols=True, dedupe=False, launch=False, no_write=False, mk_archive=False, tablog=False, drop=""): 
# 	"""
# 	Configures parse functions to run getters on a batch of cases. Returns config object accepted as argument by alac.parse...() functions. 
# 	"""
# 	tab_ext = ""
# 	arc_ext = ""
# 	in_ext = ""
# 	input_type = ""
# 	appendArchive = False
# 	appendTable = False
# 	stringInput = True
# 	pathMode = False
# 	old_archive = None
# 	old_table = None
# 	launch = True if GUI_mode == True else launch
# 	if warn == False:
# 		warnings.filterwarnings("ignore")
# 	if table_path == None and archive_path == None:
# 		no_write = True

#  # Correct archive path provided as table path
# 	if table_path != None:
# 		if os.path.splitext(table_path)[1] == ".xz" and archive_path == None:
# 			archive_path = table_path
# 			table_path = None
# 			if print_log and warn:
# 				print(f"WARNING: alac.config() received archive file format for parameter table_path: Setting archive_path to {archive_path}. Reconfigure to export table.")
#  # EXISTING FILE INPUT
# 	if os.path.isfile(input_path): 
# 		in_head = os.path.split(input_path)[0]
# 		in_tail = os.path.split(input_path)[1]
# 		in_ext = os.path.splitext(input_path)[1]
# 		if in_ext == ".xz": # if archive 
# 			try:
# 				queue = pd.read_pickle(input_path,compression="xz")['AllPagesText']
# 				pathMode = False
# 				input_type = "archive"
# 			except KeyError:
# 				raise Exception("Could not identify Series \'AllPagesText\' in input archive!")
# 		elif in_ext == ".pdf": # if pdf get text
# 			queue = pd.Series([getPDFText(input_path)])
# 			pathMode = False
# 			input_type = "pdf"
# 		elif in_ext == ".txt": # if txt get text
# 			pathMode = False
# 			input_type = "text"
# 			with open(input_path,'r') as textfile:
# 				queue = pd.Series([textfile.read()])
# 		else:
# 			raise Exception("Invalid input!")
#  # DIRECTORY INPUT
# 	elif os.path.isdir(input_path):
# 		queue = pd.Series(glob.glob(input_path + '**/*.pdf', recursive=True))
# 		input_type = "directory"
# 		pathMode = True
# 		if queue.shape[0] == 0:
# 			raise Exception("No PDFs found in input directory!")
#  # DATAFRAME INPUT
# 	elif type(input_path) == pd.DataFrame:
# 		stringInput = False
# 		pathMode = False
# 		try:
# 			queue = input_path['AllPagesText']
# 		except KeyError:
# 			raise Exception("Could not identify Series \'AllPagesText\' in input path!")
#  # SERIES INPUT
# 	elif type(input_path) == pd.Series:
# 		stringInput = False
# 		try:
# 			if os.path.exists(input_path.tolist()[0]):
# 				pathMode = True
# 				queue = input_path
# 			elif "ALABAMA SJIS CASE DETAIL" in input_path.tolist()[0]:
# 				pathMode = False
# 				queue = input_path
# 			else:
# 				raise Exception("Could not parse input object!")
# 		except (AttributeError, KeyError, IndexError):
# 			raise Exception("Could not parse input object!")
# 	try:
# 		content_length = queue.shape[0]
# 	except UnboundLocalError:
# 		content_length = 1
# 		queue = []
# 	if content_length > max_cases and max_cases > 0: # cap input at max
# 		queue = queue.sample(frac=1) # shuffle rows
# 		queue = queue[0:max_cases] # get max_cases 
# 	if max_cases > content_length or max_cases == 0: # cap max at input len
# 		max_cases = content_length

# 	if archive_path != None:
# 		arc_head = os.path.split(archive_path)[0]
# 		if os.path.exists(arc_head) == False:
# 			raise Exception("Invalid input!")
# 		arc_tail = os.path.split(archive_path)[1]
# 		arc_ext = os.path.splitext(arc_tail)[1]
# 		if arc_ext == ".xz": # if archive 
# 			try: # if exists at path, append
# 				old_archive = pd.read_pickle(archive_path,compression="xz")
# 				if print_log:
# 					try:
# 						click.secho(old_archive.columns, italic=True)
# 					except:
# 						pass
# 					appendArchive = True
# 			except: 
# 				pass
 
# 	if table_path != None:
# 		tab_head = os.path.split(table_path)[0]
# 		if os.path.exists(tab_head) is False:
# 			raise Exception(f"Invalid table output path!")
# 		tab_tail = os.path.split(table_path)[1]
# 		tab_ext = os.path.splitext(tab_tail)[1]
# 		if os.path.isfile(table_path):
# 			appendTable = True
# 			if tab_ext == ".xls" or tab_ext == ".xlsx":
# 				try:
# 					old_cases = pd.read_excel(table_path, sheet_name="cases")
# 					old_fees = pd.read_excel(table_path, sheet_name="fees")
# 					old_charges = pd.read_excel(table_path, sheet_name="charges")
# 					old_table = [old_cases, old_fees, old_charges]
# 					if print_log:
# 						for x in old_table:
# 							print(f"Existing table at output with columns: {x.columns}")
# 				except:
# 					appendTable = False
# 					pass
# 			elif tab_ext == ".json":
# 				old_table = pd.read_json(table_path)
# 			elif tab_ext == ".csv":
# 				old_table = pd.read_csv(table_path)
# 			elif tab_ext == ".dta":
# 				old_table = pd.read_stata(table_path)
# 			elif overwrite:
# 				appendTable = False
# 				if print_log or warn:
# 					click.secho("WARNING: Force overwrite mode is enabled. Existing file at table output path will be overwritten. Continue anyway?",bold=True,fg='yellow')
# 			else:
# 				raise Exception("ERROR: Existing file at output path! Provide valid table export path or use \'overwrite\' flag to replace existing file with task outputs.")
# 		elif os.path.exists(tab_head) == False or (tab_ext == ".xz" or tab_ext == ".pkl" or tab_ext == ".json" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".dta") == False:
# 			raise Exception("Table output invalid!")
# 		elif table == "" and tab_ext != ".xls" and tab_ext != ".xlsx" and tab_ext != ".pkl" and tab_ext != ".xz":
# 			click.secho(f"(DEFAULTING TO CASES TABLE) Must specify table export (cases, fees, charges) on table export to file extension {tab_ext}. Specify table or export to .xls or .xlsx to continue.",bold=True,fg='yellow')
# 		elif tab_ext == ".xz" or tab_ext == ".json" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".pkl" or tab_ext == ".dta":
# 			pass
# 		else:
# 			raise Exception("Invalid table output file extension! Must write to .xls, .xlsx, .csv, .json, or .dta.")
# 	conf_no_echo = pd.Series({'input_path': input_path, 'table_out': table_path, 'table_ext': tab_ext, 'table': table, 'archive_out': archive_path, 'archive_ext': arc_ext, 'appendArchive': appendArchive, 'appendTable': appendTable, 'old_archive': old_archive, 'old_table': old_table, 'warn': warn, 'log': print_log, 'overwrite': overwrite, 'queue': queue, 'count': max_cases, 'path_mode': pathMode, 'drop_cols': drop_cols, 'drop': drop, 'tablog': tablog, 'dedupe': dedupe, 'launch': launch, 'no_write': no_write, 'mk_archive': mk_archive, 'content_length': content_length }) 
# 	lc = log_config(conf_no_echo)
# 	conf = pd.Series({'input_path': input_path, 'table_out': table_path, 'table_ext': tab_ext, 'table': table, 'archive_out': archive_path, 'archive_ext': arc_ext, 'appendArchive': appendArchive, 'appendTable': appendTable, 'old_archive': old_archive, 'old_table': old_table, 'warn': warn, 'log': print_log, 'overwrite': overwrite, 'queue': queue, 'count': max_cases, 'path_mode': pathMode, 'drop_cols': drop_cols, 'drop': drop, 'tablog': tablog, 'dedupe': dedupe, 'launch': launch, 'echo': lc, 'no_write': no_write, 'mk_archive': mk_archive, 'content_length': content_length }) 
# 	return conf
# def splitext(path: str):
# 	head = os.path.split(path)[0]
# 	tail = os.path.split(path)[1]
# 	ext = os.path.splitext(path)[1] 
# 	return pd.Series({
# 		'head': head,
# 		'tail': tail,
# 		'ext': ext
# 	})
# def checkPath(path: str, warn=False):
# 	PathType = ""
# 	if os.path.isdir(path):
# 		count = len(glob.glob(path + '**/*.pdf', recursive=True))
# 		if count == 0:
# 			PathType = "bad"
# 			warnings.warn("No PDFs found in input path!")
# 		if count > 0:
# 			PathType = "pdf_directory"
# 			if warn:
# 				click.echo(f"\nAlacorder found {count} PDFs in input directory.")
# 			return PathType
# 	else:
# 		head = os.path.split(path)[0]
# 		tail = os.path.split(path)[1]
# 		ext = os.path.splitext(path)[1]

# 		if not os.path.isdir(head):
# 			PathType = "bad"
# 			warnings.warn("ERROR: Invalid output path!")
# 			return PathType

# 		if os.path.isfile(path):
# 			if ext == ".txt":
# 				PathType = "text"
# 				if warn:
# 					click.echo(f"WARNING: text file input experimental!")
# 			if ext == ".pdf":
# 				PathType = "pdf"
# 			if ext == ".xz":
# 				test = pd.read_pickle(path,compression="xz")
# 				if "AllPagesText" in test.columns:
# 					PathType = "existing_archive"
# 					if warn:
# 						click.echo(f"Found existing archive with {test.shape[0]} cases.")
# 					return PathType
# 				else:
# 					PathType = "overwrite_archive"
# 					if warn:
# 						click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
# 					return PathType
# 			elif ext == ".xls" or ext == ".xlsx":
# 				if warn:
# 					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
# 				PathType = "overwrite_all_table"
# 				return PathType
# 			elif ext == ".csv" or ext == ".json" or ext == ".dta":
# 				if warn:
# 					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
# 				PathType = "overwrite_table"
# 				return PathType
# 			else:
# 				PathType = "bad"
# 				if warn:
# 					click.echo("Output file extension not supported!")
# 				if warn:
# 					click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
# 				return PathType
# 		else:
# 			if ext == ".xls" or ext == ".xlsx":
# 				PathType = "all_table"
# 				return PathType
# 			elif ext == ".xz":
# 				PathType = "archive"
# 				return PathType
# 			elif ext == ".csv" or ext == ".json" or ext == ".dta" or ext == ".txt":
# 				PathType = "table"
# 				return PathType
# 			else:
# 				PathType = "bad"
# 				warnings.warn("Output file extension not supported!")
# 				return PathType
# 	return PathType
# def pickTable():
# 	pick = "".join(input())
# 	if pick == "A":
# 		table = "cases"
# 	elif pick == "B":
# 		table = "fees"
# 	elif pick == "C":
# 		table = "charges"
# 	elif pick == "D":
# 		table = "disposition"
# 	elif pick == "E":
# 		table = "filing"
# 	else:
# 		print("Warning: invalid selection - defaulting to \'cases\'...")
# 		table = "cases"
# 	return table


@click.command()
@click.option('--input-path','-in',required=True,prompt=title,help="Path to input archive or PDF directory")
@click.option('--output-path','-out',prompt=both,help="Path to output table (.xls, .xlsx, .csv, .json, .dta) or archive (.pkl.xz)")
@click.option('--table', show_default=False, help="Table export choice")
@click.option('--archive',type=bool, is_flag=True, default=False, help='Write archive to output.pkl.xz')
@click.option('--count',default=0, help='Max cases to pull from input',show_default=False)
@click.option('--no-bar', default=False, is_flag = True, help="Print progress bar, log to console", show_default=False)
@click.option('--warn', default=False, is_flag=True, help="Print warnings from alacorder, pandas, and other dependencies to console", show_default=True, hidden=True)
@click.option('--overwrite', default=False, help="Overwrite output path if exists (cannot be used with append mode)", is_flag=True, show_default=True)
@click.option('--launch', default=False, is_flag=True, help="Launch export in default application upon completion", show_default=True)
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path",hidden=True) # not yet func
@click.option('--dedupe', default=False, is_flag=True, help="Remove duplicate cases from input archive") # not yet func
@click.option('--log', default=False, is_flag=True, help="Print outputs to console upon completion")
@click.option('--no-prompt', default=False, is_flag=True, help="Don't give confirmation prompts")
def cli(input_path, output_path, table, archive, count, no_bar, warn, overwrite, launch, no_write, dedupe, log, no_prompt):
	"""
	ALACORDER beta 73 

	Alacorder processes case detail PDFs into data tables suitable for research purposes. Alacorder also generates compressed text archives from the source PDFs to speed future data collection from the same set of cases.

	© 2023 Sam Robson	https://github.com/sbrobson959/alacorder
	"""
	path = input_path
	output = output_path
	bar = no_bar
	supportTable = True
	supportArchive = archive
	prompted_overwrite = False
	incheck = conf.checkPath(path)
	if incheck == "pdf":
		supportTable = False
	if incheck == "text":
		supportTable = False
	if incheck == "pdf_directory":
		supportArchive = True
	if incheck == "existing_archive":
		supportArchive = False
	if incheck == "archive":
		supportArchive = False
		click.secho("Invalid input path!", nl=True, bold=True, fg='red')
	if incheck == "overwrite_table" or incheck == "table" or incheck == "bad" or incheck == "":
		supportTable = False
		supportArchive = False
		click.secho("Invalid input path!", nl=True, bold=True, fg='red')

	if (table == "" or table == "none") and archive == False and ((os.path.splitext(output)[1] != ".xls" and os.path.splitext(output)[1] != ".xlsx") or os.path.splitext(output)[1]==".xz"):
		if click.getchar("Make [A]rchive or [T]able? [A/T]") == "A":
			supportTable = False 
			supportArchive = True
		else:
			supportArchive = False
			supportTable = True


	outcheck = conf.checkPath(output)

	if "archive" in outcheck and archive==False:
		archive = True
		supportArchive = True

	if overwrite == False and (outcheck == "overwrite_archive" or outcheck == "overwrite_table" or outcheck == "overwrite_all_tables"):
		if no_prompt:
			overwrite = True
			archive = True
		else:
			if click.confirm("Warning: Existing file at output path will be written over! Continue in OVERWRITE MODE?"):
				overwrite = True
				archive = True
			else:
				raise Exception("Alacorder quit.")

	if overwrite == True and outcheck == "existing_archive" and prompted_overwrite == False:
		if no_prompt:
			archive = True
		else:
			click.secho("OVERWRITE MODE is enabled. Existing file at output will be replaced!",bold=True,fg='red')
			if click.confirm("Continue?"):
				archive = True
			else:
				archive = True
				click.secho("APPEND MODE is now enabled.",bold=True,fg='magenta')
				if click.confirm("Continue?"):
					overwrite == False
				else:
					raise Exception("Alacorder quit.")

	if overwrite == False and outcheck == "existing_archive":
		if no_prompt:
			archive = True
			supportArchive = True
		else:
			if click.confirm("Appending to existing file at output path. Continue?"):
				archive = True
			else:
				if click.confirm("Do you want to continue in OVERWRITE MODE and overwrite the existing file at output path?"):
					click.secho("OVERWRITE MODE enabled.",bold=True,fg='red')
					overwrite = True
					prompted_overwrite = True
					archive = True
					supportArchive = True
				else:
					raise Exception("Alacorder quit.")
	if outcheck == "archive" or outcheck == "existing_archive":
		supportTable = False

	if os.path.splitext(output)[1] == ".xls" or os.path.splitext(output)[1] == ".xlsx":
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.secho("\n>>	Successfully configured!\n", fg='green',bold=True,overline=True)
				click.secho(a.echo,nl=True, italic=True)
				b = alac.parseCases(a)
		except ValueError:
			raise Exception("Failed to configure!")

 
	if supportArchive == False and (outcheck == "archive" or outcheck == "existing_archive"):
		supportTable = False
		supportArchive = False
		click.secho("Table export file extension not supported!",nl=True,bold=True)

	if supportTable == False and supportArchive == False:
		click.secho("Failed to configure export!",nl=True)

	def getBool(y):
		if isinstance(y, str):
			if y == "":
				return False
			else:
				return True
		if isinstance(y, bool):
			return bool(y)

	if archive:
		a = conf.config(path, archive_path=output, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, mk_archive=True, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.secho("\n>>	Successfully configured!\n", fg='green',bold=True,overline=True)
				click.secho(a.echo,nl=True, italic=True)
				b = alac.writeArchive(a)
		except ValueError:
			raise Exception("Failed to configure!")		

		
	if supportTable and (outcheck == "table" or outcheck == "overwrite_table"):
		pick = click.getchar(pick_table)
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
			if warn:
				click.secho("WARNING: Invalid table selection - defaulting to \'cases\'...")
			table = "cases"
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.secho("\n>>	Successfully configured!\n", fg='green',bold=True,overline=True)
				click.secho(a.echo,nl=True, italic=True)
				b = alac.parseTable(a)
		except ValueError:
			raise Exception("Failed to configure!")


	elif supportTable and (outcheck == "all" or outcheck == "all_tables" or outcheck == "overwrite_all_tables"):
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn,max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.secho("\n>>	Successfully configured!\n", fg='green',bold=True,overline=True)
				click.secho(a.echo,nl=True, italic=True)
				b = alac.parseTable(a)
		except ValueError:
			raise Exception("Failed to configure!")


if __name__ == '__main__':
	cli()

