"""
alac 78
"""

import warnings
warnings.filterwarnings('ignore')
import fitz
import glob
import inspect
import math
import os
import re
import sys
import datetime
import time
import click
import numpy as np
import pandas as pd
import selenium
from tqdm.auto import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option('display.expand_frame_repr', False) 
pd.set_option('display.min_rows', 50)
pd.set_option('compute.use_bottleneck', True)
pd.set_option('compute.use_numexpr', True)
pd.set_option('display.max_categories', 16)
pd.set_option('display.precision',2)


tqdm.pandas()


## CONFIG

def append_archive(in_path, out_path, no_write=False, obj=False):
   if not obj:
         input_archive = read(in_path)
         output_archive = read(out_path)
         new_archive = pd.concat([output_archive, input_archive], ignore_index=True)
         new_archive = new_archive.dropna()
         if not no_write:
            cin = setinputs(input_archive)
            cout = setoutputs(out_path)
            conf = set(cin, cout)
            write(conf, new_archive)
         return new_archive
   else: # object in_path
      output_archive = read(out_path)
      new_archive = pd.concat([output_archive, in_path], ignore_index = True)
      return new_archive


def read(path, log=True):
   if os.path.isdir(path):
      pdfpaths = pd.Series(glob.glob(path + '**/*.pdf', recursive=True))
      if log:
         tqdm.pandas(desc="PDF=>Text")
         pdftexts = pdfpaths.progress_map(lambda x: getPDFText(x))
      else:
         pdftexts = pdfpaths.map(lambda x: getPDFText(x))
      archive = pd.DataFrame({
         'Timestamp': time.time(),
         'AllPagesText': pdftexts,
         'Path': pdfpaths
         })
      archive.AllPagesText = archive.AllPagesText.astype("string")
      assert len(pdfpaths) > 0
      return archive
   else:
      ext = os.path.splitext(path)[1]
      nzext = os.path.splitext(path.replace(".zip","").replace(".xz",""))[1]
      if nzext == ".pkl" and ext == ".xz":
         archive = pd.read_pickle(path, compression="xz")
      if nzext == ".pkl" and ext == ".pkl":
         archive = pd.read_pickle(path)
      elif nzext == ".json" and ext == ".zip":
         archive = pd.read_json(path, orient='table', compression="zip")
      elif nzext == ".json" and ext == ".json":
         archive = pd.read_json(path, orient='table')
      elif nzext == ".csv" and ext == ".zip":
         archive = pd.read_csv(path, compression="zip")
      elif nzext == ".csv" and ext == ".csv":
         archive = pd.read_csv(path, compression="zip")
      elif nzext == ".parquet" and ext == ".zip":
         archive = pd.read_parquet(path,compression="zip")
      elif nzext == ".parquet" and ext == ".parquet":
         archive = pd.read_parquet(path)
      assert "AllPagesText" in archive.columns
      return archive

def setinputs(path, debug=False, fetch=False):
   """Verify and configure input path. Must use set() to finish configuration even if NO_WRITE mode. Call setoutputs() with no arguments.  
   
   Args:
      path (str): Path to PDF directory, compressed archive, or query template sheet,
      debug (bool, optional): Print detailed logs,
      fetch (bool, optional): Configure template sheet for web PDF retrieval 
   
   Returns:
      inp = pd.Series({
         INPUT_PATH: (path-like obj) path to input file or directory,
         IS_FULL_TEXT: (bool) origin is case text (False = PDF directory or query template),
         QUEUE: (list) paths or case texts (dep. on IS_FULL_TEXT) for export function,
         FOUND: (int) total cases found in input path,
         GOOD: (bool) configuration succeeded,
         PICKLE: (pd.DataFrame) original archive file (if appl.),
         ECHO: (IFrame(str)) log data for console 
      })
   """
   if fetch == True and isinstance(path, str) and not isinstance(path, pd.core.frame.DataFrame) and not isinstance(path, pd.core.series.Series):
      if fetch == True or (os.path.splitext(path)[1] in [".xlsx",".xls",".csv",".json"]):
         queue = readPartySearchQuery(path)
         out = pd.Series({
            'INPUT_PATH': path,
            'IS_FULL_TEXT': False,
            'QUEUE': queue,
            'FOUND': 0,
            'GOOD': True,
            'PICKLE': '',
            'ECHO': ''
         })
         return out
   else:
      found = 0
      is_full_text = False
      good = False
      pickle = None
      if not debug:
         warnings.filterwarnings('ignore')

      if isinstance(path, pd.core.frame.DataFrame) or isinstance(path, pd.core.series.Series):
         if "AllPagesText" in path.columns and path.shape[0] > 0:
            queue = path['AllPagesText']
            is_full_text = True
            found = len(queue)
            good = True
            pickle = path
            path = "NONE"

      elif isinstance(path, str) and path != "NONE":
         queue = pd.Series()
         if os.path.isdir(path):  # if PDF directory -> good
            queue = pd.Series(glob.glob(path + '**/*.pdf', recursive=True))
            if queue.shape[0] > 0:
               found = len(queue)
               good = True
         elif os.path.isfile(path) and os.path.splitext(path)[1] == ".xz": 
            good = True
            pickle = pd.read_pickle(path, compression="xz")
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
         elif os.path.isfile(path) and (os.path.splitext(path)[1] == ".zip"):
            nzpath = path.replace(".zip","")
            nozipext = os.path.splitext(nzpath)[1]
            if debug:
               click.echo(f"NZPATH: {nozipext}, NOZIPEXT: {nozipext}, PATH: {path}")
            if nozipext == ".json":
               pickle = pd.read_json(path, orient='table',compression="zip")
               queue = pickle['AllPagesText']
               is_full_text = True
               found = len(queue)
               good = True
            if nozipext == ".csv":
               pickle = pd.read_csv(path, escapechar='\\',compression="zip")
               queue = pickle['AllPagesText']
               is_full_text = True
               good = True
               found = len(queue)
            if nozipext == ".parquet":
               pickle = pd.read_parquet(path,compression="zip")
               queue = pickle['AllPagesText']
               is_full_text = True
               found = len(queue)
               good = True
            if nozipext == ".pkl":
               pickle = pd.read_pickle(path,compression="zip")
               queue = pickle['AllPagesText']
               is_full_text = True
               found = len(queue)
               good = True
         elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            try:
               pickle = pd.read_json(path, orient='table')
            except:
               pickle = pd.read_json(path, orient='table',compression="zip")
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
            good = True
         elif os.path.isfile(path) and os.path.splitext(path)[1] == ".csv":
            pickle = pd.read_csv(path, escapechar='\\')
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
            good = True
         elif os.path.isfile(path) and os.path.splitext(path)[1] == ".pkl":
            pickle = pd.read_pickle(path)
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
            good = True
         elif os.path.isfile(path) and os.path.splitext(path)[1] == ".parquet":
            pickle = pd.read_parquet(path)
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
            good = True
         else:
            good = False
      else:
         good = False

      if good:
         echo = f"Found {found} cases in input."
      else:
         echo = "Alacorder failed to configure input! Try again with a valid PDF directory or full text archive path, or run 'python3 -m alacorder --help' in command line for more details."
      out = pd.Series({
         'INPUT_PATH': path,
         'IS_FULL_TEXT': is_full_text,
         'QUEUE': pd.Series(queue),
         'FOUND': found,
         'GOOD': good,
         'PICKLE': pickle,
         'ECHO': echo
      })
      return out

def setoutputs(path="", debug=False, archive=False, table="", fetch=False):
   """Verify and configure output path. Must use set(inconf, outconf) to finish configuration.

   Args:
      path (str): Path to PDF directory, compressed archive, or query template sheet,
      debug (bool, optional): Print detailed logs,
      archive (bool, optional): Create full text archive,
      table (str, optional): Create table ('cases', 'fees', 'charges', 'filing', 'disposition') 

   Returns:
   out = pd.Series({
      'OUTPUT_PATH': (path-like obj) path to output file or directory,
      'ZIP_OUTPUT_PATH': (path-like obj) path to output file or directory with .zip if zip compression enabled,
      'OUTPUT_EXT': (str) output file extension,
      'MAKE': (str) table, archive, or directory to be made at init(),
      'GOOD': (bool) configuration succeeded,
      'EXISTING_FILE': (bool) existing file at output path,
      'ECHO': (IFrame(str)) log data 
   )}
   """
   good = False
   make = ""
   compress = False
   exists = False
   ext = ""
   if not debug:
      warnings.filterwarnings('ignore')

   if fetch:
      if os.path.isdir(path):  # if PDF directory -> good
         make = "pdf_directory"
         good = True
      else:
         good = False
   else:
      if ".zip" in path or ".xz" in path:
         compress=True
      
      nzpath = path.replace(".zip","")

      # if no output -> set default
      if path == "" and archive == False:
         path = "NONE"
         ext = "NONE"
         make == "multiexport" if table != "cases" and table != "charges" and table != "fees" and table != "disposition" and table != "filing" else "singletable"
         good = True
         exists = False
      if path == "" and archive == True:
         path = "NONE"
         ext = "NONE"
         make == "archive"
         good = True
         exists = False

      # if path
      if isinstance(path, str) and path != "NONE" and make != "pdf_directory":
         exists = os.path.isfile(path)
         ext = os.path.splitext(path)[1]
         if ext == ".zip":  # if vague due to compression, assume archive
            ext = os.path.splitext(os.path.splitext(path)[0])[1]
            compress = True
            good = True

         if ext == ".xz" or ext == ".parquet" or ext == ".pkl":  # if output is existing archive
            make = "archive"
            compress = True
            good = True
         elif ext == ".xlsx" or ext == ".xls":  # if output is multiexport
            make = "multiexport"
            good = True
         elif archive == False and (ext == ".csv" or ext == ".dta" or ext == ".json" or ext == ".txt"):
            make = "singletable"
            good = True
         elif archive == True and (ext == ".csv" or ext == ".dta" or ext == ".json" or ext == ".txt"):
            make = "archive"
            good = True

   if good and not debug:
      echo = "Successfully configured output."
   if good and debug:
      echo = "Output path is valid. Call set() to finish configuration."

   out = pd.Series({
      'OUTPUT_PATH': nzpath,
      'ZIP_OUTPUT_PATH': path,
      'OUTPUT_EXT': ext,
      'MAKE': make,
      'GOOD': good,
      'EXISTING_FILE': exists,
      'COMPRESS': compress,
      'ECHO': echo
   })
   return out

