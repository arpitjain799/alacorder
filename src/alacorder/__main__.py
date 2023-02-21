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
upick_table = '''
>>  Select preferred table output below.
	A:  Case Details
	B:  Fee Sheets
	C:  Charges (all)
	D:  Charges (disposition only)
	E:  Charges (filing only)

Enter A, B, C, D, or E to continue:

'''
pick_table = click.style(upick_table,bold=True)

ujust_table = '''
	--------------------------------------------------------
	|  ALL TABLE     .xlsx         Excel spreadsheet       |
	|  OUTPUTS:      .xls          Excel \'97-\'03           |
	|------------------------------------------------------|
	|  SINGLE        .csv          Comma-separated values  |
	|  TABLE         .json         JavaScript obj. not.    |
	|  OUTPUTS:      .dta          Stata dataset           |
	|                .txt          Text file - no reimport!|
	--------------------------------------------------------
>>  EXPORT DATA TABLE:

	To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format, select a table after entering output file path.

Enter path:

'''
just_table = click.style(ujust_table,bold=True)

uboth =  '''
	--------------------------------------------------------
	|  ALL TABLE     .xlsx         Excel spreadsheet       |
	|  OUTPUTS:      .xls          Excel \'97-\'03           |
	|------------------------------------------------------|
	|  SINGLE        .csv          Comma-separated values  |
	|  TABLE         .json         JavaScript obj. not.    |
	|  OUTPUTS:      .dta          Stata dataset           |
	|                .txt          Text file - no reimport!|
	|------------------------------------------------------|
	|  ARCHIVE:      .pkl.xz       Compressed archive      |
	--------------------------------------------------------

EXPORT FULL TEXT ARCHIVE: To process case inputs into a full text archive (recommended), enter archive path below with file extension .pkl.xz.

EXPORT DATA TABLE: To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format, select a table after entering output file path.

Enter path:

'''
both = click.style(uboth,fg='bright_white')
utitle = '''

ALACORDER beta 73
© 2023 Sam Robson

Alacorder processes case detail PDFs into data tables suitable for research purposes. Alacorder also generates compressed text archives from the source PDFs to speed future data collection from the same set of cases.

--------------------------------------------------------
INPUTS:       /pdfs/path/   PDF directory           
              .pkl.xz       Compressed archive      
--------------------------------------------------------

Enter input path: 

'''

title = click.style(utitle,fg='bright_white',bold=True)

utext_p = '''

Enter path to output text file (must be .txt): 

'''
text_p = click.style(utext_p,bold=True)

def print_red(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='red',bold=True,nl=True))
		return click.style(text,fg='red',bold=True,nl=True)
	else:
		return click.style(text,fg='red',bold=True,nl=True)
def print_yellow(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='bright_yellow',bold=True,nl=True))
		return click.style(text,fg='bright_yellow',bold=True,nl=True)
	else:
		return click.style(text,fg='bright_yellow',bold=True,nl=True)
def print_green(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='bright_green',bold=True,nl=True))
		return click.style(text,fg='bright_green',bold=True,nl=True)
	else:
		return click.style(text,fg='bright_green',bold=True,nl=True)

def load():
	click.echo(click.style(". . .", fg='yellow', blink=True))

