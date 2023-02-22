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
from alacorder import __main__
from alacorder import get
from alacorder import parse
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
    max_cases = conf['count']
    old_archive = conf['old_archive']
    old_table = conf['old_table']
    appendTable = conf['appendTable']
    print_log = conf['log']

    if appendTable and isinstance(old_table, pd.core.frame.DataFrame):
        out = [outputs, old_table]
        outputs = pd.concat(out)

    if isinstance(old_archive, pd.core.frame.DataFrame):
        try:
            outputs = old_archive.append(outputs)
        except (AttributeError, TypeError):
          outputs = pd.Series([old_archive, outputs])
    if archive:
        path_out = conf['archive_out']
    else:
        path_out = conf['table_out']
    print_log = conf['log']
    warn = conf['warn']
    try:
        out_ext = os.path.splitext(path_out)[1]
    except TypeError:
        out_ext = ""

    if out_ext == ".xls":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table")
        except ValueError:
            try:
                with pd.ExcelWriter(path_out,engine="xlwt") as writer:
                    outputs.to_excel(writer, sheet_name="output-table")
            except ValueError:
                try:
                    if not appendTable:
                        os.remove(path_out)
                except:
                    pass
                outputs.to_csv(path_out,escapechar='\\')
                if warn or print_log:
                    click.echo("Exported to CSV due to XLSX engine failure")
    if out_ext == ".xlsx":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table", engine="xlsxwriter")
        except ValueError:
            try:
                with pd.ExcelWriter(path_out[0:-1]) as writer:
                    outputs.to_excel(writer, sheet_name="output-table")
            except ValueError:
                try:
                    if not appendTable:
                        os.remove(path_out)
                except:
                    pass
                outputs.to_csv(path_out+".csv",escapechar='\\')
                if warn or print_log:
                    click.echo("Exported to CSV due to XLSX engine failure")
    elif out_ext == ".pkl":
        outputs.to_pickle(path_out+".xz",compression="xz")
    elif out_ext == ".xz":
        outputs.to_pickle(path_out,compression="xz")
    elif out_ext == ".json":
        outputs.to_json(path_out)
    elif out_ext == ".csv":
        outputs.to_csv(path_out,escapechar='\\')
    elif out_ext == ".txt":
        outputs.to_string(path_out)
    elif out_ext == ".dta":
        outputs.to_stata(path_out)
    else:
        if warn:
            click.echo("Warning: Failed to export!")
    size = os.path.getsize(path_out)
    return size 

def Archive(conf): 
    """
    Write full text archive to file.pkl.xz
    """
    path_in = conf['input_path']
    path_out = conf['archive_out']
    out_ext = conf['archive_ext']
    max_cases = conf['count']
    queue = conf['queue']
    print_log = conf['log']
    warn = conf['warn']
    path_mode = conf['path_mode']
    max_cases = conf['count']
    old_archive = conf['old_archive']
    overwrite = conf['overwrite']
    no_write = conf['no_write']
    dedupe = conf['dedupe']
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")



    batches = pd.Series(np.array_split(queue, math.ceil(max_cases / 500)))
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            if path_mode:
                allpagestext = pd.Series(c).map(lambda x: get.PDFText(x))
            else:
                allpagestext = c

            case_number = allpagestext.map(lambda x: get.CaseNumber(x))

            outputs = pd.DataFrame({
                'Path': queue if path_mode else np.nan,
                'AllPagesText': allpagestext,
                'Timestamp': start_time,
                'CaseNumber': case_number
                })

            if dedupe == True:
                outputs.drop_duplicates('CaseNumber',keep='first',inplace=True)

            if isinstance(old_archive, pd.core.frame.DataFrame):
                try:
                    outputs = old_archive.append(outputs)
                except:
                    outputs = [old_archive, outputs]
        outputs.fillna('',inplace=True)
    try:
        if dedupe == True and outputs.shape[0] < queue.shape[0]:
            click.echo(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
    except:
        pass


    if not no_write:
        now(conf, outputs, archive=True)
    log_complete(conf, start_time, outputs)
    return outputs
