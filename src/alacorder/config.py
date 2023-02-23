# conf 75
# in progress
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
from alacorder import logs #
from alacorder import get 
from alacorder import parse
from alacorder import write
import PyPDF2
from io import StringIO
import warnings
try:
    import xlsxwriter
except ImportError:
    pass

warnings.filterwarnings('ignore')

def inputs(path):
    found = 0
    is_full_text = False
    good = False
    pickle = None
    queue = pd.Series()
    
    if os.path.isdir(path): # if PDF directory -> good
        queue = pd.Series(glob.glob(path + '**/*.pdf', recursive=True))
        if queue.shape[0] > 0:
            found = len(queue)
            good = True
    elif os.path.isfile(path) and os.path.splitext(path)[1] == ".xz": # if archive -> good
        good = True
        try:
            pickle = pd.read_pickle(path,compression="xz")
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
        except:
            good = False
    else:
        good = False

    if good:
        echo = click.style(f"\nFound {found} cases in input.",fg='bright_blue',bold=True)
    else:
        echo = click.style(f"""Alacorder failed to configure input! Try again with a valid PDF directory or full text archive path, or run 'python -m alacorder --help' in command line for more details.""",fg='red',bold=True)

    out = pd.Series({
        'INPUT_PATH': path,
        'IS_FULL_TEXT': is_full_text,
        'QUEUE': queue,
        'FOUND': found,
        'GOOD': good,
        'PICKLE': pickle,
        'ECHO': echo
        })
    return out

def outputs(path):
    is_appendable = False
    good = False
    make = None
    pickle = None
    old_archive = None
    old_count = 0
    exists = os.path.isfile(path)
    ext = os.path.splitext(path)[1]
    if os.path.splitext(path)[1] == ".xz": # if output is existing archive
        make = "archive"
        good = True
        try:
            pickle = pd.read_pickle(path,compression="xz")
            old_archive = pickle['AllPagesText']
            old_count = old_archive.shape[0]
            if old_count > 0:
                is_appendable = True
        except:
            is_appendable = False
    if os.path.splitext(path)[1] == ".xlsx" or os.path.splitext(path)[1] == ".xls": # if output is multiexport
        make = "multiexport"
        table = "all"
        good = True
    if os.path.splitext(path)[1] == ".csv" or os.path.splitext(path)[1] == ".dta" or os.path.splitext(path)[1] == ".json" or os.path.splitext(path)[1] == ".txt" or os.path.splitext(path)[1] == ".pkl":
        make = "singletable"
        good = True
    if good:
        echo = click.style(f"""Output path successfully configured for {"table" if (make == "multiexport" or make == "singletable") else "archive"} export. {"Existing archive at output path supports append mode. Check overwrite settings before proceeding..." if is_appendable else ""}""",fg='bright_blue',bold=True) 
    else:
        echo = click.style(f"Alacorder failed to configure output! Try again with a valid path to a file with a supported extension, or run 'python -m alacorder --help' in command line for more details.",fg='red',bold=True)

    out = pd.Series({
        'OUTPUT_PATH': path,
        'OUTPUT_EXT': ext,
        'MAKE': make,
        'GOOD': good,
        'IS_APPENDABLE': is_appendable,
        'EXISTING_FILE': exists,
        'OLD_ARCHIVE': old_archive,
        'OLD_ARCHIVE_COUNT': old_count,
        'ECHO': echo
        })
    return out