def set(inputs, outputs=None, count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="", fetch_uID="", fetch_pwd="", fetch_qmax=0, fetch_qskip=0, fetch_speed=1, archive=False, append=False):
   """Verify and configure task from setinputs() and setoutputs() configuration objects and **kwargs. Must call init() or export function to begin task. 
   DO NOT USE TO CALL ALAC.FETCH() OR OTHER BROWSER-DEPENDENT METHODS. 
   
   Args:
      inputs (obj): configuration object from setinputs(),
      outputs (None, optional): configuration object from setoutputs(),
      count (int, optional): (int) total cases in queue,
      table (str, optional): table export setting,  
      overwrite (bool, optional): overwrite without prompting, 
      log (bool, optional): print logs to console,
      dedupe (bool, optional): remove duplicates from archive export,
      no_write (bool, optional): don't write to output file,
      no_prompt (bool, optional): don't prompt user for input,
      debug (bool, optional): print detailed logs,
      no_batch (bool, optional): don't split task into batches,
      compress (bool, optional): compress output file (Excel files not supported)
   
   Returns:
      
   out = pd.Series({
      'GOOD': (bool) configuration succeeded,
      'ECHO':  (IFrame(str)) log data,
      'TIME': timestamp at configuration,

      'QUEUE': (list) paths or case texts to process,
      'COUNT': (int) total in queue,
      'IS_FULL_TEXT': (bool) origin is case text (False = PDF directory or query template),
      'MAKE': (str) table, archive, or directory to be made at init(),
      'TABLE': Table export selection if appl. ('cases', 'fees', 'charges', 'filing', 'disposition')

      'INPUT_PATH': (path-like obj) path to input file or directory,
      'OUTPUT_PATH': (path-like obj) path to output file or directory,
      'OUTPUT_EXT': (str) output file extension,

      'OVERWRITE': (bool) existing file at output path will be overwritten,
      'FOUND': (int) cases found in inputs,

      'DEDUPE': (bool) remove duplicate cases from exported archives
      'LOG': (bool) print logs to console,
      'DEBUG': (bool) print detailed logs,
      'NO_PROMPT': (bool) don't prompt user for input,
      'NO_WRITE': (bool) don't write file to output path,
      'NO_BATCH': (bool) don't split task into batches,
      'COMPRESS': (bool) compress output if supported 

      'FETCH': fetch,
      'ALA_CUSTOMER_ID': fetch_cID,
      'ALA_USER_ID': fetch_uID,
      'ALA_PASSWORD': fetch_pwd
   })

   """

   echo = ""
   will_overwrite = False
   good = True

   if append:
      overwrite = True

   # DEDUPE
   content_len = len(inputs.QUEUE)
   if dedupe and not fetch:
      queue = inputs.QUEUE.drop_duplicates()
      dif = content_len - queue.shape[0]
      if (log or debug) and dif > 0:
         click.secho(f"Removed {dif} duplicate cases from queue.", italic=True)
   else:
      queue = inputs.QUEUE


   # COUNT
   content_len = inputs['FOUND']
   if content_len > count and count != 0:
      ind = count - 1
      queue = inputs.QUEUE[0:ind]
   elif count > content_len and content_len > 0:
      count = inputs.QUEUE.shape[0]
   elif count < content_len and count == 0:
      count = content_len
   else:
      queue = inputs.QUEUE

   count += 1

   echo = echo_conf(inputs.INPUT_PATH, outputs.MAKE, outputs.OUTPUT_PATH, overwrite, no_write, dedupe, no_prompt, compress)

   if outputs.COMPRESS == True:
      compress = True

   cftime = time.time()

   if archive:
      make = "archive"
   else:
      make = outputs.MAKE 

   out = pd.Series({
      'GOOD': good,
      'ECHO': echo,
      'TIME': cftime,

      'QUEUE': queue,
      'COUNT': count,
      'IS_FULL_TEXT': bool(inputs.IS_FULL_TEXT),
      'MAKE': make,
      'TABLE': table,

      'INPUT_PATH': inputs.INPUT_PATH,
      'OUTPUT_PATH': outputs.OUTPUT_PATH,
      'OUTPUT_EXT': outputs.OUTPUT_EXT,

      'OVERWRITE': will_overwrite,
      'APPEND': append,
      'FOUND': inputs.FOUND,

      'DEDUPE': dedupe,
      'LOG': log,
      'DEBUG': debug,
      'NO_PROMPT': no_prompt,
      'NO_WRITE': no_write,
      'NO_BATCH': no_batch,
      'COMPRESS': compress,

      'FETCH': fetch,
      'ALA_CUSTOMER_ID': fetch_cID,
      'ALA_USER_ID': fetch_uID,
      'ALA_PASSWORD': fetch_pwd
   })

   return out

def setpaths(input_path, output_path=None, count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="", fetch_uID="", fetch_pwd="", fetch_qmax="", fetch_qskip="", fetch_speed=1, archive=False, append=False): # DOC
   """Substitute paths for setinputs(), setoutputs() configuration objects for most tasks. Must call init() or export function to begin task. 
   DO NOT USE TO CALL ALAC.FETCH() OR OTHER BROWSER-DEPENDENT METHODS. 
   
   Args:
      input_path (str): (path-like obj) path to input file or directory,
      output_path (None, optional): (path-like obj) path to output file or directory,
      count (int, optional): (int) total cases in queue,
      table (str, optional): table export setting,  
      overwrite (bool, optional): overwrite without prompting, 
      log (bool, optional): print logs to console,
      dedupe (bool, optional): remove duplicates from archive export,
      no_write (bool, optional): don't write to output file or directory,
      no_prompt (bool, optional): don't prompt user for input,
      debug (bool, optional): print detailed logs,
      no_batch (bool, optional): don't split task into batches,
      compress (bool, optional): compress output file (Excel files not supported)
   
   Returns:
      
   out = pd.Series({
      'GOOD': (bool) configuration succeeded,
      'ECHO':  (IFrame(str)) log data,
      'TIME': timestamp at configuration,

      'QUEUE': (list) paths or case texts to process,
      'COUNT': (int) total in queue,
      'IS_FULL_TEXT': (bool) origin is case text (False = PDF directory or query template),
      'MAKE': (str) table, archive, or directory to be made at init(),
      'TABLE': Table export selection if appl. ('cases', 'fees', 'charges', 'filing', 'disposition')

      'INPUT_PATH': (path-like obj) path to input file or directory,
      'OUTPUT_PATH': (path-like obj) path to output file or directory,
      'OUTPUT_EXT': (str) output file extension,

      'OVERWRITE': (bool) existing file at output path will be overwritten,
      'FOUND': (int) cases found in inputs,

      'DEDUPE': (bool) remove duplicate cases from exported archives
      'LOG': (bool) print logs to console,
      'DEBUG': (bool) print detailed logs,
      'NO_PROMPT': (bool) don't prompt user for input,
      'NO_WRITE': (bool) don't write file to output path,
      'NO_BATCH': (bool) don't split task into batches,
      'COMPRESS': (bool) compress output if supported,
   })

   """

   a = setinputs(input_path, fetch=fetch)
   if log:
      click.secho(a.ECHO)
   b = setoutputs(output_path, fetch=fetch)
   if b.MAKE == "archive": #
      compress = True
   c = set(a, b, count=count, table=table, overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, debug=debug, no_batch=no_batch, compress=compress, fetch=fetch, fetch_cID=fetch_cID, fetch_uID=fetch_uID, fetch_pwd=fetch_pwd, fetch_qmax=fetch_qmax, fetch_qskip=fetch_qskip, fetch_speed=fetch_speed, archive=archive, append=append)
   if log:
      click.secho(c.ECHO)
   return c

def setinit(input_path, output_path=None, archive=False,count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="",fetch_uID="", fetch_pwd="", fetch_qmax=0, fetch_qskip=0, fetch_speed=1, append=False): # DOC
   """
   Initialize tasks from paths without calling setinputs(), setoutputs(), or set().
   Note additional fetch flags for auth info if task involves alac.fetch()
   
   Args:
      input_path (str): (path-like obj) path to input file or directory,
      output_path (None, optional): (path-like obj) path to output file or directory,
      archive (bool, optional): make compressed archive,
      count (int, optional): (int) total cases in queue,
      table (str, optional): table export setting,  
      overwrite (bool, optional): overwrite without prompting, 
      log (bool, optional): print logs to console,
      dedupe (bool, optional): remove duplicates from archive export,
      no_write (bool, optional): don't write to output file or directory,
      no_prompt (bool, optional): don't prompt user for input,
      debug (bool, optional): print detailed logs,
      no_batch (bool, optional): don't split task into batches,
      compress (bool, optional): compress output file (Excel files not supported)
      fetch_cID (str): Alacourt.com Customer ID
      fetch_uID (str): Alacourt.com User ID
      fetch_pwd (str): Alacourt.com Password
      fetch_qmax (int, optional): Max queries to pull from inputs
      fetch_qskip (int, optional): Skip top n queries in inputs
      fetch_speed (int, optional): Fetch rate multiplier

   Returns: [out, init_out]
      
   out = pd.Series({
      'GOOD': (bool) configuration succeeded,
      'ECHO':  (IFrame(str)) log data,
      'TIME': timestamp at configuration,

      'QUEUE': (list) paths or case texts to process,
      'COUNT': (int) total in queue,
      'IS_FULL_TEXT': (bool) origin is case text (False = PDF directory or query template),
      'MAKE': (str) table, archive, or directory to be made at init(),
      'TABLE': Table export selection if appl. ('cases', 'fees', 'charges', 'filing', 'disposition')

      'INPUT_PATH': (path-like obj) path to input file or directory,
      'OUTPUT_PATH': (path-like obj) path to output file or directory,
      'OUTPUT_EXT': (str) output file extension,

      'OVERWRITE': (bool) existing file at output path will be overwritten,
      'FOUND': (int) cases found in inputs,

      'DEDUPE': (bool) remove duplicate cases from exported archives
      'LOG': (bool) print logs to console,
      'DEBUG': (bool) print detailed logs,
      'NO_PROMPT': (bool) don't prompt user for input,
      'NO_WRITE': (bool) don't write file to output path,
      'NO_BATCH': (bool) don't split task into batches,
      'COMPRESS': (bool) compress output if supported 
   })

   init_out = pd.DataFrame() # depends on init() configuration

   """
   
   if fetch:
      fetch_no_log = not log
      if not isinstance(input_path, pd.core.series.Series) and not isinstance(output_path, pd.core.series.Series):
         fetch(input_path, output_path, fetch_cID, fetch_uID, fetch_pwd, fetch_qmax, fetch_qskip, fetch_speed, fetch_no_log)
      else:
         input_path = setinputs(input_path)
         output_path = setoutputs(output_path)
         fetch(input_path, output_path, fetch_cID, fetch_uID, fetch_pwd, fetch_qmax, fetch_qskip, fetch_speed, fetch_no_log)
   else:
      if not isinstance(input_path, pd.core.series.Series) and input_path != None:
         input_path = setinputs(input_path)

      if not isinstance(output_path, pd.core.series.Series) and output_path != None:
         output_path = setoutputs(output_path)

      a = set(input_path, output_path, count=count, table=table, overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt,debug=debug, no_batch=no_batch, compress=compress, archive=archive, append=append)
      
      if archive == True:
         a.MAKE = "archive"
      
      b = init(a)

      return b


