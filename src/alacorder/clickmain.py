# clickmain test

from alacorder import alac
import click
import os
tables = ""

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

        To export data tables from case inputs, enter 
        full output path. Use .xls or .xlsx to export all
        all tables, or, if using another format, select
        a table after entering output file path.

>>  Enter path:

        '''


both =  '''
>>  EXPORT FULL TEXT ARCHIVE:

        To process case inputs into a full text 
        archive (recommended), enter archive 
        path below with file extension .pkl.xz.

>>  EXPORT DATA TABLE:

        To export data tables from case inputs, enter 
        full output path. Use .xls or .xlsx to export all
        all tables, or, if using another format, select
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

>>  Enter full path to input directory or archive file path...

'''

text_p = '''

>>  Enter path to output text file (must be .txt): 

'''
def pickTable():
        print(pick_table)
        pick = "".join(input())
        if pick == "A":
                tables = "cases"
        elif pick == "B":
                tables = "fees"
        elif pick == "C":
                tables = "charges"
        elif pick == "D":
                tables = "disposition"
        elif pick == "E":
                tables = "filing"
        else:
                print("Warning: invalid selection - defaulting to \'cases\'...")
                tables = "cases"
        return tables

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
@click.option('--count', default=0, help='max cases to pull from input')
@click.option('--warn/--no-warn', default=False, help="Print warnings from alacorder, pandas, and other dependencies to console", show_default=True)
@click.option('--log/--no-log', default=True, help="Print log to console", show_default=True)
@click.option('--table', default="", help="Table export choice (cases, fees, charges, disposition, filing)", prompt=pick_table)
@click.option('--verbose', default=False, help="Detailed print logs to console", show_default=True)
@click.option('--overwrite/--no-overwrite', default=False, help="Overwrite output path if exists (cannot be used with append mode)", show_default=True)
def start(path, output, count, warn, log, table, verbose, overwrite):
	if table == "" and (os.path.splitext(output)[1] == ".csv" or os.path.splitext(output)[1] == ".json" or os.path.splitext(output)[1] == ".dta" or os.path.splitext(output)[1] == ".txt"):
		table = click.prompt(pick_table, type=char)
	supportTable = True
	supportArchive = True
	incheck = alac.checkPath(path)
	if incheck == "pdf":
		supportTable = False
	if incheck == "text":
		supportTable = False
	if incheck == "pdf_directory":
		pass
	if incheck == "existing_archive":
		supportArchive = False
	if incheck == "archive":
		supportArchive = False
		click.echo("Invalid input path!")
		raise Exception("Invalid input path!")
	if incheck == "overwrite_table" or incheck == "table" or incheck == "bad" or incheck == "":
		supportTable = False
		supportArchive = False
		click.echo("Invalid input path!")
		raise Exception("Invalid input path!")

	outcheck = alac.checkPath(output)

	if supportTable and (outcheck == "archive" or outcheck == "existing_archive"):
		supportTable = False
		supportArchive = False
		click.echo("Table export file extension not supported!")
		raise Exception("Table export file extension not supported!")

	if supportTable == False and supportArchive == False:
		click.echo("Failed to configure export!")
		raise Exception("Failed to configure export!")

	if supportTable and (outcheck == "table" or outcheck == "overwrite_table"):
		if table != "all_tables" and table != "all" and table != "cases" and table != "fees" and table != "charges" and table != "disposition" and table != "filing":
			table = "cases"

	if overwrite == True:
		click.confirm("Existing file at output path will be overwritten! Continue anyway? [Y/N]")

	if supportArchive:
		a = alac.config(path, archive_path=output, GUI_mode=False, print_log=log, warn=warn, verbose=verbose, max_cases=count, force_overwrite=overwrite)
		click.echo(a)
		b = alac.writeArchive(a)
		return b

	if supportTable and (os.path.splitext(output)[1] == ".xls" or os.path.splitext(output)[1] == ".xlsx"):
		a = alac.config(path, table_path=output, tables=table, GUI_mode=False, print_log=log, warn=warn, verbose=verbose, max_cases=count, force_overwrite=overwrite)
		click.echo(a)
		b = alac.parseTables(a)
		return b