def set(inputs,outputs,count=0,table='',overwrite=False,append=True,launch=False,log=True,dedupe=False,warn=False,no_write=False,no_prompt=False,skip_echo=False,debug=False):

    status_code = []
    echo = ""
    will_append = False
    will_archive = False
    will_overwrite = False
    good = True

    ## NON-APPENDABLE EXISTING FILES 
    ## if no --append flag -> all treated as non-appendable
    if overwrite == False and outputs.EXISTING_FILE == True and (outputs.IS_APPENDABLE==False or append==False):
        good = False
        status_code += ["APPEND_OVERWRITE_DEFAULT_OVERWRITE"]
        if not skip_echo:
            echo += click.style(f"Existing file at output path cannot be appended to! Reconfigure in OVERWRITE MODE (--overwrite) to continue. ",fg='red',bold=True)
    elif overwrite == True and outputs.EXISTING_FILE == True and (outputs.IS_APPENDABLE==False or append==False):
        if not skip_echo:
            will_overwrite = True
            echo += click.style(f"Existing file at output path will be OVERWRITTEN! ",fg='yellow',bold=True)
    ## APPENDABLE EXISTING FILES
        # Classic append mode
    elif overwrite == False and outputs.EXISTING_FILE == True and (outputs.IS_APPENDABLE==True and append==True):
        if not skip_echo:
            will_append = True
            echo += click.style(f"Existing file at output path will be appended to. ",fg='bright_blue',bold=True)
        # Overwrite and append enabled -> default append
    elif overwrite == True and outputs.EXISTING_FILE == True and (outputs.IS_APPENDABLE==True and append==True):
        if not skip_echo:
            will_append = True
            echo += click.style(f"Warning: '--append' and '--overwrite' flags are both enabled. DEFAULTING TO APPEND MODE. Existing file at output path will be appended to. Use flag '--help' for more details. ",fg='yellow',bold=True)
            status_code += ["APPEND_OVERWRITE_DEFAULT_APPEND"]
    else:
        pass

    ## COUNT 
    content_len = inputs['FOUND']
    if content_len > count and count != 0:
        ind = count - 1
        queue = inputs.QUEUE[0:ind] 
    else:
        queue = inputs.QUEUE

    ## TABLE
    if outputs.MAKE == "singletable" and (table == "" or table == None):
        table = "NEEDS_TABLE_SELECTION"
        if not skip_echo:
            echo += click.style(f"Warning: '--append' and '--overwrite' flags are both enabled. DEFAULTING TO APPEND MODE. Existing file at output path will be appended to. Use flag '--help' for more details. ",fg='red',bold=True)

    echo += logs.echo_conf(inputs.INPUT_PATH,outputs.MAKE,outputs.OUTPUT_PATH,overwrite,append,no_write,dedupe,launch,warn,no_prompt)

    out = pd.Series({
        'GOOD': good,
        'ECHO': echo,
        'STATUS_CODES': status_code,

        'QUEUE': queue,
        'COUNT': count,
        'IS_FULL_TEXT': bool(inputs.IS_FULL_TEXT),
        'MAKE': outputs.MAKE,
        'TABLE': table,

        'INPUT_PATH': inputs.INPUT_PATH,
        'OUTPUT_PATH': outputs.OUTPUT_PATH,
        'OUTPUT_EXT': outputs.OUTPUT_EXT,

        'OVERWRITE': will_overwrite,
        'APPEND': will_append,
        'OLD_ARCHIVE': outputs.OLD_ARCHIVE,
        'OLD_ARCHIVE_COUNT': outputs.OLD_ARCHIVE_COUNT,
        'FOUND': inputs.FOUND,
        'INPUT_PICKLE': inputs.PICKLE,

        'DEDUPE': dedupe, # not ready (well none of its ready but especially that)
        'LOG': log,
        'WARN': warn,
        'LAUNCH': launch,
        'NO_PROMPT': no_prompt,
        'NO_WRITE': no_write
        })

    return out

def batcher(conf):
    q = conf['QUEUE']
    if conf.IS_FULL_TEXT: 
        batchsize = q.shape[0] / 2
    else: 
        batchsize = 1000
    if conf.FOUND < 1000:
        batchsize = 100
    if conf.FOUND > 10000:
        batchsize = conf.FOUND / 20
    batches = np.array_split(conf.QUEUE, math.floor(conf.FOUND/batchsize))
    return batches

# same as calling conf.set(conf.inputs(path), conf.outputs(path), **kwargs)
def pathset(input_path, output_path, count=0, table='', overwrite=False, append=True, launch=False, log=True, dedupe=False, warn=False,no_write=False, no_prompt=False, skip_echo=False, debug=False):
    a = inputs(input_path)
    if log:
        click.echo(a.ECHO)
    b = outputs(output_path)
    if log:
        click.echo(b.ECHO)
    c = set(a,b, count=0, table='', overwrite=False, append=True, launch=False, log=True, dedupe=False, warn=False,no_write=False, no_prompt=False, skip_echo=False, debug=False)
    if log:
        click.echo(c.ECHO)
    return c



