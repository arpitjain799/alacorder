# alacorder beta 73 CLI
from alacorder import alac
import pandas as pd
import numpy as np
import click
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

Enter input and output paths: 

'''

text_p = '''

Enter path to output text file (must be .txt): 

'''

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

def splitext(path: str):
    head = os.path.split(path)[0]
    tail = os.path.split(path)[1]
    ext = os.path.splitext(path)[1] 
    return pd.Series({
	'head': head,
	'tail': tail,
	'ext': ext
	})

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
@click.option('--pager', default=False, is_flag=True, help="Open pager view of outputs upon completion")
def cli(input_path, output_path, table, archive, count, no_bar, warn, overwrite, launch, no_write, dedupe, pager):
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
	incheck = alac.checkPath(path)
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
		click.echo("Invalid input path!")
	if incheck == "overwrite_table" or incheck == "table" or incheck == "bad" or incheck == "":
		supportTable = False
		supportArchive = False
		click.echo("Invalid input path!")

	if (table == "" or table == "none") and archive == False and ((os.path.splitext(output)[1] != ".xls" and os.path.splitext(output)[1] != ".xlsx") or os.path.splitext(output)[1]==".xz"):
		if click.getchar("Make [A]rchive or [T]able? [A/T]") == "A":
			supportTable = False 
			supportArchive = True
		else:
			supportArchive = False
			supportTable = True


	outcheck = alac.checkPath(output)

	if "archive" in outcheck and archive==False:
		if click.confirm("Make archive?"):
			archive = True
			supportArchive = True
		else:
			raise Exception("Alacorder quit.")

	if overwrite == False and (outcheck == "overwrite_archive" or outcheck == "overwrite_table" or outcheck == "overwrite_all_tables"):
		if click.confirm("Warning: Existing file at output path will be written over! Continue in OVERWRITE MODE?"):
			overwrite = True
			archive = True
		else:
			raise Exception("Alacorder quit.")
	if overwrite == False and outcheck == "existing_archive":
		if click.confirm("Appending to existing file at output path. Continue?"):
			archive = True
		else:
			raise Exception("Alacorder quit.")

	if outcheck == "archive" or outcheck == "existing_archive":
		supportTable = False

	if os.path.splitext(output)[1] == ".xls" or os.path.splitext(output)[1] == ".xlsx":
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, pager=pager, no_write=no_write)
		click.echo(a.echo)
		b = alac.parseCases(a)
 
	if supportArchive == False and (outcheck == "archive" or outcheck == "existing_archive"):
		supportTable = False
		supportArchive = False
		click.echo("Table export file extension not supported!")

	if supportTable == False and supportArchive == False:
		click.echo("Failed to configure export!")

	def getBool(y):
		if isinstance(y, str):
			if y == "":
				return False
			else:
				return True
		if isinstance(y, bool):
			return bool(y)

	if archive:
		a = alac.config(path, archive_path=output, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, mk_archive=True, dedupe=dedupe, pager=pager, no_write=no_write)
		click.echo(a.echo)
		b = a.map(lambda x: getBool(x))
		c = a[b == True]
		b = alac.writeArchive(a)


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
				click.echo("WARNING: Invalid table selection - defaulting to \'cases\'...")
			table = "cases"
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, pager=pager, no_write=no_write)
		click.echo(a.echo)
		b = a.map(lambda x: getBool(x))
		c = a[b == True]
		b = alac.parseTable(a)

	elif supportTable and (outcheck == "all" or outcheck == "all_tables" or outcheck == "overwrite_all_tables"):
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn,max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, pager=pager, no_write=no_write)
		click.echo(a.echo)
		b = alac.parseTable(a)


if __name__ == '__main__':
	cli()
