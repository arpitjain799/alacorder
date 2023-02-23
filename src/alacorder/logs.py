# log 74
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
from alacorder import get #
from alacorder import write #
from alacorder import config #
from alacorder import parse
from alacorder import logs
import PyPDF2
from io import StringIO
try:
	import xlsxwriter
except ImportError:
	pass
def echo_conf(input_path,make,output_path,overwrite,append,no_write,dedupe,launch,warn,no_prompt):
	d = click.style(f"""\n* Successfully configured!\n""",fg='green', bold=True)
	e = click.style(f"""INPUT: {input_path}\n{'TABLE' if make == "multiexport" or make == "singletable" else 'ARCHIVE'}: {output_path}\n""",fg='bright_yellow',bold=True)
	f = click.style(f"""{"OVERWRITE is enabled. Alacorder will overwrite existing files at output path! " if overwrite else ''}{"APPEND is enabled. Alacorder will attempt to append outputs to existing file at path. " if append else ''}{"NO-WRITE is enabled. Alacorder will NOT export outputs. " if no_write else ''}{"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output. " if dedupe else ''}{"LAUNCH is enabled. Upon completion, Alacorder will attempt to launch exported file in default viewing application. " if launch and make != "archive" else ''}{"WARN is enabled. All warnings from pandas and other modules will print to console. " if warn else ''}{"NO_PROMPT is enabled. All user confirmation prompts will be suppressed as if set to default by user." if no_prompt else ''}""".strip(), italic=True, fg='white')
	return d + e + "\n" + f + "\n"

def complete(conf, start_time, output=None):
	path_in = conf['INPUT_PATH']
	path_out = conf['OUTPUT_PATH']
	arc_out = conf['OUTPUT_PATH']
	archive_out = conf['OUTPUT_PATH']
	out_ext = conf['OUTPUT_EXT']
	max_cases = conf['COUNT']
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
	cases_per_sec = max_cases/elapsed
	if print_log:
		click.secho(output)
	if print_log:
		click.echo(f'''TASK COMPLETED: Successfully processed {max_cases} cases. Last batch completed in {elapsed:.2f} seconds ({cases_per_sec:.2f} cases/sec)''')
def debug(conf, *msg):
	if conf.DEBUG == True:
		click.echo(msg)
		return msg
	else:
		return ""
def console(conf, *msg):
	if conf.LOG==True:
		click.echo(msg)

def echo(conf, *msg, echo=True):
	if conf.LOG==True and echo==True:
		click.echo(msg)
	return msg

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