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
import alacorder as alac
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
    elif os.path.splitext(path)[1] == ".xlsx" or os.path.splitext(path)[1] == ".xls": # if output is multiexport
        make = "multiexport"
        table = "all"
        good = True
    elif os.path.splitext(path)[1] == ".csv" or os.path.splitext(path)[1] == ".dta" or os.path.splitext(path)[1] == ".json" or os.path.splitext(path)[1] == ".txt" or os.path.splitext(path)[1] == ".pkl":
        make = "singletable"
        good = True
    if good:
        echo = click.style(f"""Output path successfully configured for {"table" if (make == "multiexport" or make == "singletable") else "archive"} export.""",fg='bright_blue',bold=True) 
    else:
        echo = click.style(f"Alacorder failed to configure output! Try again with a valid path to a file with a supported extension, or run 'python -m alacorder --help' in command line for help.",fg='red',bold=True)

    out = pd.Series({
        'OUTPUT_PATH': path,
        'OUTPUT_EXT': ext,
        'MAKE': make,
        'GOOD': good,
        'EXISTING_FILE': exists,
        'OLD_ARCHIVE': old_archive,
        'OLD_ARCHIVE_COUNT': old_count,
        'ECHO': echo
        })
    return out

def set(inputs,outputs,count=0,table='',overwrite=False,launch=False,log=True,dedupe=False,warn=False,no_write=False,no_prompt=False,skip_echo=False,debug=False,no_batch=False):

    status_code = []
    echo = ""
    will_archive = False
    will_overwrite = False
    good = True


    ## COUNT 
    content_len = inputs['FOUND']
    if content_len > count and count != 0:
        ind = count - 1
        queue = inputs.QUEUE[0:ind] 
    else:
        queue = inputs.QUEUE


    echo += logs.echo_conf(inputs.INPUT_PATH,outputs.MAKE,outputs.OUTPUT_PATH,overwrite,no_write,dedupe,launch,warn,no_prompt)

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
        'FOUND': inputs.FOUND,

        'DEDUPE': dedupe, # not ready (well none of its ready but especially that)
        'LOG': log,
        'WARN': warn,
        'LAUNCH': launch,
        'NO_PROMPT': no_prompt,
        'NO_WRITE': no_write,
        'NO_BATCH': no_batch
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
def setpaths(input_path, output_path, count=0, table='', overwrite=False, launch=False, log=True, dedupe=False, warn=False,no_write=False, no_prompt=False, skip_echo=False, debug=False, no_batch=False):
    a = inputs(input_path)
    if log:
        click.echo(a.ECHO)
    b = outputs(output_path)
    if log:
        click.echo(b.ECHO)
    c = set(a,b, count=0, table='', overwrite=overwrite, launch=launch, log=log, dedupe=dedupe, warn=warn,no_write=no_write, no_prompt=no_prompt, debug=debug, no_batch=no_batch)
    if log:
        click.echo(c.ECHO)
    return c