## CORE PARSE FUNCTIONS

def write(conf, outputs):
   """
   Writes (outputs) to file at (conf.OUTPUT_PATH)

   Args:
      conf (pd.Series): Configuration object with paths and settings
      outputs (pd.Series|pd.DataFrame): Description
   Returns:
      outputs: DataFrame written to file at conf.OUTPUT_PATH
      DataFrame
   """

   if conf.OUTPUT_EXT == ".xls":
      try:
         with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
            outputs.to_excel(writer, sheet_name="outputs", engine="openpyxl")
      except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
         try:
            with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
               outputs.to_excel(writer, sheet_name="outputs")
         except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            outputs.to_json(os.path.splitext(conf.OUTPUT_PATH)[
                            0] + "-cases.json.zip", orient='table')
            click.echo(conf, f"Fallback export to {os.path.splitext(conf.OUTPUT_PATH)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
   if conf.OUTPUT_EXT == ".xlsx":
      try:
         with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
            outputs.to_excel(writer, sheet_name="outputs", engine="openpyxl")
      except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
         try:
            with pd.ExcelWriter(conf.OUTPUT_PATH[0:-1]) as writer:
               outputs.to_excel(writer, sheet_name="outputs", engine="xlsxwriter")
         except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            outputs.to_json(os.path.splitext(conf.OUTPUT_PATH)[
                            0] + ".json.zip", orient='table', compression="zip")
            click.echo(conf, f"Fallback export to {os.path.splitext(conf.OUTPUT_PATH)}.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
   elif conf.OUTPUT_EXT == ".pkl":
      if conf.COMPRESS:
         outputs.to_pickle(conf.OUTPUT_PATH + ".xz", compression="xz")
      else:
         outputs.to_pickle(conf.OUTPUT_PATH)
   elif conf.OUTPUT_EXT == ".xz":
      outputs.to_pickle(conf.OUTPUT_PATH, compression="xz")
   elif conf.OUTPUT_EXT == ".json":
      if conf.COMPRESS:
         outputs.to_json(conf.OUTPUT_PATH + ".zip",
                         orient='table', compression="zip")
      else:
         outputs.to_json(conf.OUTPUT_PATH, orient='table')
   elif conf.OUTPUT_EXT == ".csv":
      if conf.COMPRESS:
         outputs.to_csv(conf.OUTPUT_PATH + ".zip",
                        escapechar='\\', compression="zip")
      else:
         outputs.to_csv(conf.OUTPUT_PATH, escapechar='\\')
   elif conf.OUTPUT_EXT == ".txt":
      outputs.to_string(conf.OUTPUT_PATH)
   elif conf.OUTPUT_EXT == ".dta":
      outputs.to_stata(conf.OUTPUT_PATH)
   elif conf.OUTPUT_EXT == ".parquet":
      if conf.COMPRESS:
         outputs.to_parquet(conf.OUTPUT_PATH, compression="brotli")
      else:
         outputs.to_parquet(conf.OUTPUT_PATH)
   else:
      pass
   return outputs

def archive(conf):
   """
   Write full text archive to file.pkl.xz

   Args:
      conf (pd.Series): Configuration object with paths and settings

   Returns:
      DataFrame (written to file at conf.OUTPUT_PATH)
   """
   start_time = time.time()

   if conf.LOG or conf['DEBUG']:
      click.echo("Writing full text archive from cases...")

   if not conf.IS_FULL_TEXT:
      allpagestext = pd.Series(conf.QUEUE).progress_map(lambda x: getPDFText(x))
   else:
      allpagestext = pd.Series(conf.QUEUE)

   if (conf.LOG or conf['DEBUG']) and conf.IS_FULL_TEXT == False:
      click.echo("Exporting archive to file at output path...")

   outputs = pd.DataFrame({
      'Path': conf.QUEUE if not conf.IS_FULL_TEXT else np.nan,
      'AllPagesText': allpagestext,
      'Timestamp': start_time,
   })

   outputs.fillna('', inplace=True)
   outputs = outputs.convert_dtypes()

   if conf.DEDUPE:
      old = conf.QUEUE.shape[0]
      outputs = outputs.drop_duplicates()
      dif = outputs.shape[0] - old
      if dif > 0 and conf.LOG:
         click.echo(f"Removed {dif} duplicate cases from queue.")

   if conf.APPEND == True:
      if conf.LOG:
         click.echo(f"Appending archive to existing archive at output path...")
         outputs = append_archive(outputs, conf.OUTPUT_PATH, obj=True)

   if not conf.NO_WRITE and conf.OUTPUT_EXT == ".xz":
      outputs.to_pickle(conf.OUTPUT_PATH, compression="xz")
   if not conf.NO_WRITE and conf.OUTPUT_EXT == ".pkl":
      if conf.COMPRESS:
         outputs.to_pickle(conf.OUTPUT_PATH + ".xz", compression="xz")
      else:
         outputs.to_pickle(conf.OUTPUT_PATH)
   if not conf.NO_WRITE and conf.OUTPUT_EXT == ".csv":
      if conf.COMPRESS:
         outputs.to_csv(conf.OUTPUT_PATH + ".zip",
                        escapechar='\\', compression="zip")
      else:
         outputs.to_csv(conf.OUTPUT_PATH, escapechar='\\')
   if not conf.NO_WRITE and conf.OUTPUT_EXT == ".parquet":
      if conf.COMPRESS:
         outputs.to_parquet(conf.OUTPUT_PATH + ".parquet", compression="brotli")
      else:
         outputs.to_parquet(conf.OUTPUT_PATH + ".parquet", compression="brotli")
   if not conf.NO_WRITE and conf.OUTPUT_EXT == ".json":
      if conf.COMPRESS:
         outputs.to_json(conf.OUTPUT_PATH + ".zip",
                         orient='table', compression="zip")
      else:
         outputs.to_json(conf.OUTPUT_PATH, orient='table')
   complete(conf, outputs)
   return outputs

def map(conf, *args, bar=True, names=[]):
   """
   Return DataFrame from config object and custom column 'getter' functions like below:

      def getter(full_case_text: str):
         out = re.search(...)
         ...
         return out
   
   Creates DataFrame with cols: CaseNumber, getter_1(), getter_2(), ...
   Getter functions must take case text as first parameter. Subsequent paramters can be set in map() after the getter parameter. Getter functions must return string, float, or int outputs to map().

   Example:
      >>  a = alac.map(conf,
                   alac.getAmtDueByCode, 'D999', 
                   alac.getAmtPaidByCode, 'D999', 
                   alac.getName, 
                   alac.getDOB)
      >>  print(a)

   Args:
      conf (pd.Series): Configuration object with paths and settings

      *args:  def getter(text: str) -> float, 
            def getter(text: str) -> int,
            def getter(text: str) -> str,
            def getter(text: str) -> bool, # check / debug

   
   Returns:
      out = pd.DataFrame({
            'CaseNumber': (str) full case number with county,
            'getter_1': (float) outputs of getter_1(),
            'getter_2': (int) outputs of getter_2(),
            'getter_3': (str) outputs of getter_2() 
         })
   
   """
   start_time = time.time()
   df_out = pd.DataFrame()
   temp_no_write_tab = False

   if conf.DEDUPE: # remove duplicates from queue
      old = conf.QUEUE.shape[0]
      conf.QUEUE = conf.QUEUE.drop_duplicates()
      dif = conf.QUEUE.shape[0] - old
      if dif > 0 and conf.LOG:
         click.secho(f"Removed {dif} duplicate cases from queue.", italic=True)

   if not conf.NO_BATCH: # split into batches
      batches = batcher(conf)
   else:
      batches = [conf.QUEUE]

   # sort args into functions and their parameters
   func = pd.Series(args).map(lambda x: 1 if inspect.isfunction(x) else 0)
   funcs = func.index.map(lambda x: args[x] if func[x] > 0 else np.nan)
   no_funcs = func.index.map(lambda x: args[x] if func[x] == 0 else np.nan)
   countfunc = func.sum()
   column_getters = pd.DataFrame(columns=['Name', 'Method', 'Arguments'], index=(range(0, countfunc)))

   # call methods, return outputs with pandas-friendly dtype
   def ExceptionWrapper(getter, text, *args):
      if args:
         outputs = pd.Series(getter(text, args))
      else:
         outputs = pd.Series(getter(text))
      return outputs.values

   # set name of methods to name w/o "get", i.e. getName() -> 'Name' column in df_out
   for i, x in enumerate(funcs):
      if inspect.isfunction(x):
         try:
            if len(names)>=i:
               column_getters.Name[i] = names[i]
            else:
               column_getters.Name[i] = str(x.__name__).replace("get","").upper()
         except:
            column_getters.Name[i] = str(x.__name__).replace("get","").upper()
         column_getters.Method[i] = x

   for i, x in enumerate(args):
      if not inspect.isfunction(x):
         column_getters.Arguments[i] = x

   # run batch
   for i, b in enumerate(batches):
      if i > 0:
         click.echo(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
      b = pd.DataFrame()

      # stop slow writes on big files between batches
      if bool(conf.OUTPUT_PATH) and i > 0 and not conf.NO_WRITE:
         if os.path.getsize(conf.OUTPUT_PATH) > 500: 
            temp_no_write_tab = True
      if i == len(conf.QUEUE) - 1:
         temp_no_write_tab = False

      # get text
      if conf.IS_FULL_TEXT:
         allpagestext = conf.QUEUE
      else:
         if bar:
            tqdm.pandas(desc="PDF => Text")
            allpagestext = pd.Series(conf.QUEUE).progress_map(lambda x: getPDFText(x))
         else:
            allpagestext = pd.Series(conf.QUEUE).map(lambda x: getPDFText(x))

      # retrieve getter
      for i in column_getters.index:
         name = column_getters.Name[i]
         arg = column_getters.Arguments[i]
         getter = column_getters.Method[i]

      # map getter 
      for i, getter in enumerate(column_getters.Method.tolist()):
         arg = column_getters.Arguments[i]
         name = column_getters.Name[i]
         if bar and name != "CaseNumber":
            if arg == pd.NaT: 
               tqdm.pandas(desc=name)
               col = allpagestext.progress_map(lambda x: getter(x, arg))
            else: 
               tqdm.pandas(desc=name)
               col = allpagestext.progress_map(lambda x: getter(x))
         else:
            if arg == pd.NaT: 
               col = allpagestext.map(lambda x: getter(x, arg))
            else: 
               col = allpagestext.map(lambda x: getter(x))
         new_df_to_concat = pd.DataFrame({name: col})
         df_out = pd.concat([df_out, new_df_to_concat], axis=1)
         df_out = df_out.dropna(axis=1)
         df_out = df_out.dropna(axis=0)
         df_out = df_out.convert_dtypes()

      # fix empty -> str error
      for col in column_getters.columns:
         column_getters[col] = column_getters[col].dropna()
         column_getters[col] = column_getters[col].map(lambda x: "" if x == "Series([], Name: AmtDue, dtype: float64)" or x == "Series([], Name: AmtDue, dtype: object)" else x)
      # write
      if conf.NO_WRITE == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(conf.QUEUE) - 1):
         write(conf, df_out)  

   if not conf.NO_WRITE:
      return df_out
   write(conf, df_out)
   return df_out

def stack(dflist, *old_df):
      try:
         dflist = dflist.dropna()
      except:
         pass
      try:
         dflist = dflist.tolist()  # -> [df, df, df]
      except:
         pass
      dfliststack = pd.concat(dflist, axis=0, ignore_index=True)
      if not old_df:
         return dfliststack
      else:
         out = pd.concat([old_df, dfliststack], axis=0,ignore_index=True)
         out = out.dropna()
         out = out.fillna('', inplace=True)
         return out

def table(conf):
   """
   Route config to export function corresponding to conf.TABLE

   Args:
      conf (pd.Series): Configuration object with paths and settings
   Returns:
      DataFrame written to file at conf.OUTPUT_PATH
      DataFrame
   """
   a = []

   if conf.MAKE == "multiexport":
      a = cases(conf)
   elif conf.TABLE == "cases":
      a = cases(conf)
   elif conf.TABLE == "fees":
      a = fees(conf)
   elif conf.TABLE == "charges":
      a = charges(conf)
   elif conf.TABLE == "disposition":
      a = charges(conf)
   elif conf.TABLE == "filing":
      a = charges(conf)
   else:
      a = None
   return a

def init(conf):
   """
   Start export function corresponding to conf.MAKE, conf.TABLE
   
   Args:
      conf (pd.Series): Configuration object with paths and settings
   
   Returns:
      DataFrame written to file at conf.OUTPUT_PATH
      DataFrame
   """
   a = []
   if conf.FETCH == True:
      fetch(conf.INPUT_PATH, conf.OUTPUT_PATH, fetch_cID=conf.ALA_CUSTOMER_ID, fetch_uID=conf.ALA_USER_ID, fetch_pwd=conf.ALA_PASSWORD, fetch_qmax=conf.FETCH_QMAX, fetch_qskip=conf.FETCH_QSKIP,fetch_speed=conf.FETCH_SPEED)
   elif conf.MAKE == "multiexport" and (conf.TABLE == "" or conf.TABLE == "all"):
      a = cases(conf)
   elif conf.MAKE == "archive":
      a = archive(conf)
   elif conf.TABLE == "cases":
      a = cases(conf)
   elif conf.TABLE == "fees":
      a = fees(conf)
   elif conf.TABLE == "charges":
      a = charges(conf)
   elif conf.TABLE == "disposition":
      a = charges(conf)
   elif conf.TABLE == "filing":
      a = charges(conf)
   else:
      a = None
   return a

def batcher(conf, queue=pd.Series()):
   """Splits conf.QUEUE objects into batches
   
   Args:
      conf (pd.Series): Configuration object with paths and settings
   
   Returns:
      batches: (numpy.array) list of pd.Series()
   """
   if queue.shape[0] == 0:
      q = conf['QUEUE']
   else:
      q = queue
   if not conf.IS_FULL_TEXT:
      if conf.FOUND < 1000:
         batchsize = 250
      elif conf.FOUND > 10000:
         batchsize = 2500
      else:
         batchsize = 1000
      batches = np.array_split(q, 3)
   else:
      batches = np.array_split(q, 1)
   return batches


## TABLE PARSERS

def cases(conf):
   """
   Return [cases, fees, charges] tables as List of DataFrames from batch
   See API docs for table-specific output tokens

   Args:
      conf (pd.Series): Configuration object with paths and settings

   Returns:
      list = [cases, fees, charges]:
         out[0] = cases table (see alac.caseinfo().__str__ for outputs)
         out[1] = fees table (see alac.fees().__str__ for outputs)
         out[2] = charges table (see alac.charges().__str__ for outputs)
   """

   arch = pd.DataFrame()
   cases = pd.DataFrame()
   fees = pd.DataFrame()
   allcharges = pd.DataFrame()

   start_time = time.time()
   temp_no_write_arc = False
   temp_no_write_tab = False

   if conf.DEDUPE:
      old = conf.QUEUE.shape[0]
      conf.QUEUE = conf.QUEUE.drop_duplicates()
      dif = conf.QUEUE.shape[0] - old
      if dif > 0 and conf.LOG:
         click.secho(f"Removed {dif} duplicate cases from queue.",
                      bold=True)

   queue = pd.Series(conf.QUEUE)

   if not conf.IS_FULL_TEXT:
      tqdm.pandas(desc="PDF => Text")
      queue = pd.Series(conf.QUEUE).progress_map(lambda x: getPDFText(x))
      conf.QUEUE = queue
      conf.IS_FULL_TEXT = True


   if not conf['NO_BATCH']:
      batches = batcher(conf, queue)
   else:
      batches = [pd.Series(queue)]


   for i, c in enumerate(batches):
      b = pd.DataFrame({'AllPagesText':c})
      c = pd.Series(c)
      if i > 0:
         click.echo(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
      b = pd.DataFrame()
      b['CaseInfoOutputs'] = c.map(lambda x: getCaseInfo(x))
      b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0]).astype(str)
      b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1]).astype(str)
      b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2]).astype(str)
      b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3]).astype(str)
      b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4]).astype(str)
      b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5]).astype(str)
      b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6]).astype(str)
      b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7]).astype(str)

      tqdm.pandas(desc="Charges")
      allcharges = setinit(conf, conf.OUTPUT_PATH, archive=False, table="charges", no_write=True, no_prompt=True, log=False, no_batch=True)

      tqdm.pandas(desc="Fee Sheets")
      b['FeeOutputs'] = c.progress_map(lambda x: getFeeSheet(x))
      b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
      b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
      b['PaymentToRestore'] = c.map(
          lambda x: getPaymentToRestore(x))
      b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3]).astype(str)
      b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4]).astype(str)
      b['FeeCodesOwed'] = b['FeeCodesOwed'].map(lambda x: '' if x == "nan" else x).astype(str)
      b['FeeCodes'] = b['FeeCodes'].map(lambda x: '' if x == "nan" else x).astype(str)
      b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])

      feesheet = b['FeeOutputs'].map(lambda x: x[6])
      feesheet = feesheet.dropna()
      feesheet = feesheet.fillna('')
      feesheet = feesheet.tolist()  # -> [df, df, df]
      feesheet = pd.concat(feesheet, axis=0, ignore_index=True)  # -> batch df
      fees = pd.concat([fees, feesheet],axis=0, ignore_index=True)
      allcharges = allcharges.dropna()


      if bool(conf.OUTPUT_PATH) and i > 0 and not conf.NO_WRITE:
         if os.path.getsize(conf.OUTPUT_PATH) > 1000:
            temp_no_write_arc = True
      if bool(conf.OUTPUT_PATH) and i > 0 and not conf.NO_WRITE:
         if os.path.getsize(conf.OUTPUT_PATH) > 1000:
            temp_no_write_tab = True
      if i >= len(batches) - 1:
         temp_no_write_arc = False
         temp_no_write_tab = False

      if (i % 5 == 0 or i == len(batches) - 1) and not conf.NO_WRITE and temp_no_write_arc == False:
         if bool(conf.OUTPUT_PATH) and len(conf.OUTPUT_EXT) > 2:
            q = pd.Series(conf.QUEUE) if conf.IS_FULL_TEXT == False else pd.NaT
            ar = pd.DataFrame({
               'Path': q,
               'AllPagesText': c,
               'Timestamp': start_time
            }, index=range(0, conf.COUNT))
            try:
               arch = pd.concat([arch, ar], ignore_index=True, axis=0)
            except:
               pass
            arch.fillna('', inplace=True)
            arch.dropna(inplace=True)
            arch.to_pickle(conf.OUTPUT_PATH, compression="xz")

      b.drop(
         columns=['CaseInfoOutputs',
             'FeeOutputs', 'FeeSheet'],
         inplace=True)
      if conf.DEDUPE:
         old = conf.QUEUE.shape[0]
         cases = cases.drop_duplicates()
         dif = cases.shape[0] - old
         if dif > 0 and conf.LOG:
            click.secho(f"Removed {dif} duplicate cases from queue.",
                        bold=True)

      if conf.LOG:
         click.secho(f"Cleaning outputs and writing file to export path...", italic=True)

      b.fillna('', inplace=True)
      cases = pd.concat([cases, b], axis=0, ignore_index=True)
      cases['TotalAmtDue'] = pd.to_numeric(cases['TotalAmtDue'], 'ignore')
      cases['TotalBalance'] = pd.to_numeric(cases['TotalBalance'], 'ignore')
      cases['PaymentToRestore'] = pd.to_numeric(cases['PaymentToRestore'], 'ignore')
      if conf.MAKE == "cases":
         write(conf, cases)
      elif not temp_no_write_tab:
         if conf.OUTPUT_EXT == ".xls":
            try:
               with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
                  cases.to_excel(writer, sheet_name="cases", engine="openpyxl")
                  fees.to_excel(writer, sheet_name="fees", engine="openpyxl")
                  allcharges.to_excel(writer, sheet_name="charges", engine="openpyxl")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
               click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
               with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
                  cases.to_excel(writer, sheet_name="cases")
                  fees.to_excel(writer, sheet_name="fees")
                  allcharges.to_excel(writer, sheet_name="charges")
         elif conf.OUTPUT_EXT == ".xlsx":
            try:
               with pd.ExcelWriter(conf.OUTPUT_PATH, engine="openpyxl") as writer:
                  cases.to_excel(writer, sheet_name="cases", engine="openpyxl")
                  fees.to_excel(writer, sheet_name="fees", engine="openpyxl")
                  allcharges.to_excel(writer, sheet_name="charges", engine="openpyxl")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
               try:
                  if conf.LOG:
                     click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
                  with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
                     cases.to_excel(writer, sheet_name="cases", engine="xlsxwriter")
                     fees.to_excel(writer, sheet_name="fees", engine="xlsxwriter")
                     allcharges.to_excel(writer, sheet_name="charges", engine="xlsxwriter")
               except (ImportError, FileNotFoundError, IndexError, ValueError, ModuleNotFoundError):
                  try:
                     cases.to_json(os.path.splitext(conf.OUTPUT_PATH)[
                                   0] + "-cases.json.zip", orient='table')
                     fees.to_json(os.path.splitext(conf.OUTPUT_PATH)[
                                  0] + "-fees.json.zip", orient='table')
                     allcharges.to_json(os.path.splitext(conf.OUTPUT_PATH)[
                                     0] + "-charges.json.zip", orient='table')
                     click.echo(f"""Fallback export to {os.path.splitext(conf.OUTPUT_PATH)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!""")
                  except (ImportError, FileNotFoundError, IndexError, ValueError):
                     click.echo("Failed to export!")
         elif conf.OUTPUT_EXT == ".json":
            if conf.COMPRESS:
               cases.to_json(conf.OUTPUT_PATH, orient='table', compression="zip")
            else:
               cases.to_json(conf.OUTPUT_PATH, orient='table')
         elif conf.OUTPUT_EXT == ".csv":
            if conf.COMPRESS:
               cases.to_csv(conf.OUTPUT_PATH, escapechar='\\', compression="zip")
            else:
               cases.to_csv(conf.OUTPUT_PATH, escapechar='\\')
         elif conf.OUTPUT_EXT == ".md":
            cases.to_markdown(conf.OUTPUT_PATH)
         elif conf.OUTPUT_EXT == ".txt":
            cases.to_string(conf.OUTPUT_PATH)
         elif conf.OUTPUT_EXT == ".dta":
            cases.to_stata(conf.OUTPUT_PATH)
         elif conf.OUTPUT_EXT == ".parquet":
            if conf.COMPRESS:
               cases.to_parquet(conf.OUTPUT_PATH, compression="brotli")
            else:
               cases.to_parquet(conf.OUTPUT_PATH)
         else:
            pd.Series([cases, fees, allcharges]).to_string(conf.OUTPUT_PATH)
      else:
         pass

   complete(conf, cases, fees, allcharges)
   return [cases, fees, allcharges]

