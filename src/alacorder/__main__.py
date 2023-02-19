# alacorder beta 73 CLI

from alacorder import alac
import pandas as pd
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

>>  Enter path:

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

>>  Enter path:

	'''
title = '''
	___    __                          __
       /   |  / /___  _________  _________/ /__  _____
      / /| | / / __ `/ ___/ __ \\/ ___/ __  / _ \\/ ___/
     / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /
    /_/  |_/_/\\__,_/\\___/\\____/_/   \\__,_/\\___/_/

	    ALACORDER beta 73
	    by Sam Robson

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


'''

text_p = '''

>>  Enter path to output text file (must be .txt): 

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
@click.argument('path', type=click.Path(exists=True))
@click.argument('output', type=click.Path(dir_okay=True))
@click.option('--count',default=0, help='max cases to pull from input',show_default=False)
@click.option('--archive',type=bool, is_flag=True, default=False, help='write archive to output.pkl.xz')
@click.option('--warn', default=False, is_flag=True, help="Print warnings from alacorder, pandas, and other dependencies to console", show_default=True)
@click.option('--bar/--no-bar', default=True, help="Print progress bar, log to console", show_default=False)
@click.option('--table', default="", help="Table export choice (all, cases, fees, charges, disposition, filing)")
@click.option('--verbose', default=False, is_flag=True, help="Detailed print logs to console", show_default=False)
@click.option('--overwrite', default=False, help="Overwrite output path if exists (cannot be used with append mode)", is_flag=True, show_default=True)
@click.option('--launch', default=False, is_flag=True, help="Launch export in default application upon completion", show_default=True)
def cli(path, output, archive, count, warn, bar, table, verbose, overwrite, launch):

	if os.path.isfile(output) and overwrite == True:
		click.confirm("Existing file at output path will be overwritten! Continue anyway?")
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

	outcheck = alac.checkPath(output)

	if outcheck == "archive" or outcheck == "existing_archive":
		supportTable = False

	if os.path.splitext(output)[1] == ".xls" or os.path.splitext(output)[1] == ".xlsx":
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, verbose=verbose, max_cases=count, overwrite=overwrite, launch=launch)
		click.echo(a)
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
		a = alac.config(path, archive_path=output, GUI_mode=False, print_log=bar, warn=warn, verbose=verbose, max_cases=count, overwrite=overwrite, launch=launch, mk_archive=True)
		b = a.map(lambda x: getBool(x))
		c = a[b == True]
		click.echo(c)
		b = alac.writeArchive(a)

	if supportTable and (outcheck == "table" or outcheck == "overwrite_table"):
		pick = click.prompt(pick_table)
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
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, verbose=verbose, max_cases=count, overwrite=overwrite, launch=launch)
		b = a.map(lambda x: getBool(x))
		c = a[b == True]
		click.echo(c)
		b = alac.parseTable(a)

	elif supportTable and (outcheck == "all" or outcheck == "all_tables" or outcheck == "overwrite_all_tables"):
		a = alac.config(path, table_path=output, table=table, GUI_mode=False, print_log=bar, warn=warn, verbose=verbose, max_cases=count, overwrite=overwrite, launch=launch)
		click.echo(a)
		b = alac.parseTable(a)


if __name__ == '__main__':
	cli()
