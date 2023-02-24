# log 74
# Sam Robson

import os
import sys
import glob
import re
import math
import xarray
import numpy as np
import datetime
import pandas as pd
import time
import warnings
import click
import inspect
from alacorder import get
from alacorder import parse
from alacorder import write
from alacorder import config

def echo_conf(input_path,make,output_path,overwrite,no_write,dedupe,launch,warn,no_prompt):
	d = click.style(f"""\n* Successfully configured!\n""",fg='green', bold=True)
	e = click.style(f"""INPUT: {input_path}\n{'TABLE' if make == "multiexport" or make == "singletable" else 'ARCHIVE'}: {output_path}\n""",fg='bright_yellow',bold=True)
	f = click.style(f"""{"OVERWRITE is enabled. Alacorder will overwrite existing files at output path! " if overwrite else ''}{"NO-WRITE is enabled. Alacorder will NOT export outputs. " if no_write else ''}{"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output. " if dedupe else ''}{"LAUNCH is enabled. Upon completion, Alacorder will attempt to launch exported file in default viewing application. " if launch and make != "archive" else ''}{"WARN is enabled. All warnings from pandas and other modules will print to console. " if warn else ''}{"NO_PROMPT is enabled. All user confirmation prompts will be suppressed as if set to default by user." if no_prompt else ''}""".strip(), italic=True, fg='white')
	return d + e + "\n" + f + "\n"

def complete(conf, start_time, output=None):
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	arc_out = conf['OUTPUT_PATH']
	archive_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	count = conf['COUNT']
	queue = conf['QUEUE']
	print_log = conf['LOG']
	warn = conf['WARN']
	no_write = conf['NO_WRITE']
	dedupe = conf['DEDUPE']
	table = conf['TABLE']
	dedupe = conf['DEDUPE']
	from_archive = True if conf['IS_FULL_TEXT']==True else False

	completion_time = time.time()
	elapsed = completion_time - start_time
	cases_per_sec = count/elapsed

	if print_log:
		click.secho(f'''\n* Task completed!\n''',bold=True,fg='green')

def debug(conf, *msg):
	if conf['DEBUG'] == True:
		click.echo(msg)

def echo(conf, *msg):
	if conf['LOG']==True:
		click.echo(msg)

def echo_red(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='bright_red',bold=True),nl=True)
		return click.style(text,fg='bright_red',bold=True)
	else:
		return click.style(text,fg='bright_red',bold=True)
def echo_yellow(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='bright_yellow',bold=True),nl=True)
		return click.style(text,fg='bright_yellow',bold=True)
	else:
		return click.style(text,fg='bright_yellow',bold=True)
def echo_green(text, echo=True):
	if echo:
		click.echo(click.style(text,fg='bright_green',bold=True),nl=True)
		return click.style(text,fg='bright_green',bold=True)
	else:
		return click.style(text,fg='bright_green',bold=True)

upick_table = ('''
Select preferred table output below.
	A:  Case Details
	B:  Fee Sheets
	C:  Charges (all)
	D:  Charges (disposition only)
	E:  Charges (filing only)

>> Enter A, B, C, D, or E to continue:

''')
def pick_table():
	return click.style(upick_table,bold=True)
ujust_table = ('''

EXPORT DATA TABLE: To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format (.csv, .json, .dta), select a table after entering output file path.

>> Enter path:

''')

def just_table():
	return click.style(ujust_table,bold=True)
uboth =  ('''

EXPORT FULL TEXT ARCHIVE: To process case inputs into a full text archive (recommended), enter archive path below with file extension .pkl.xz.

EXPORT DATA TABLE: To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format (.csv, .json, .dta), select a table after entering output file path.

>> Enter path:

''')

def both():
	return click.style(uboth,fg='bright_white')
utitle = ('''

ALACORDER beta 74
© 2023 Sam Robson

Alacorder processes case detail PDFs into data tables suitable for research purposes. Alacorder also generates compressed text archives from the source PDFs to speed future data collection from the same set of cases.

ACCEPTED      /pdfs/path/   PDF directory           
INPUTS:       .pkl.xz       Compressed archive      

>> Enter input path: 

''')

def title():
	return click.style(utitle,fg='bright_white')

utext_p = ('''

>> Enter path to output text file (must be .txt): 

''')

def text_p():
	return click.style(utext_p,bold=True)