def fees(conf):   
   """
   Return fee sheet with case number as DataFrame from batch


   Args:
      conf (pd.Series): Configuration object with paths and settings

   Returns:
      fees = pd.DataFrame({
         CaseNumber: Full case number with county number,
         Code: 4-digit fee code,
         Payor: 3-4-digit Payor code,
         AmtDue (float): Amount Due,
         AmtPaid (float): Amount Paid,
         Balance (float): Current Balance,
         AmtHold: (float): Amount Hold
      })

   """

   fees = pd.DataFrame()

   if conf.DEDUPE:
      old = conf.QUEUE.shape[0]
      conf.QUEUE = conf.QUEUE.drop_duplicates()
      dif = conf.QUEUE.shape[0] - old
      if dif > 0 and conf.LOG:
         click.secho(f"Removed {dif} duplicate cases from queue.",
                     bold=True)

   if not conf['NO_BATCH']:
      batches = batcher(conf)
   else:
      batches = [conf.QUEUE]

   for i, c in enumerate(batches):
      if i > 0:
         click.echo(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
      b = pd.DataFrame()

      if conf.IS_FULL_TEXT:
         b['AllPagesText'] = c
      else:
         tqdm.pandas(desc="PDF => Text")
         b['AllPagesText'] = c.progress_map(lambda x: getPDFText(x))
      b['CaseNumber'] = b['AllPagesText'].map(lambda x: getCaseNumber(x))
      tqdm.pandas(desc="Fee Sheets")
      b['FeeOutputs'] = b['AllPagesText'].progress_map(lambda x: getFeeSheet(x))
      feesheet = b['FeeOutputs'].map(lambda x: x[6])

      feesheet = feesheet.dropna()
      fees = fees.dropna()
      feesheet = feesheet.tolist()  # -> [df, df, df]
      feesheet = pd.concat(feesheet, axis=0, ignore_index=True)
      fees = pd.concat([fees, feesheet], axis=0,ignore_index=True)
      fees.fillna('', inplace=True)
      fees = fees.convert_dtypes()

   if not conf.NO_WRITE:
      write(conf, fees)

   complete(conf, fees)
   return fees

def charges(conf, multi=False):
   def cleanCat(x):
      if len(x) > 1:
         if "MISDEMEANOR" in x:
            return "MISDEMEANOR"
         elif "FELONY" in x:
            return "FELONY"
         elif "VIOLATION" in x:
            return "VIOLATION"
         else:
            return x[1]
      elif len(x) == 1:
         return x[0]
      else:
         return pd.NaT
   def segmentCharge(text):
      cite_split = re.split(r'[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\({0,1}?[A-Z]{0,1}?\){0,1}?\.{0,1}?\d{0,1}?', text)
      if len(cite_split) > 1:
         return [cite_split[0][9:], cite_split[1]]
      else:
         return [text,text]

   df = map(conf, getCaseNumber, getCharges, names=['CaseNumber','Charges'])
   df = df.explode('Charges') # num :: [ch, ch] -> num :: ch, num :: ch
   df['Charges'] = df['Charges'].astype(str) # obj -> str
   
   df['Sort'] = df['Charges'].map(lambda x: str(x)[9] if len(str(x)) > 9 else '') # charge sorter slices at first char after Code: if digit -> Disposition 

   df = df.dropna() # drop pd.NaT before bool() ambiguity TypeError

   df['Disposition'] = df['Sort'].str.isdigit().astype(bool)
   df['Filing'] = df['Disposition'].map(lambda x: not x).astype(bool)
   df['Felony'] = df['Charges'].str.contains("FELONY")
   df['Conviction'] = df['Charges'].map(lambda x: "GUILTY PLEA" in x or "CONVICTED" in x)

   df['Num'] = df.Charges.str.slice(0,3)
   df['Code'] = df.Charges.str.slice(4,9)
   df['CourtActionDate'] = df['Charges'].str.findall(r'\d{1,2}/\d\d/\d\d\d\d') # -> [x]
   df['Cite'] = df['Charges'].str.findall(r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}\({0,1}[A-Z]{0,1}\){0,1}\.{0,1}\d{0,1}') # -> [x]
   df['Cite'] = df['Cite'].map(lambda x: x[0] if len(x)>0 else x).astype(str) # [x] -> x

   df = df.dropna()

   df['CourtAction'] = df['Charges'].str.findall(r'(BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)')
   df = df.explode('CourtAction')
   df = df.reset_index()
   df = df.fillna('')

   # split at cite - different parse based on filing/disposition
   df['SegmentedCharges'] = df.Charges.map(lambda x: segmentCharge(x))
   # whatever segment wasn't the description (now same for disposition and filing)
   # try:
   # except:
    #  pass

   df['Description'] = df.index.map(lambda x: (df['SegmentedCharges'].iloc[x])[0] if not df['Disposition'].iloc[x] else (df['SegmentedCharges'].iloc[x])[1]).astype("string")
   df['Description'] = df['Description'].str.strip()
   df['OtherSegment'] = df.index.map(lambda x: (df['SegmentedCharges'].iloc[x])[0] if df['Disposition'].iloc[x] else (df['SegmentedCharges'].iloc[x])[1])
   df['Category'] = df['OtherSegment'].str.findall(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)')
   df['TypeDescription'] = df['OtherSegment'].str.findall(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)')

   # VRR
   df['A_S_C_NON_DISQ'] = df['Description'].str.contains(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)')
   df['CERV_MATCH'] = df['Code'].str.contains(r'(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)')
   df['PARDON_DISQ_MATCH'] = df['Code'].str.contains(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)')
   df['PERM_DISQ_MATCH'] = df['Charges'].str.contains(r'(CM\d\d|CMUR)|(CAPITAL)')
   df['CERV'] = df.index.map(
      lambda x: df['CERV_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
         x] == True).astype(bool)
   df['Pardon'] = df.index.map(
      lambda x: df['PARDON_DISQ_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
         x] == True).astype(bool)
   df['Permanent'] = df.index.map(
      lambda x: df['PERM_DISQ_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
         x] == True).astype(bool)

   # type conversions
   df['Category'] = df['Category'].map(lambda x: cleanCat(x))
   df['TypeDescription'] = df['TypeDescription'].map(lambda x: cleanCat(x))

   df = df.drop(columns=['Sort','SegmentedCharges','OtherSegment','A_S_C_NON_DISQ','PARDON_DISQ_MATCH','PERM_DISQ_MATCH','CERV_MATCH'])

   try:
      df.drop(columns=['index'])
   except:
      pass

   has_num = df['Num'].map(lambda x: "0" in str(x))
   df = df[has_num]

   df['Cite'] = df['Cite'].map(lambda x: '' if x == "[]" or [] else x)
   

   df['CourtActionDate'] = df['CourtActionDate'].map(lambda x: x[0] if len(x)>0 else pd.NaT) # [x]->x or []->nan

   df = df.fillna('')

   if conf.TABLE == "filing":
      is_disp = df['Disposition']
      is_filing = is_disp.map(lambda x: False if x == True else True)
      df = df[is_filing]
      df.drop(columns=['CourtAction', 'CourtActionDate'], inplace=True)

   if conf.TABLE == "disposition":
      is_disp = df.Disposition.map(lambda x: True if x == True else False)
      df = df[is_disp]

   if conf.NO_WRITE:
      return df

   write(conf, df)

   if not multi:
      complete(conf, df)

   return df


## GETTERS


def getPDFText(path) -> str:
   try:
      doc = fitz.open(path)
   except:
      return ''
   text = ''
   for pg in doc:
      text += ' \n '.join(x[4].replace("\n"," ") for x in pg.get_text(option='blocks'))
   text = re.sub(r'(<image\:.+?>)','',text).strip()
   return text


def getCaseNumber(text: str):
   county = re.search(r'(?:County\: )(\d{2})', text).group(1).strip()
   case_num = re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group().strip()
   return county + "-" + case_num


def getName(text: str):
   """Returns name from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   name = ""
   if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)):
      name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:",
                                                                        "").strip()
   else:
      if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)):
         name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":", "").replace(
            "Case Number:", "").strip()
   return name

def getDOB(text: str):
   """Returns DOB from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   dob = ""
   if bool(re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL)):
      dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
   return dob

