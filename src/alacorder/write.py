# write 74
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
from alacorder import get 
from alacorder import parse 
from alacorder import config 
from alacorder import logs
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass

def now(conf, outputs, archive=False):
    """
    Writes outputs to path in conf
    """
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    arc_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    max_cases = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    dedupe = conf['DEDUPE']
    launch = conf['LAUNCH']
    OLD_ARCHIVE = conf['OLD_ARCHIVE']
    path_out = conf['OUTPUT_PATH'] if conf['MAKE'] != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf['MAKE'] == "archive" else ''
    appendTable = conf['APPEND']
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    if appendTable and isinstance(old_table, pd.core.frame.DataFrame):
        out = [outputs, old_table]
        outputs = pd.concat(out)

    if isinstance(OLD_ARCHIVE, pd.core.frame.DataFrame):
        try:
            outputs = OLD_ARCHIVE.append(outputs)
        except (AttributeError, TypeError):
          outputs = pd.Series([OLD_ARCHIVE, outputs])

    try:
        out_ext = os.path.splitext(path_out)[1]
    except TypeError:
        out_ext = ""

    if out_ext == ".xls":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table",engine="openpyxl")
        except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            try:
                with pd.ExcelWriter(path_out,engine="xlwt") as writer:
                    outputs.to_excel(writer, sheet_name="output-table")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                try:
                    if not appendTable:
                        os.remove(path_out)
                except:
                    pass
                outputs.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                if warn or print_log:
                    click.echo(f"Fallback export to {os.path.splitext(path_out)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")

    if out_ext == ".xlsx":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table", engine="openpyxl")
        except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            try:
                with pd.ExcelWriter(path_out[0:-1]) as writer:
                    outputs.to_excel(writer, sheet_name="output-table", engine="xlsxwriter")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                try:
                    if not appendTable:
                        os.remove(path_out)
                except:
                    pass
                outputs.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                if warn or print_log:
                    click.echo(f"Fallback export to {os.path.splitext(path_out)[0] + "-cases.json.zip"} due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
    elif out_ext == ".pkl":
        outputs.to_pickle(path_out+".xz",compression="xz")
    elif out_ext == ".xz":
        outputs.to_pickle(path_out,compression="xz")
    elif out_ext == ".json":
        outputs.to_json(path_out,orient='table')
    elif out_ext == ".csv":
        outputs.to_csv(path_out,escapechar='\\')
    elif out_ext == ".txt":
        outputs.to_string(path_out)
    elif out_ext == ".dta":
        outputs.to_stata(path_out)
    else:
        pass
    return outputs 

def archive(conf): 
    """
    Write full text archive to file.pkl.xz
    """
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    arc_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    max_cases = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    dedupe = conf['DEDUPE']
    old_archive = conf['OLD_ARCHIVE']
    append = conf['APPEND']
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")
    if warn or log:
        click.echo(click.style("* ",blink=True) + "Creating full text archive...")

    if not from_archive:
        allpagestext = pd.Series(queue).map(lambda x: get.PDFText(x))
    else:
        allpagestext = pd.Series(queue)

    outputs = pd.DataFrame({
        'Path': queue if from_archive else np.nan,
        'AllPagesText': allpagestext,
        'Timestamp': start_time,
        })

    if append:
        try:
            new = [old_archive, outputs]
            outputs = pd.concat(new,ignore_index=True)
        except:
            pass

    outputs.fillna('',inplace=True)

    if not no_write:
        outputs.to_pickle(path_out,compression="xz")
    parse.logs.complete(conf, start_time, outputs)
    return outputs