@click.command()
@click.option('--input-path','-in',required=True,prompt=title,help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path','-out',prompt=both,help="Path to output table (.xls, .xlsx, .csv, .json, .dta) or archive (.pkl.xz)", show_choices=False)
@click.option('--count',default=0, help='Max cases to pull from input',show_default=False)
@click.option('--archive',type=bool, is_flag=True, default=False, help='Write archive to output.pkl.xz')
@click.option('--table', help="Table export choice")
@click.option('--no-bar', default=False, is_flag = True, help="Don't print progress bar", show_default=False)
@click.option('--warn', default=False, is_flag=True, help="Print warnings from alacorder, pandas, and other dependencies to console", show_default=True, hidden=True)
@click.option('--overwrite', default=False, help="Overwrite output path if exists (cannot be used with append mode)", is_flag=True, show_default=True)
@click.option('--launch', default=False, is_flag=True, help="Launch export in default application upon completion", show_default=True)
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path",hidden=True)
@click.option('--dedupe', default=False, is_flag=True, help="Remove duplicate cases from input archive",hidden=True) # not yet func
@click.option('--log', default=False, is_flag=True, help="Print outputs to console upon completion")
@click.option('--no-prompt', default=False, is_flag=True, help="Don't give confirmation prompts")
def cli(input_path, output_path, count, archive, table, no_bar, warn, overwrite, launch, no_write, dedupe, log, no_prompt):
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
		print_red("Invalid input path!")
	if incheck == "overwrite_table" or incheck == "table" or incheck == "bad" or incheck == "":
		supportTable = False
		supportArchive = False
		print_red("Invalid input path!")

	if (table == "" or table == "none") and archive == False and ((os.path.splitext(output)[1] != ".xls" and os.path.splitext(output)[1] != ".xlsx") or os.path.splitext(output)[1]==".xz"):
		if click.input("Make [A]rchive or [T]able? [A/T]") == "A":
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
			if click.confirm(print_red("Warning: Existing file at output path will be written over! Continue in OVERWRITE MODE?",echo=False)):
				overwrite = True
				archive = True
			else:
				raise Exception("Alacorder quit.")

	if overwrite == True and outcheck == "existing_archive" and prompted_overwrite == False:
		if no_prompt:
			archive = True
		else:
			print_yellow("OVERWRITE MODE is enabled. Existing file at output will be replaced!")
			if click.confirm("Continue?"):
				archive = True
			else:
				archive = True
				print_green("APPEND MODE is now enabled.")
				if click.confirm("Continue?"):
					overwrite == False
				else:
					raise Exception("Alacorder quit.")

	if overwrite == False and outcheck == "existing_archive":
		if no_prompt:
			archive = True
			supportArchive = True
		else:
			if click.confirm(click.style("Appending to existing file at output path. Continue?",fg='yellow')):
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
		load()
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.clear()
				click.secho("\nSuccessfully configured!\n", fg='green',bold=True,overline=True)
				click.echo(a.echo)
				b = alac.parseCases(a)
		except ValueError:
			raise Exception("Failed to configure!")

 
	if supportArchive == False and (outcheck == "archive" or outcheck == "existing_archive"):
		supportTable = False
		supportArchive = False
		click.secho("Table export file extension not supported!",nl=True,bold=True,fg='red')

	if supportTable == False and supportArchive == False:
		click.secho("Failed to configure export!",nl=True,fg='red')

	def getBool(y):
		if isinstance(y, str):
			if y == "":
				return False
			else:
				return True
		if isinstance(y, bool):
			return bool(y)

	if archive:
		load()
		a = conf.config(path, archive_path=output, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, mk_archive=True, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.clear()
				click.secho("\nSuccessfully configured!\n", fg='green',bold=True,overline=True)
				click.echo(a.echo)
				b = alac.writeArchive(a)
		except ValueError:
			raise Exception("Failed to configure!")		

		
	if supportTable and (outcheck == "table" or outcheck == "overwrite_table"):
		pick = click.input(pick_table)
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
		load()
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.clear()
				click.secho("\nSuccessfully configured!", fg='green',bold=True,overline=True)
				click.echo(a.echo)
				b = alac.parseTable(a)
		except ValueError:
			raise Exception("Failed to configure!")


	elif supportTable and (outcheck == "all" or outcheck == "all_tables" or outcheck == "overwrite_all_tables"):
		load()
		a = conf.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn,max_cases=count, overwrite=overwrite, launch=launch, dedupe=dedupe, tablog=log, no_write=no_write)
		try:
			if len(a.input_path) > 0:
				click.clear()
				click.secho("\nSuccessfully configured!\n", fg='green',bold=True,overline=True)
				click.echo(a.echo)
				b = alac.parseTable(a)
		except ValueError:
			raise Exception("Failed to configure!")


if __name__ == '__main__':
	cli()