def getTotalAmtDue(text: str):
   """Returns total amt due from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   try:
      trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
      totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
      if len(totalrow.split("$")[-1]) > 5:
         totalrow = totalrow.split(" . ")[0]
      tdue = totalrow.split("$")[1].strip().replace("$", "").replace(",", "").replace(" ", "")
   except IndexError:
      tdue = ""
   return tdue

def getAddress(text: str):
   """Returns address from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   try:
      street_addr = re.search(r'(Address 1\:)(.+)(?:Phone)*?', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      street_addr = ""
   try:
      zip_code = re.search(r'(Zip\: )(.+)', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      zip_code = ""
   try:
      city = re.search(r'(?:City\:)(.+?)(?:State)', str(text)).group().strip()
   except (IndexError, AttributeError):
      city = ""
   try:
      state = re.search(r'(State\:\s+?[A-Z]{2})', text).group().strip()
   except (IndexError, AttributeError):
      state = ""
   address = street_addr + " " + city + ", " + state + " " + zip_code
   if len(address) < 5:
      address = ""
   address = address.replace("00000-0000", "").replace("%", "").strip()
   address = re.sub(r'([A-Z]{1}[a-z]+)', '', address)
   return address

def getRace(text: str):
   """Return race from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
   race = racesex.group(1).strip()
   return race

def getSex(text: str):
   """Return sex from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
   sex = racesex.group(2).strip()
   return sex

def getNameAlias(text: str):
   """Return name from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   name = ""
   if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE)):
      name = re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:",
                                                                             "").strip()
   else:
      if bool(re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE)):
         name = re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE).group(1).replace(":", "").replace(
            "Case Number:", "").strip()
   try:
      alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":", "").replace("Alias 1",
                                                                                "").strip()
   except (IndexError, AttributeError):
      alias = ""
   if alias == "":
      return name
   else:
      return name + "\r" + alias

def getCaseInfo(text: str):
   """Returns case information from case text -> cases table
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   case_num = ""
   name = ""
   alias = ""
   race = ""
   sex = ""

   try:
      county: str = re.search(r'(?:County\: )(\d{2})', str(text)).group(1).strip()
      case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group(1).strip()
   except (IndexError, AttributeError):
      pass

   if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE)):
      name = re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:",
                                                                             "").strip()
   else:
      if bool(re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE)):
         name = re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE).group(1).replace(":", "").replace(
            "Case Number:", "").strip()
   try:
      alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":", "").replace("Alias 1",
                                                                                "").strip()
   except (IndexError, AttributeError):
      pass
   else:
      pass
   try:
      dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
      phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
      phone = re.sub(r'[^0-9]', '', phone)
      if len(phone) < 7:
         phone = ""
      if len(phone) > 10 and phone[-3:] == "000":
         phone = phone[0:9]
   except (IndexError, AttributeError):
      dob = ""
      phone = ""
   try:
      racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
      race = racesex.group(1).strip()
      sex = racesex.group(2).strip()
   except (IndexError, AttributeError):
      pass
   try:
      street_addr = re.search(r'(Address 1\:)(.+)(?:Phone)*?', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      street_addr = ""
   try:
      zip_code = re.search(r'(Zip\: )(.+)', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      zip_code = ""
   try:
      city = re.search(r'(City\: )(.*)(State\: )(.*)', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      city = ""
   try:
      state = re.search(r'(?:City\: )(.*)(?:State\: )(.*)', str(text), re.MULTILINE).group(2).strip()
   except (IndexError, AttributeError):
      state = ""

   address = street_addr + " " + city + ", " + state + " " + zip_code
   if len(address) < 5:
      address = ""
   address = address.replace("00000-0000", "").replace("%", "").strip()
   address = re.sub(r'([A-Z]{1}[a-z]+)', '', address)
   case = [case_num, name, alias, dob, race, sex, address, phone]
   return case

def getPhone(text: str):
   """Return phone number from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   try:
      phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
      phone = re.sub(r'[^0-9]', '', phone)
      if len(phone) < 7:
         phone = ""
      if len(phone) > 10 and phone[-3:] == "000":
         phone = phone[0:9]
   except (IndexError, AttributeError):
      phone = ""
   return phone

def getFeeSheet(text: str):
   """
   Return fee sheet and fee summary outputs from case text
   List: [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]
   feesheet = feesheet[['CaseNumber', 'FeeStatus', 'AdminFee', 'Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
   if len(actives) == 0:
      return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
   else:
      try:
         trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
         totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
         if len(totalrow.split("$")[-1]) > 5:
            totalrow = totalrow.split(" . ")[0]
         tbal = totalrow.split("$")[3].strip().replace("$", "").replace(",", "").replace(" ", "").strip()
         tdue = totalrow.split("$")[1].strip().replace("$", "").replace(",", "").replace(" ", "").strip()
         tpaid = totalrow.split("$")[2].strip().replace("$", "").replace(",", "").replace(" ", "").strip()
         thold = totalrow.split("$")[4].strip().replace("$", "").replace(",", "").replace(" ", "").strip()
      except IndexError:
         totalrow = ""
         tbal = ""
         tdue = ""
         tpaid = ""
         thold = ""
      fees = pd.Series(actives, dtype=str)
      fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
      srows = fees.map(lambda x: x.strip().split(" "))
      drows = fees_noalpha.map(lambda x: x.replace(",", "").split("$"))
      coderows = srows.map(lambda x: str(x[5]).strip() if len(x) > 5 else "")
      payorrows = srows.map(lambda x: str(x[6]).strip() if len(x) > 6 else "")
      amtduerows = drows.map(lambda x: str(x[1]).strip() if len(x) > 1 else "")
      amtpaidrows = drows.map(lambda x: str(x[2]).strip() if len(x) > 2 else "")
      balancerows = drows.map(lambda x: str(x[-1]).strip() if len(x) > 5 else "")
      amtholdrows = drows.map(lambda x: str(x[3]).strip() if len(x) > 5 else "")
      amtholdrows = amtholdrows.map(lambda x: x.split(" ")[0].strip() if " " in x else x)
      adminfeerows = fees.map(lambda x: x.strip()[7].strip() if 'N' else '')

      feesheet = pd.DataFrame({'CaseNumber': getCaseNumber(text), 'Total': '', 'FeeStatus': 'ACTIVE', 'AdminFee': adminfeerows.tolist(), 'Code': coderows.tolist(), 'Payor': payorrows.tolist(), 'AmtDue': amtduerows.tolist(), 'AmtPaid': amtpaidrows.tolist(), 'Balance': balancerows.tolist(), 'AmtHold': amtholdrows.tolist() })
      totalrdf = pd.DataFrame({'CaseNumber': getCaseNumber(text), 'Total': 'TOTAL', 'FeeStatus': '', 'AdminFee': '', 'Code': '', 'Payor': '', 'AmtDue': tdue, 'AmtPaid': tpaid, 'Balance': tbal, 'AmtHold': thold },index=[0])

      feesheet = feesheet.dropna()
      feesheet = pd.concat([feesheet, totalrdf], axis = 0, ignore_index=True)

      try:
         d999 = feesheet[feesheet['Code'] == 'D999']['Balance']
      except (TypeError, IndexError):
         d999 = ""

      owe_codes = " ".join(feesheet['Code'][feesheet.Balance.str.len() > 0])
      codes = " ".join(feesheet['Code'])
      allrows = actives
      allrows.append(totalrow)
      allrowstr = "\n".join(allrows)

      feesheet = feesheet[
         ['CaseNumber', 'FeeStatus', 'AdminFee', 'Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance',
          'AmtHold']]

      feesheet['AmtDue'] = pd.to_numeric(feesheet['AmtDue'], errors='coerce')
      feesheet['AmtPaid'] = pd.to_numeric(feesheet['AmtPaid'], errors='coerce')
      feesheet['Balance'] = pd.to_numeric(feesheet['Balance'], errors='coerce')
      feesheet['AmtHold'] = pd.to_numeric(feesheet['AmtHold'], errors='coerce')

      return [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]

def getFeeCodes(text: str):
   """Return fee codes from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   return getFeeSheet(text)[4]

def getFeeCodesOwed(text: str):
   """Return fee codes with positive balance owed from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   return getFeeSheet(text)[3]

def getTotals(text: str):
   """Return totals from case text -> List: [totalrow,tdue,tpaid,tdue,thold]
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   try:
      trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
      totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
      if len(totalrow.split("$")[-1]) > 5:
         totalrow = totalrow.split(" . ")[0]
      tbal = totalrow.split("$")[3].strip().replace("$", "").replace(",", "").replace(" ", "")
      tdue = totalrow.split("$")[1].strip().replace("$", "").replace(",", "").replace(" ", "")
      tpaid = totalrow.split("$")[2].strip().replace("$", "").replace(",", "").replace(" ", "")
      thold = totalrow.split("$")[4].strip().replace("$", "").replace(",", "").replace(" ", "")
      try:
         tdue = pd.to_numeric(tdue, 'coerce')
         tpaid = pd.to_numeric(tpaid, 'coerce')
         thold = pd.to_numeric(thold, 'coerce')
      except:
         pass
   except IndexError:
      totalrow = 0
      tdue = 0
      tpaid = 0
      thold = 0
   return [totalrow, tdue, tpaid, tdue, thold]

def getTotalBalance(text: str):
   """Return total balance from case text
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   try:
      trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
      totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
      if len(totalrow.split("$")[-1]) > 5:
         totalrow = totalrow.split(" . ")[0]
      tbal = totalrow.split("$")[3].strip().replace("$", "").replace(",", "").replace(" ", "")
   except:
      tbal = ""
   return str(tbal)

def getPaymentToRestore(text: str):
   """
   Return (total balance - total d999) from case text -> str
   Does not mask misc balances!
   
   Args:
      text (str): Description
   
   Returns:
      TYPE: Description
   """
   totalrow = "".join(re.findall(r'(Total.*\$.+\$.+\$.+)', str(text), re.MULTILINE)) if bool(
      re.search(r'(Total.*\$.*)', str(text), re.MULTILINE)) else "0"
   try:
      tbalance = totalrow.split("$")[3].strip().replace("$", "").replace(",", "").replace(" ", "").strip()
      try:
         tbal = pd.Series([tbalance]).astype(float)
      except ValueError:
         tbal = 0.0
   except (IndexError, TypeError):
      tbal = 0.0
   try:
      d999raw = re.search(r'(ACTIVE.*?D999\$.*)', str(text), re.MULTILINE).group() if bool(
         re.search(r'(ACTIVE.*?D999\$.*)', str(text), re.MULTILINE)) else "0"
      d999 = pd.Series([d999raw]).astype(float)
   except (IndexError, TypeError):
      d999 = 0.0
   t_out = pd.Series(tbal - d999).astype(float).values[0]
   return str(t_out)

def getBalanceByCode(text: str, code: str):
   """
   Return balance by code from case text -> str
   
   Args:
      text (str): Description
      code (str): Description
   
   Returns:
      TYPE: Description
   """
   actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
   fees = pd.Series(actives, dtype=str)
   fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
   srows = fees.map(lambda x: x.strip().split(" "))
   drows = fees_noalpha.map(lambda x: x.replace(",", "").split("$"))
   coderows = srows.map(lambda x: str(x[5]).strip() if len(x) > 5 else "")
   balancerows = drows.map(lambda x: str(x[-1]).strip() if len(x) > 5 else "")
   codemap = pd.DataFrame({
      'Code': coderows,
      'Balance': balancerows
   })
   matches = codemap[codemap.Code == code].Balance
   return str(matches.sum())

def getAmtDueByCode(text: str, code: str):
   """
   Return total amt due from case text -> str
   
   Args:
      text (str): Description
      code (str): Description
   
   Returns:
      TYPE: Description
   """
   actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
   fees = pd.Series(actives, dtype=str)
   fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
   srows = fees.map(lambda x: x.strip().split(" "))
   drows = fees_noalpha.map(lambda x: x.replace(",", "").split("$"))
   coderows = srows.map(lambda x: str(x[5]).strip() if len(x) > 5 else "")
   payorrows = srows.map(lambda x: str(x[6]).strip() if len(x) > 6 else "")
   amtduerows = drows.map(lambda x: str(x[1]).strip() if len(x) > 1 else "")

   codemap = pd.DataFrame({
      'Code': coderows,
      'Payor': payorrows,
      'AmtDue': amtduerows
   })

   codemap.AmtDue = codemap.AmtDue.map(lambda x: pd.to_numeric(x, 'coerce'))

   due = codemap.AmtDue[codemap.Code == code]
   return str(due)

def getAmtPaidByCode(text: str, code: str):
   """
   Return total amt paid from case text -> str
   
   Args:
      text (str): Description
      code (str): Description
   
   Returns:
      TYPE: Description
   """
   actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
   fees = pd.Series(actives, dtype=str)
   fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
   srows = fees.map(lambda x: x.strip().split(" "))
   drows = fees_noalpha.map(lambda x: x.replace(",", "").split("$"))
   coderows = srows.map(lambda x: str(x[5]).strip() if len(x) > 5 else "")
   payorrows = srows.map(lambda x: str(x[6]).strip() if len(x) > 6 else "")
   amtpaidrows = drows.map(lambda x: str(x[2]).strip() if len(x) > 2 else "")

   codemap = pd.DataFrame({
      'Code': coderows,
      'Payor': payorrows,
      'AmtPaid': amtpaidrows
   })

   codemap.AmtPaid = codemap.AmtPaid.map(lambda x: pd.to_numeric(x, 'coerce'))

   paid = codemap.AmtPaid[codemap.Code == code]
   return str(paid)

def getCaseYear(text):
   """
   Return case year 
   
   Args:
      text (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   cnum = getCaseNumber(text)
   return float(cnum[6:10])

def getCounty(text):
   """
   Return county
   
   Args:
      text (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   cnum = getCaseNumber(text)
   return int(cnum[0:2])

def getLastName(text):
   """
   Return last name
   
   Args:
      text (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   name = getName(text)
   return name.split(" ")[0].strip()

def getFirstName(text):
   """
   Return first name
   
   Args:
      text (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   name = getName(text)
   if len(name.split(" ")) > 1:
      return name.split(" ")[1].strip()
   else:
      return name

def getMiddleName(text):
   """
   Return middle name or initial
   
   Args:
      text (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   name = getName(text)
   if len(name.split(" ")) > 2:
      return name.split(" ")[2].strip()
   else:
      return ""

def getCharges(text):
   b = re.findall(r'(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}.{10,75})', text, re.MULTILINE)
   b = [re.sub(r'[A-Z][a-z][a-z\s]+.+','',x) for x in b]
   b = [re.sub(r'\:\s\:.+','',x) for x in b]
   # b = [re.sub(r'^\d{3}\n.+','',x) for x in b]
   # b = ['' if re.search(r'\d{1,2}\:{1,2}\s\D{2}',x) else x for x in b]
   # btest = [True if len(str(x))>9 else False for x in b]
   # b = pd.Series(b)
   # b = b[btest]
   return b


## FETCH

def mark(in_path, out_path, no_write=False):

    # get input text, names, dob
    input_archive = read(in_path)
    mapinputs = setinputs(input_archive)
    mapoutputs = setoutputs()
    mapconf = set(mapinputs, mapoutputs, no_write=True, no_prompt=True, overwrite=True, log=False, debug=True)

    caseinfo = map(mapconf, lambda x: x, getCaseNumber, getName, getDOB, names=['AllPagesText','CaseNumber','NAME','DOB'])

    # get output cols 
    output_query = readPartySearchQuery(out_path)[0]

    # get common columns
    q_columns = pd.Series(output_query.columns).astype("string")
    i_columns = pd.Series(caseinfo.columns).astype("string")
    q_columns = q_columns.str.upper().str.strip().str.replace(" ","_")
    i_columns = i_columns.str.upper().str.strip().str.replace(" ","_")
    common = q_columns.map(lambda x: x in i_columns.tolist())
    common_cols = q_columns[common]

    assert common_cols.shape[0] > 0

    output_query['RETRIEVED_ON'] = output_query.index.map(lambda x: time.time() if str(output_query.NAME[x]).replace(",","") in caseinfo.NAME.tolist() and output_query.RETRIEVED_ON[x] == "" else output_query.RETRIEVED_ON[x])
    output_query['RETRIEVED_ON'] = output_query['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
    output_query['CASES_FOUND'] = output_query['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
    if not no_write:
        with pd.ExcelWriter(out_path) as writer:
            output_query.to_excel(writer, sheet_name="MarkedQuery", engine="openpyxl")

    return output_query

def fetch(listpath, path, cID, uID, pwd, qmax=0, qskip=0, speed=1, no_log=False, no_update=False, debug=False):
   """
   Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to fetch.
   
   USE WITH CHROME (TESTED ON MACOS) 
   KEEP YOUR COMPUTER POWERED ON AND CONNECTED TO THE INTERNET.
   
   Args:
      listpath: (path-like obj) Query template path / input path
      path: (path-like obj) Path to output/downloads directory 
      cID (str): Alacourt.com Customer ID
      uID (str): Alacourt.com User ID
      pwd (str): Alacourt.com Password
      qmax (int, optional): Max queries to pull from inputs
      qskip (int, optional): Skip top n queries in inputs
      speed (int, optional): fetch rate multiplier
      no_log (bool, optional): Do not print logs to console
      no_update (bool, optional): Do not update input query file with completion status
      debug (bool, optional): Print detailed logs to console

   Returns:
      [driver, query_out, query_writer]:
         driver[0]: Google Chrome WebDriver() object 
         query_out[1]: (pd.Series) fetch queue
         query_writer[2]: (pd.DataFrame) Updated input query file
   """

   rq = readPartySearchQuery(listpath, qmax, qskip, no_log)

   query = pd.DataFrame(rq[0]) # for fetch - only search columns
   query_writer = pd.DataFrame(rq[1]) # original sheet for write completion 
   incomplete = query.RETRIEVED_ON.map(lambda x: True if x == "" else False)
   query = query[incomplete]

   options = webdriver.ChromeOptions()
   options.add_experimental_option('prefs', {
      "download.default_directory": path, #Change default directory for downloads
      "download.prompt_for_download": False, #To auto download the file
      "download.directory_upgrade": True,
      "plugins.always_open_pdf_externally": True #It will not display PDF directly in chrome
   })

   # start browser session, login
   if not no_log:
      click.secho("Starting browser... Do not close while in progress!",bold=True)
   driver = webdriver.Chrome(options=options)
   login(driver, cID, uID, pwd, speed)
   if not no_log:
      click.secho("Authentication successful. Fetching cases via party search...",bold=True)

   # search, retrieve from URL, download to path
   for i, n in enumerate(query.index):
      if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
            login(driver, cID, uID, pwd, speed, no_log)
      driver.implicitly_wait(4/speed)
      results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], speed=speed, no_log=no_log)
      driver.implicitly_wait(4/speed)
      if len(results) == 0:
         query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
         query_writer['CASES_FOUND'][n] = "0"
         if not no_log:
            click.echo(f"{query.NAME[n]}: Found no results.")
         continue
      results = pd.Series(results)
      tqdm.pandas(desc=query.NAME[n])
      results.progress_map(lambda x: downloadPDF(driver, x))
      if not no_update:
         query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
         query_writer['CASES_FOUND'][n] = str(len(results))
         query_writer['RETRIEVED_ON'] = query_writer['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
         query_writer['CASES_FOUND'] = query_writer['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
         query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)
   return [driver, query_writer]

def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", filed_before="", filed_after="", speed=1, no_log=False, debug=False, cID="", uID="", pwd=""):
   """
   Collect PDFs via SJIS Party Search Form from Alacourt.com
   Returns list of URLs for downloadPDF() to download
   
   Args:
      driver (WebDriver): selenium/chrome web driver object 
      name (str, optional): Name (LAST FIRST)
      party_type (str, optional): "Defendants" | "Plaintiffs" | "ALL"
      ssn (str, optional): Social Security Number
      dob (str, optional): Date of Birth
      county (str, optional): County
      division (str, optional): "All Divisions"
         "Criminal Only"
         "Civil Only"
         "CS - CHILD SUPPORT"
         "CV - CIRCUIT - CIVIL"
         "CC - CIRCUIT - CRIMINAL"
         "DV - DISTRICT - CIVIL"
         "DC - DISTRICT - CRIMINAL"
         "DR - DOMESTIC RELATIONS"
         "EQ - EQUITY-CASES"
         "MC - MUNICIPAL-CRIMINAL"
         "TP - MUNICIPAL-PARKING"
         "SM - SMALL CLAIMS"
         "TR - TRAFFIC"
      case_year (str, optional): YYYY
      filed_before (str, optional): M/DD/YYYY
      filed_after (str, optional): M/DD/YYYY
      speed (int, optional): fetch rate multiplier
      no_log (bool, optional): Do not print logs.
      debug (bool, optional): Print detailed logs.
   
   Returns:
      URL list to PDFs
   """
   speed = speed * 2


   if "frmIndexSearchForm" not in driver.current_url:
      driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

   driver.implicitly_wait(5/speed)


   # connection error 
   try:
      party_name_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtName")
   except selenium.common.exceptions.NoSuchElementException:
      if debug:
         print("""NoSuchElementException on alac.py 2173: party_name_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtName")""")
      if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
         time.sleep(10)
         login(driver,cID=cID,uID=uID,pwd=pwd)
         driver.implicitly_wait(1)
      driver.get("https:v2.alacourt.com/frmIndexSearchForm.aspx")

      if not no_log:
         click.secho("Successfully connected and logged into Alacourt!",bold=True)

   # field search

   if name != "":
      party_name_box.send_keys(name)
   if ssn != "":
      ssn_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtSSN")
      ssn_box.send_keys(ssn)
   if dob != "":
      date_of_birth_box = driver.find_element(by=By.NAME,value="ctl00$ContentPlaceHolder1$txtDOB")
      date_of_birth_box.send_keys(dob)
   if party_type != "":
      party_type_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$rdlPartyType")
      pts = Select(party_type_select)
      if party_type == "plaintiffs":
         pts.select_by_visible_text("Plaintiffs")
      if party_type == "defendants":
         pts.select_by_visible_text("Defendants")
      if party_type == "all":
         pts.select_by_visible_text("ALL")

   if county != "":
      county_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCounties")
      scounty = Select(county_select)
      scounty.select_by_visible_text(county)
   if division != "":
      division_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$UcddlDivisions1$ddlDivision")
      sdivision = Select(division_select)
      sdivision.select_by_visible_text(division)
   if case_year != "":
      case_year_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCaseYear")
      scase_year = Select(case_year_select)
      scase_year.select_by_visible_text(case_year)
   no_records_select = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlNumberOfRecords")
   sno_records = Select(no_records_select)
   sno_records.select_by_visible_text("1000")
   if filed_before != "":
      filed_before_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtFrom")
      filed_before_box.send_keys(filed_before)
   if filed_after != "":
      filed_after_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtTo")
      filed_after_box.send_keys(filed_after)

   driver.implicitly_wait(1/speed)

   # submit search
   search_button = driver.find_element(by=By.ID,value="searchButton")

   driver.implicitly_wait(1/speed)
   try:
      search_button.click()
   except:
      driver.implicitly_wait(5/speed)
      time.sleep(5)

   if debug:
      click.echo("Submitted party search form...")

   driver.implicitly_wait(1/speed)

   # count pages
   try:
      page_counter = driver.find_element(by=By.ID,value="ContentPlaceHolder1_dg_tcPageXofY").text
      pages = int(page_counter.strip()[-1])

   except:
      pages = 1

   # count results
   try:
      results_indicator = driver.find_element(by=By.ID, value="ContentPlaceHolder1_lblResultCount")
      results_count = int(results_indicator.text.replace("Search Results: ","").replace(" records returned.","").strip())
      if results_count == 1000 and debug or no_log:
         click.echo(f"Max records (1000) returned for party {name}!")
   except:
      pass

   if debug:
      click.echo(f"Found {results_count} results, fetching URLs and downloading PDFs...")


   # get PDF links from each page
   pdflinks = []
   i = 0
   for i in range(0,pages):
      driver.implicitly_wait(0.5/speed)
      hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
      for x in hovers:
         try:
            a = x.get_attribute("href")
            if "PDF" in a:
               pdflinks.append(a)
         except:
            pass
      driver.implicitly_wait(0.5/speed)
      try:
         pager_select = Select(driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"))
         next_pg = int(pager_select.text) + 1
         driver.implicitly_wait(0.5/speed)
      except:
         try:
            driver.implicitly_wait(0.5/speed)
            time.sleep(0.5/speed)
            next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
            next_button.click()
         except:
            continue
   return pdflinks

def downloadPDF(driver, url, no_log=False, cID="", uID="", pwd="", speed=2):
   """
   With (driver), download PDF at (url)
   
   Args:
      driver (WebDriver): Google Chrome selenium.WebDriver() object
      url (TYPE): Description
      no_log (bool, optional): Description
   
   Deleted Parameters:
      speed (int, optional): fetch rate multiplier
   """
   if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx" and cID != "" and uID != "" and pwd != "":
      login(driver,cID=cID,uID=uID,pwd=pwd)
   a = driver.get(url)
   driver.implicitly_wait(0.5)


def login(driver, cID, uID="", pwd="", speed=1, no_log=False, path=""):
   """Login to Alacourt.com using (driver) and auth (cID, username, pwd) at (speed) for browser download to directory at (path)
   
   Args:
      driver (WebDriver): Google Chrome selenium.WebDriver() object
      cID (str): Alacourt.com Customer ID
      uID (str): Alacourt.com User ID
      pwd (str): Alacourt.com Password
      speed (TYPE): fetch rate multiplier
      no_log (bool, optional): Do not print logs
      path (str, optional): Set browser download path 
   
   Returns:
      driver (WebDriver): Google Chrome selenium.WebDriver() object
   """
   if driver == None:
      options = webdriver.ChromeOptions()
      options.add_experimental_option('prefs', {
         "download.default_directory": path, #Change default directory for downloads
         "download.prompt_for_download": False, #To auto download the file
         "download.directory_upgrade": True,
         "plugins.always_open_pdf_externally": True #It will not display PDF directly in chrome
      })
      driver = webdriver.Chrome(options=options)

   if not no_log:
      click.echo("Connecting to Alacourt...")


   login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

   if not no_log:
      click.echo("Logging in...")

   driver.implicitly_wait(1)
   
   cID_box = driver.find_element(by=By.NAME, 
      value="ctl00$ContentPlaceHolder$txtCusid")
   username_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId")
   pwd_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword")
   login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

   cID_box.send_keys(cID)
   username_box.send_keys(uID)
   pwd_box.send_keys(pwd)

   driver.implicitly_wait(1)

   login_button.click()

   driver.implicitly_wait(1)

   try:
      continueLogIn = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$btnContinueLogin")
      continueLogIn.click()
   except:
      pass


   driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

   if not no_log:
      click.secho("Successfully connected and logged into Alacourt!",bold=True)


   driver.implicitly_wait(1)

   return driver

def readPartySearchQuery(path, qmax=0, qskip=0, speed=1, no_log=False):
   """Reads and interprets query template spreadsheets for `alacorder fetch` to queue from. Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in an Excel spreadsheet, CSV, or JSON file to submit a list of queries for Alacorder to fetch.
   
   Args:
      path (TYPE): Description
      qmax (int, optional): Description
      qskip (int, optional): Description
      speed (int, optional): Description
      no_log (bool, optional): Description
   
   Returns:
      [query_out, writer_df]:
         query_out: (pd.DataFrame) queue object for alac.fetch()
         writer_df: (pd.DataFrame) progress log to be written back to (path)
   
   Raises:
      Exception: Connection error!
   """
   good = os.path.exists(path)
   ext = os.path.splitext(path)[1]
   if ext == ".xlsx" or ".xls":
      query = pd.read_excel(path, dtype=pd.StringDtype())
   if ext == ".csv":
      query = pd.read_csv(path, dtype=pd.StringDtype())
   if ext == ".json":
      query = pd.read_json(path, orient='table', dtype=pd.StringDtype())
   if qskip > 0:
      query = query.truncate(before=qskip)
   if qmax > 0:
      query = query.truncate(after=qmax+qskip)

   writer_df = pd.DataFrame(query)

   if "RETRIEVED_ON" not in writer_df.columns:
      writer_df['RETRIEVED_ON'] = pd.NaT
      writer_df['CASES_FOUND'] = pd.NaT

   query_out = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"])

   clist = []
   for c in query.columns:
      if str(c).upper().strip().replace(" ","_") in ["NAME", "PARTY", "DATE_OF_BIRTH", "BIRTHDATE", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"]:
         ce = str(c).replace("DATE_OF_BIRTH","DOB").replace("BIRTHDATE","DOB").replace("PARTY","PARTY_TYPE").replace("PARTY_TYPE_TYPE","PARTY_TYPE").strip()
         clist += [ce]
         query_out[str(c).upper().strip().replace(" ","_")] = query[str(c)]
         query_out[ce] = query[str(c)]
   clist = pd.Series(clist).drop_duplicates().tolist()
   if clist == []:
      raise Exception("Invalid template! Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in a spreadsheet or JSON file to submit a list of queries for Alacorder to fetch.")
      click.echo(f"Field columns {clist} identified in query file.")

   query_out = query_out.fillna('')
   return [query_out, writer_df]

## LOGS


def echo_conf(input_path, make, output_path, overwrite, no_write, dedupe, no_prompt, compress):
   """
   Logs configuration details to console
   
   Args:
      input_path (TYPE): Description
      make (TYPE): Description
      output_path (TYPE): Description
      overwrite (TYPE): Description
      no_write (TYPE): Description
      dedupe (TYPE): Description
      no_prompt (TYPE): Description
      compress (TYPE): Description
   
   Returns:
      TYPE: Description
   """
   return f"""{"ARCHIVE is enabled. Alacorder will write full text case archive to output path instead of data tables. " if make == "archive" else ''}{"NO-WRITE is enabled. Alacorder will NOT export outputs. " if no_write else ''}{"OVERWRITE is enabled. Alacorder will overwrite existing files at output path! " if overwrite else ''}{"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output. " if dedupe and make == "archive" else ''}{"NO_PROMPT is enabled. All user confirmation prompts will be suppressed as if set to default by user." if no_prompt else ''}{"COMPRESS is enabled. Alacorder will try to compress output file." if compress == True else ''}""".strip()

def pick_table():
   upick_table = ('''
   For compressed archive, enter:
      [A] Full text archive
   To export a data table, enter:
      [B]  Case Details
      [C]  Fee Sheets
      [D]  Charges (all)
      [E]  Charges (disposition only)
      [F]  Charges (filing only)

   Enter selection to continue. [A-F]
   ''')
   return upick_table

def pick_table_only():
   upick_table_only = ('''
   To export a data table, enter:
      [B]  Case Details
      [C]  Fee Sheets
      [D]  Charges (all)
      [E]  Charges (disposition only)
      [F]  Charges (filing only)

   Enter selection to continue. [B-F]
   ''')
   return upick_table_only

def just_table():
   ujust_table = ('''
   EXPORT DATA TABLE: To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format (.csv, .json, .dta), select a table after entering output file path.

   Enter path.
   ''')
   return ujust_table

def just_archive():
   ujust_archive = ('''
   EXPORT ARCHIVE: Compressed archives can store thousands of cases' data using a fraction of the original PDF storage. To export full text archive, enter full output path. Supported file extensions are archive.pkl.xz, archive.json(.zip), archive.csv(.zip), and archive.parquet.

   Enter path.
   ''')
   return ujust_archive

def both():
   uboth = ('''
   EXPORT DATA TABLE: To export data table from case inputs, enter full output path. Use .xls or .xlsx to export all tables, or, if using another format (.csv, .json, .dta), select a table after entering output file path.

   Enter output path.
   ''')
   return click.style(uboth)

def title():
   utitle = """Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.

      ACCEPTED   /pdfs/path/   PDF directory           
      INPUTS:    .pkl(.xz)     Pickle archive
                 .json(.zip)   JSON archive
                 .csv(.zip)    CSV archive
                 .parquet      Apache Parquet archive


   Enter input path.
   """
   return utitle

def smalltitle():
   usmalltitle = """Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.
   """
   return usmalltitle

def text_p():
   utext_p = ('''
   Enter path to output text file (must be .txt). 
''')
   return utext_p

def complete(conf, *outputs):
   """
   Logs completion
   
   Args:
      conf (TYPE): Description
      *outputs: Description
   """

   elapsed = math.floor(time.time() - conf.TIME)
   if conf['LOG'] != False and conf['MAKE'] != "archive":
      click.secho(f"Task completed in {elapsed} seconds.", bold=True)

def log(msg, fg="", bold=False, italic=False, *conf):
   if isinstance(conf, pd.core.series.Series):
      try:
         if conf['LOG']:
            click.secho(msg, fg=fg, bold=bold, italic=italic)
      except:
         pass
   else:
      click.secho(msg, fg=fg, bold=bold, italic=italic)
