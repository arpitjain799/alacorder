# ALACORDER 78
# sam robson


import click, rich, tqdm.rich # command line interface
import threading, PySimpleGUI as sg # graphical user interface
import os, sys, time, glob, inspect, math, re, warnings # standard library tools
import pandas as pd # 2.0.0rc0
import fitz # PyMuPdf text extraction
import numpy as np
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.min_rows', 50)
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_categories', 16)
pd.set_option('display.precision',2)
try:
	pd.set_option('mode.dtype_backend','pyarrow')
except:
	pass
try:
	pd.set_option('mode.string_storage','pyarrow')
except:
	pass
warnings.filterwarnings('ignore')

name = "ALACORDER beta"
version = "78.5.3"

fname = f"{name} {version}"

sg.theme("DarkBlack")

sg.set_options(font="Default 12")


###################################### ALAC ########################################

## CONFIG

def append_archive(in_path, out_path, no_write=False, obj=False, window=None):
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
     else: # object in_path
          output_archive = read(out_path)
          new_archive = pd.concat([output_archive, in_path], ignore_index = True)
     if window != None:
          window.write_event_value('COMPLETE','AA-COMPLETE')
     return new_archive


def read(path, log=True, window=None):
     if os.path.isdir(path):
          queue = pd.Series(glob.glob(path + '**/*.pdf', recursive=True))
          if window != None:
               aptxt = []
               print("Extracting text...")
               window.write_event_value("PROGRESS-TEXT-TOTAL",len(queue.tolist()))
               for i, pp in enumerate(queue.tolist()):
                    aptxt += [getPDFText(pp)]
                    window.write_event_value("PROGRESS-TEXT",i+1)
               allpagestext = pd.Series(aptxt, dtype="string")
          else:
               tqdm.rich.tqdm.pandas()
               allpagestext = queue.progress_map(lambda x: getPDFText(x)).astype("string")
          archive = pd.DataFrame({
               'Timestamp': time.time(),
               'AllPagesText': allpagestext,
               'Path': queue
               })
          archive.AllPagesText = archive.AllPagesText.astype("string")
          archive.Path = archive.Path.astype("string")
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
          return archive

def setinputs(path, debug=False, fetch=False, window=None):
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
               if "ALABAMA SJIS CASE DETAIL" in path.tolist()[0] and path.shape[0] > 0:
                    queue = pd.Series(path.tolist())
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
                         print(f"NZPATH: {nozipext}, NOZIPEXT: {nozipext}, PATH: {path}")
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

def setoutputs(path="", debug=False, archive=False, table="", fetch=False, window=None):
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
     echo = ""
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
     elif good and debug:
          echo = "Output path is valid. Call set() to finish configuration."
     elif echo != "":
          pass
     else:
          echo = ""

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

def set(inputs, outputs=None, count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="", fetch_uID="", fetch_pwd="", fetch_qmax=0, fetch_qskip=0, archive=False, append=False, window=None):
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
               print(f"Removed {dif} duplicate cases from queue.")
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

def setpaths(input_path, output_path=None, count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="", fetch_uID="", fetch_pwd="", fetch_qmax="", fetch_qskip="", archive=False, append=False, window=None): # DOC
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
          print(a.ECHO)
     b = setoutputs(output_path, fetch=fetch)
     if b.MAKE == "archive": #
          compress = True
     c = set(a, b, count=count, table=table, overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, debug=debug, no_batch=no_batch, compress=compress, fetch=fetch, fetch_cID=fetch_cID, fetch_uID=fetch_uID, fetch_pwd=fetch_pwd, fetch_qmax=fetch_qmax, fetch_qskip=fetch_qskip, archive=archive, append=append, window=window)

     return c

def setinit(input_path, output_path=None, archive=False,count=0, table='', overwrite=False, log=True, dedupe=False, no_write=False, no_prompt=False, debug=False, no_batch=True, compress=False, fetch=False, fetch_cID="",fetch_uID="", fetch_pwd="", fetch_qmax=0, fetch_qskip=0, append=False, window=None): # DOC
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
               fetch(input_path, output_path, fetch_cID, fetch_uID, fetch_pwd, fetch_qmax, fetch_qskip, fetch_no_log)
          else:
               input_path = setinputs(input_path)
               output_path = setoutputs(output_path)
               fetch(input_path, output_path, fetch_cID, fetch_uID, fetch_pwd, fetch_qmax, fetch_qskip, fetch_no_log)
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

def write(conf, outputs, window=None):
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
                    print(conf, f"Fallback export to {os.path.splitext(conf.OUTPUT_PATH)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
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
                    print(conf, f"Fallback export to {os.path.splitext(conf.OUTPUT_PATH)}.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
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

def archive(conf, window=None, **kwargs):
     """
     Write full text archive to file.pkl.xz

     Args:
          conf (pd.Series): Configuration object with paths and settings

     Returns:
          DataFrame (written to file at conf.OUTPUT_PATH)
     """
     start_time = time.time()

     if conf.LOG or conf['DEBUG']:
          print("Writing full text archive from cases...")

     if not conf.IS_FULL_TEXT and window != None:
          aptxt = []
          print("Extracting text...")
          window.write_event_value("PROGRESS-TEXT-TOTAL",len(conf.QUEUE.tolist()))
          for i, pp in enumerate(conf.QUEUE.tolist()):
               aptxt += [getPDFText(pp)]
               window.write_event_value("PROGRESS-TEXT",i+1)
          allpagestext = pd.Series(aptxt, dtype="string")
     elif not conf.IS_FULL_TEXT and window == None:
          tqdm.rich.tqdm.pandas()
          allpagestext = conf.QUEUE.progress_map(lambda x: getPDFText(x)).astype("string")
     else:
          allpagestext = pd.Series(conf.QUEUE, dtype="string")

     if (conf.LOG or conf['DEBUG']) and conf.IS_FULL_TEXT == False:
          print("Exporting archive to file at output path...")

     outputs = pd.DataFrame({
          'Path': conf.QUEUE if not conf.IS_FULL_TEXT else pd.NaT,
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
               print(f"Removed {dif} duplicate cases from queue.")

     if conf.APPEND == True:
          if conf.LOG:
               print(f"Appending archive to existing archive at output path...")
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
     complete(conf,window=window)
     return outputs

def map(conf, *args, bar=True, names=[], window=None): # TQDM PDF=>TEXT (bar flag)
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
               print(f"Removed {dif} duplicate cases from queue.")

     if not conf.NO_BATCH: # split into batches
          batches = batcher(conf)
     else:
          batches = [conf.QUEUE]

     # sort args into functions and their parameters
     func = pd.Series(args).map(lambda x: 1 if inspect.isfunction(x) else 0)
     funcs = func.index.map(lambda x: args[x] if func[x] > 0 else pd.NaT)
     no_funcs = func.index.map(lambda x: args[x] if func[x] == 0 else pd.NaT)
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
               print(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
          b = pd.DataFrame()

          # stop slow writes on big files between batches
          if bool(conf.OUTPUT_PATH) and i > 0 and not conf.NO_WRITE:
               if os.path.getsize(conf.OUTPUT_PATH) > 500: 
                    temp_no_write_tab = True
          if i == len(conf.QUEUE) - 1:
               temp_no_write_tab = False

          # get text
          if not conf.IS_FULL_TEXT and window != None:
               aptxt = []
               window.write_event_value("PROGRESS-TEXT-TOTAL",len(conf.QUEUE.tolist()))
               for i, pp in enumerate(conf.QUEUE.tolist()):
                    aptxt += [getPDFText(pp)]
                    window.write_event_value("PROGRESS-TEXT",i+1)
               allpagestext = pd.Series(aptxt, dtype="string")
          elif not conf.IS_FULL_TEXT and window == None:
               tqdm.rich.tqdm.pandas()
               allpagestext = conf.QUEUE.progress_map(lambda x: getPDFText(x)).astype("string")
          else:
               allpagestext = pd.Series(conf.QUEUE, dtype="string")

          # retrieve getter
          for i in column_getters.index:
               name = column_getters.Name[i]
               arg = column_getters.Arguments[i]
               getter = column_getters.Method[i]

          # map getter 
          for i, getter in enumerate(column_getters.Method.tolist()):
               arg = column_getters.Arguments[i]
               name = column_getters.Name[i]
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
     else:
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

def table(conf, window=None):
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

def init(conf, window=None):
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
          fetch(conf.INPUT_PATH, conf.OUTPUT_PATH, fetch_cID=conf.ALA_CUSTOMER_ID, fetch_uID=conf.ALA_USER_ID, fetch_pwd=conf.ALA_PASSWORD, fetch_qmax=conf.FETCH_QMAX, fetch_qskip=conf.FETCH_QSKIP,window=window)
     elif conf.MAKE == "multiexport" and (conf.TABLE == "" or conf.TABLE == "all"):
          a = cases(conf, window=window)
     elif conf.MAKE == "archive":
          a = archive(conf, window=window)
     elif conf.TABLE == "cases":
          a = cases(conf, window=window)
     elif conf.TABLE == "fees":
          a = fees(conf, window=window)
     elif conf.TABLE == "charges":
          a = charges(conf, window=window)
     elif conf.TABLE == "disposition":
          a = charges(conf, window=window)
     elif conf.TABLE == "filing":
          a = charges(conf, window=window)
     else:
          a = None
     return a

def batcher(conf, queue=pd.Series(), window=None):
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
          elif conf.FOUND > 25000:
               batchsize = 10000
          else:
               batchsize = 1000
          batches = np.array_split(q, 3)
     else:
          batches = np.array_split(q, 1)
     return batches


## TABLE PARSERS

def cases(conf, window=None):
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
               print(f"Removed {dif} duplicate cases from queue.")

     queue = pd.Series(conf.QUEUE)

     if not conf.IS_FULL_TEXT and window != None:
          aptxt = []
          window.write_event_value("PROGRESS-TEXT-TOTAL",len(conf.QUEUE.tolist()))
          for i, pp in enumerate(conf.QUEUE.tolist()):
               aptxt += [getPDFText(pp)]
               window.write_event_value("PROGRESS-TEXT",i+1)
          allpagestext = pd.Series(aptxt, dtype="string")
     elif not conf.IS_FULL_TEXT and window == None:
          tqdm.rich.tqdm.pandas()
          allpagestext = conf.QUEUE.progress_map(lambda x: getPDFText(x)).astype("string")
     else:
          allpagestext = pd.Series(conf.QUEUE, dtype="string")


     if not conf['NO_BATCH']:
          batches = batcher(conf, allpagestext)
     else:
          batches = [pd.Series(allpagestext, dtype="string")]


     for i, c in enumerate(batches):
          b = pd.DataFrame({'AllPagesText':c})
          c = pd.Series(c, dtype="string")
          if i > 0:
               print(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
          b = pd.DataFrame()
          b['CaseInfoOutputs'] = c.map(lambda x: getCaseInfo(x))
          b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0]).astype("string")
          b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1]).astype("string")
          b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2]).astype("string")
          b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3]).astype("string")
          b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4]).astype("string")
          b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5]).astype("string")
          b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6]).astype("string")
          b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7]).astype("string")

          conf.IS_FULL_TEXT = True
          chinputs = setinputs(c)
          allcharges = setinit(chinputs, conf.OUTPUT_PATH, archive=False, table="charges", no_write=True, no_prompt=True, log=False, no_batch=True)

          print("Reading fee sheets...")

          b['FeeOutputs'] = c.map(lambda x: getFeeSheet(x))
          b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
          b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
          b['PaymentToRestore'] = c.map(
                lambda x: getPaymentToRestore(x))
          b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
          b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
          b['FeeCodesOwed'] = b['FeeCodesOwed'].map(lambda x: '' if x == "nan" else x)
          b['FeeCodes'] = b['FeeCodes'].map(lambda x: '' if x == "nan" else x)
          b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])
          b['FeeCodes'] = b['FeeCodes'].astype("string")
          b['FeeCodesOwed'] = b['FeeCodesOwed'].astype("string")

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
                    print(f"Removed {dif} duplicate cases from queue.")

          if conf.LOG:
               print(f"Cleaning outputs and writing file to export path...")

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
                         print(f"openpyxl engine failed! Trying xlsxwriter...")
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
                                   print(f"openpyxl engine failed! Trying xlsxwriter...")
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
                                   print(f"""Fallback export to {os.path.splitext(conf.OUTPUT_PATH)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!""")
                              except (ImportError, FileNotFoundError, IndexError, ValueError):
                                   print("Failed to export!")
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
     if window != None:
          complete(conf, window=window)
     else:
          complete(conf)

     return [cases, fees, allcharges]

def fees(conf, window=None):   # TQDM PDF=>TEXT
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
               print(f"Removed {dif} duplicate cases from queue.")

     if not conf['NO_BATCH']:
          batches = batcher(conf)
     else:
          batches = [conf.QUEUE]

     for i, c in enumerate(batches):
          if i > 0:
               print(f"Finished batch {i}. Now reading batch {i+1} of {len(batches)}")
          b = pd.DataFrame()

          if not conf.IS_FULL_TEXT and window != None:
               aptxt = []
               window.write_event_value("PROGRESS-TEXT-TOTAL",len(conf.QUEUE.tolist()))
               for i, pp in enumerate(conf.QUEUE.tolist()):
                    aptxt += [getPDFText(pp)]
                    window.write_event_value("PROGRESS-TEXT",i+1)
               allpagestext = pd.Series(aptxt, dtype="string")
          elif not conf.IS_FULL_TEXT and window == None:
               tqdm.rich.tqdm.pandas()
               allpagestext = conf.QUEUE.progress_map(lambda x: getPDFText(x)).astype("string")
          else:
               allpagestext = pd.Series(conf.QUEUE, dtype="string")
          b['CaseNumber'] = allpagestext.map(lambda x: getCaseNumber(x))

          print("Reading fee sheets...")
          b['FeeOutputs'] = allpagestext.map(lambda x: getFeeSheet(x))
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
     if window != None:
          complete(conf, window)
     return fees

def isfulltext(conf):
     try:
          if isinstance(conf, pd.core.series.Series):
               if "IS_FULL_TEXT" in conf.columns:
                    return "ALABAMA SJIS CASE DETAIL" in str(conf.QUEUE.tolist()[0])
               if "AllPagesText" in conf.columns:
                    return "ALABAMA SJIS CASE DETAIL" in str(conf.AllPagesText.tolist()[0])
          elif isinstance(conf, pd.core.frame.DataFrame):
               conf = conf.melt()
               return "ALABAMA SJIS CASE DETAIL" in str(conf.AllPagesText.tolist()[0])
          elif isinstance(conf, list):
               return "ALABAMA SJIS CASE DETAIL" in str(conf[0])
          else:
               return None
     except:
          return None


def charges(conf, multi=False, window=None):
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

     if conf.IS_FULL_TEXT:
          print("Reading charges...")
     else:
          print("Extracting text and reading charges...")

     df = map(conf, getCaseNumber, getCharges, names=['CaseNumber','Charges'])
     df = df.explode('Charges') # num :: [ch, ch] -> num :: ch, num :: ch
     df['Charges'] = df['Charges'].astype("string")
     df['Sort'] = df['Charges'].map(lambda x: str(x)[9] if len(str(x)) > 9 else '') # charge sorter slices at first char after Code: if digit -> Disposition 

     df = df.dropna() # drop pd.NaT before bool() ambiguity TypeError

     df['Disposition'] = df['Sort'].str.isdigit().astype("boolean")
     df['Filing'] = df['Disposition'].map(lambda x: not x).astype("boolean")
     df['Felony'] = df['Charges'].str.contains("FELONY").astype("boolean")
     df['Conviction'] = df['Charges'].map(lambda x: "GUILTY PLEA" in x or "CONVICTED" in x).astype("string")

     df['Num'] = df.Charges.str.slice(0,3)
     df['Code'] = df.Charges.str.slice(4,9)
     df['CourtActionDate'] = df['Charges'].str.findall(r'\d{1,2}/\d\d/\d\d\d\d') # -> [x]
     df['Cite'] = df['Charges'].str.findall(r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}\({0,1}[A-Z]{0,1}\){0,1}\.{0,1}\d{0,1}') # -> [x]
     df['Cite'] = df['Cite'].map(lambda x: x[0] if len(x)>0 else x).astype("string") # [x] -> x

     df = df.dropna()

     df['CourtAction'] = df['Charges'].str.findall(r'(BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)')
     df = df.explode('CourtAction')
     df['CourtAction'] = df['CourtAction'].astype("string")
     df = df.reset_index()
     df = df.fillna('')

     # split at cite - different parse based on filing/disposition
     df['SegmentedCharges'] = df.Charges.map(lambda x: segmentCharge(x))


     df['Description'] = df.index.map(lambda x: (df['SegmentedCharges'].iloc[x])[0] if not df['Disposition'].iloc[x] else (df['SegmentedCharges'].iloc[x])[1]).astype("string")
     df['Description'] = df['Description'].str.strip()
     df['OtherSegment'] = df.index.map(lambda x: (df['SegmentedCharges'].iloc[x])[0] if df['Disposition'].iloc[x] else (df['SegmentedCharges'].iloc[x])[1]).astype("string")
     df['Category'] = df['OtherSegment'].str.findall(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)')
     df['TypeDescription'] = df['OtherSegment'].str.findall(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)')

     # VRR
     df['A_S_C_NON_DISQ'] = df['Description'].str.contains(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)')
     df['CERV_MATCH'] = df['Code'].str.contains(r'(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)')
     df['PARDON_DISQ_MATCH'] = df['Code'].str.contains(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)')
     df['PERM_DISQ_MATCH'] = df['Charges'].str.contains(r'(CM\d\d|CMUR)|(CAPITAL)')
     df['CERV'] = df.index.map(
          lambda x: df['CERV_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
               x] == True).astype("boolean")
     df['Pardon'] = df.index.map(
          lambda x: df['PARDON_DISQ_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
               x] == True).astype("boolean")
     df['Permanent'] = df.index.map(
          lambda x: df['PERM_DISQ_MATCH'].iloc[x] == True and df['A_S_C_NON_DISQ'].iloc[x] == False and df['Felony'].iloc[
               x] == True).astype("boolean")

     # type conversions / fix match overlap
     df['Category'] = df['Category'].map(lambda x: cleanCat(x)).astype("string")
     df['TypeDescription'] = df['TypeDescription'].map(lambda x: cleanCat(x)).astype("string")

     # df['Category'] = df['Category'].astype("category")

     df = df.drop(columns=['Sort','SegmentedCharges','OtherSegment','A_S_C_NON_DISQ','PARDON_DISQ_MATCH','PERM_DISQ_MATCH','CERV_MATCH'])

     try:
          df = df.drop(columns=['index'])
     except:
          pass

     has_num = df['Num'].astype("string").str.contains("0")
     df = df[has_num]

     df['Cite'] = df['Cite'].map(lambda x: '' if x == "[]" or [] else x)
     df['Cite'] = df['Cite'].astype("string")
     

     df['CourtActionDate'] = df['CourtActionDate'].map(lambda x: x[0] if len(x)>0 else pd.NaT) # [x]->x or []->nan
     df['CourtActionDate'] = df['CourtActionDate'].astype("string")

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

     if not multi and window != None:
          complete(conf, window)
     elif not multi:
          complete(conf)

     return df


## GETTERS


def getPDFText(path) -> str:
     try:
          doc = fitz.open(path)
     except:
          return ''
     text = ''
     for pg in doc:
          try:
               text += ' \n '.join(x[4].replace("\n"," ") for x in pg.get_text(option='blocks'))
          except:
               pass
     text = re.sub(r'(<image\:.+?>)','', text).strip()
     return text


def getCaseNumber(text: str):
     county = re.search(r'(County\: \d{2})', str(text)).group().replace("County: ","").strip()
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
          fees = pd.Series(actives, dtype="string")
          fees_noalpha = fees.str.replace(r'[^0-9|\.|\s|\$]', "", regex=True).str.strip()
          srows = fees.str.split(" ")
          drows = fees.str.replace(",","").str.split("$")        
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
          feesheet = feesheet.convert_dtypes()
          totalrdf = totalrdf.convert_dtypes()
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
     return b


## FETCH

def mark(in_path, out_path, no_write=False, window=None):

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

      output_query['RETRIEVED_ON'] = output_query.index.map(lambda x: time.time() if str(output_query.NAME[x]).replace(",","") in caseinfo.NAME.tolist() and output_query.RETRIEVED_ON[x] == "" else output_query.RETRIEVED_ON[x])
      output_query['RETRIEVED_ON'] = output_query['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
      output_query['CASES_FOUND'] = output_query['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
      if not no_write:
            with pd.ExcelWriter(out_path) as writer:
                    output_query.to_excel(writer, sheet_name="MarkedQuery", engine="openpyxl")
      if window != None:
            window.write_event_value('COMPLETE','MQ-COMPLETE')

      return output_query

def fetch(listpath, path, cID, uID, pwd, qmax=0, qskip=0, no_log=False, no_update=False, debug=False, window=None):
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
          print("Starting browser... Do not close while in progress!")
     driver = webdriver.Chrome(options=options)
     login(driver, cID, uID, pwd, window=window)
     if not no_log:
          print("Authentication successful. Fetching cases via party search...")

     # search, retrieve from URL, download to path
     for i, n in enumerate(query.index):
          if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                    login(driver, cID, uID, pwd, no_log, window=window)
          driver.implicitly_wait(2)
          results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], no_log=no_log, window=window)
          print(f'#{n}/{query.shape[0]} {query.NAME[n]} ({len(results)} records returned)')

          driver.implicitly_wait(2)
          if len(results) == 0:
               query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
               query_writer['CASES_FOUND'][n] = "0"
               if not no_log:
                    print(f"{query.NAME[n]}: Found no results.")
               continue

          if window != None:
               window.write_event_value('PROGRESS-TEXT',0)
               window.write_event_value('PROGRESS-TEXT-TOTAL',100)

               for i, url in enumerate(results):
                    window.write_event_value('PROGRESS-TEXT', i+1)
                    downloadPDF(driver, url)

          if window == None:
               for i, url in enumerate(tqdm.rich.tqdm(results)):
                    downloadPDF(driver, url)



          if not no_update:
               query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
               query_writer['CASES_FOUND'][n] = str(len(results))
               query_writer['RETRIEVED_ON'] = query_writer['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
               query_writer['CASES_FOUND'] = query_writer['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
               query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)
          if window != None:
               window.write_event_value('COMPLETE-MA',time.time())
     return [driver, query_writer]

def party_search(driver, name = "", party_type = "", ssn="", dob="", county="", division="", case_year="", filed_before="", filed_after="", no_log=False, debug=False, cID="", uID="", pwd="", window=None):
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
          no_log (bool, optional): Do not print logs.
          debug (bool, optional): Print detailed logs.
     
     Returns:
          URL list to PDFs
     """

     if "frmIndexSearchForm" not in driver.current_url:
          driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

     driver.implicitly_wait(5)

     has_window = False if window == "None" else True


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
               print("Successfully connected and logged into Alacourt!")

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

     driver.implicitly_wait(1)

     # submit search
     search_button = driver.find_element(by=By.ID,value="searchButton")

     driver.implicitly_wait(1)
     try:
          search_button.click()
     except:
          driver.implicitly_wait(5)
          time.sleep(5)

     if debug:
          print("Submitted party search form...")

     driver.implicitly_wait(1)

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
     except:
          pass

     if debug:
          print(f"Found {results_count} results, fetching URLs and downloading PDFs...")


     # get PDF links from each page
     pdflinks = []
     i = 0
     for i in range(0,pages):
          driver.implicitly_wait(0.5)
          hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
          for x in hovers:
               try:
                    a = x.get_attribute("href")
                    if "PDF" in a:
                         pdflinks.append(a)
               except:
                    pass
          driver.implicitly_wait(0.5)
          try:
               pager_select = Select(driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"))
               next_pg = int(pager_select.text) + 1
               driver.implicitly_wait(0.5)
          except:
               try:
                    driver.implicitly_wait(0.5)
                    time.sleep(0.5)
                    next_button = driver.find_element(by=By.ID, value = "ContentPlaceHolder1_dg_ibtnNext")
                    next_button.click()
               except:
                    continue
     return pdflinks

def downloadPDF(driver, url, no_log=False, cID="", uID="", pwd="", window=None):
     """
     With (driver), download PDF at (url)
     
     Args:
          driver (WebDriver): Google Chrome selenium.WebDriver() object
          url (TYPE): Description
          no_log (bool, optional): Description
     
     """
     if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx" and cID != "" and uID != "" and pwd != "":
          login(driver,cID=cID,uID=uID,pwd=pwd,window=window)
     a = driver.get(url)
     driver.implicitly_wait(0.5)


def login(driver, cID, uID="", pwd="", no_log=False, path="", window=None):
     """Login to Alacourt.com using (driver) and auth (cID, username, pwd) for browser download to directory at (path)
     
     Args:
          driver (WebDriver): Google Chrome selenium.WebDriver() object
          cID (str): Alacourt.com Customer ID
          uID (str): Alacourt.com User ID
          pwd (str): Alacourt.com Password
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
          print("Connecting to Alacourt...")


     login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

     if not no_log:
          print("Logging in...")

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
          print("Successfully connected and logged into Alacourt!")


     driver.implicitly_wait(1)

     return driver

def makeQueryTemplate(path):
     empty = pd.DataFrame(columns=["NAME", "PARTY_TYPE", "SSN", "DOB", "COUNTY", "DIVISION", "CASE_YEAR", "NO_RECORDS", "FILED_BEFORE", "FILED_AFTER", "RETRIEVED_ON", "CASES_FOUND"])
     empty.to_excel(path, sheet_name="queries")

def readPartySearchQuery(path, qmax=0, qskip=0, no_log=False, window=None):
     """Reads and interprets query template spreadsheets for `alacorder fetch` to queue from. Use headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE in an Excel spreadsheet, CSV, or JSON file to submit a list of queries for Alacorder to fetch.
     
     Args:
          path (TYPE): Description
          qmax (int, optional): Description
          qskip (int, optional): Description
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
          print(f"Field columns {clist} identified in query file.")

     query_out = query_out.fillna('')
     return [query_out, writer_df]

## LOGS


def echo_conf(input_path, make, output_path, overwrite, no_write, dedupe, no_prompt, compress, window=None):
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
     return uboth

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

def complete(conf, window=None):
     """
     Logs completion
     
     Args:
          conf (TYPE): Description
          *outputs: Description
     """

     elapsed = math.floor(time.time() - conf.TIME)
     if bool(conf.LOG) != False:
          print(f"Task completed in {elapsed} seconds.")
     if window != None:
          window.write_event_value('COMPLETE',f"Task completed in {elapsed} seconds.")


def log(msg, fg="", bold=False, italic=False, *conf):
     if isinstance(conf, pd.core.series.Series):
          try:
               if conf['LOG']:
                    print(msg)
          except:
               pass
     else:
          print(msg)


################### GRAPHICAL USER INTERFACE ##################





def loadgui():

     fetch_layout = [
           [sg.Text("""Collect case PDFs in bulk from Alacourt.com\nfrom a list of names or search parameters.""",font="Default 22",pad=(5,5))],
           [sg.Text("""Requires Google Chrome. Use column headers NAME, PARTY_TYPE,
SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel
spreadsheet to submit a list of queries for Alacorder to scrape. Each column
corresponds to a search field in Party Search. Missing columns and entries
will be left empty (i.e. if only the NAME's and CASE_YEAR's are relevant 
to the search, a file with two columns works too).""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(size=[30,10], key="SQ-INPUTPATH-",focus=True), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Text("Output Path: "), sg.InputText(size=[35,10], key="SQ-OUTPUTPATH-")],
           [sg.Text("Alacourt.com Credentials", font="Default 14")],
           [sg.Text("Customer ID: "), sg.Input(key="SQ-CUSTOMERID-",size=(20,1))],
           [sg.Text("User ID: "), sg.Input(key="SQ-USERID-",size=(20,1))],
           [sg.Text("Password: "), sg.InputText(key="SQ-PASSWORD-",password_char='*',size=(20,1))],
           [sg.Text("Max queries: "), sg.Input(key="SQ-MAX-", default_text="0", size=[5,1]),sg.Text("Skip from top: "), sg.Input(key="SQ-SKIP-", default_text="0",size=[5,1])],
           [sg.Button("Start Query",key="SQ",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]]
     archive_layout = [
           [sg.Text("""Create full text archives from a\ndirectory with PDF cases.""", font="Default 22", pad=(5,5))],
           [sg.Text("""Case text archives require a fraction of the storage capacity and processing
time used to process PDF directories. Before exporting your data to tables,
create an archive with supported file extensions .pkl.xz, .json, .csv, and .parquet.
Once archived, use your case text archive as an input for multitable or
single table export.""", pad=(5,5), auto_size_text=True)],
           [sg.Text("Input Path: "), sg.InputText(size=[30,10], key="MA-INPUTPATH-",focus=True), sg.FolderBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Text("Output Path: "), sg.InputText(size=[35,10], key="MA-OUTPUTPATH-")],
           [sg.Text("Skip Cases From: "), sg.Input(key="MA-SKIP-",size=[35,10])],
           [sg.Text("Max cases: "), sg.Input(key="MA-COUNT-", default_text="0", size=[10,1])],
           [sg.Checkbox("Try to Append",key="MA-APPEND-", default=False), sg.Checkbox("Allow Overwrite",default=True,key="MA-OVERWRITE-")],
           [sg.Button("Make Archive",button_color=("white","black"),key="MA",enable_events=True,bind_return_key=True, disabled_button_color=("grey","black"), mouseover_colors=("grey","black"), pad=(10,10))]] # "MA"
     table_layout = [
           [sg.Text("""Export data tables from\ncase archive or directory.""", font="Default 22", pad=(5,5))],
           [sg.Text("""Alacorder processes case detail PDFs and case text archives into data
tables suitable for research purposes. Export an Excel spreadsheet
with detailed cases information (cases), fee sheets (fees), and charges
information (charges, disposition, filing), or select a table choice to export to
a single-table format (.json, .csv, .parquet). Note: Create a case text archive
from your target PDF directory before exporting tables. Case text archives
can be processed into tables at a much faster rate and require
far less storage.""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(size=[30,10], key="TB-INPUTPATH-",focus=True), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Text("Output Path: "), sg.InputText(size=[35,10], key="TB-OUTPUTPATH-")],
           [sg.Radio("All Tables (.xlsx, .xls)", "TABLE", key="TB-ALL-", default=True), 
                 sg.Radio("Cases", "TABLE", key="TB-CASES-", default=False), 
                 sg.Radio("All Charges", "TABLE", key="TB-CHARGES-", default=False)], 
           [sg.Radio("Disposition Charges", "TABLE", key="TB-DISPOSITION-",default=False), sg.Radio("Filing Charges", "TABLE", key="TB-FILING-",default=False), sg.Radio("Fee Sheets","TABLE",key="TB-FEES-",default=False)],
           [sg.Text("Max cases: "), sg.Input(key="TB-COUNT-", default_text="0", size=[10,1]), sg.Checkbox("Allow Overwrite", key="TB-OVERWRITE-", default=True), sg.Checkbox("Compress", key="TB-COMPRESS-")],
           [sg.Button("Export Table",key="TB",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]] # "TB"
     append_layout = [
           [sg.Text("""Append case text archive with the contents\nof a case directory or archive.""", font="Default 22", pad=(5,5))],
           [sg.Text("""Case text archives require a fraction of the storage capacity and 
processing time used to process PDF directories. Before exporting your
data to tables, create an archive with a supported file extension: .pkl,
.pkl.xz, .json, .csv, or .parquet. Once archived, use your case text
archive as an input for table export.""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(size=[30,10], key="AA-INPUTPATH-",focus=True), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Text("Output Path: "), sg.InputText(size=[30,10], key="AA-OUTPUTPATH-"), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Button("Append Archives", key="AA",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"), bind_return_key=True)]] # "AA"
     mark_layout = [
           [sg.Text("""Mark query template with collected cases\nfrom input archive or directory.""", font="Default 22", pad=(5,5))],
           [sg.Text("""Use column headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION,
CASE_YEAR, and/or FILED_BEFORE in an Excel spreadsheet to submit a list of
queries for Alacorder to scrape. Each column corresponds to a search field
in Party Search. Missing columns and entries will be left empty (i.e. if
only the NAME's and CASE_YEAR's are relevant to the search, a file with two
columns works too).""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(size=[30,10], key="MQ-INPUTPATH-",focus=True), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Text("Output Path: "), sg.InputText(size=[30,10], key="MQ-OUTPUTPATH-"), sg.FileBrowse(button_color=("white","black"), pad=(5,5))],
           [sg.Button("Mark Query",key="MQ",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]] # "MQ"
     about_layout = [
           [sg.Text(f"""\n{fname}""",font="Courier 30", pad=(5,5))],[sg.Text("""Alacorder retrieves and processes\nAlacourt case detail PDFs into data\ntables and archives.""",font="Default 25", pad=(5,5))],
           [sg.Text(
                 """
     1.  fetch - Retrieve case detail PDFs in bulk from Alacourt.com.
     2.  archive - Create full text archives from PDF directory.
     3.  table - Export data tables from case archive or directory.
     4.  append - Append contents of one archive to another.
     5.  mark - Mark completed cases in existing output query.""", font="Default 14")],
           [sg.Text("""View documentation, source code, and latest updates at\ngithub.com/sbrobson959/alacorder.\n\n© 2023 Sam Robson""", font="Default 14")],
           ] # "ABOUT"
     tabs = sg.TabGroup(expand_x=True, expand_y=False, size=[0,0], font="Courier",layout=[
                                     [sg.Tab("fetch", layout=fetch_layout, pad=(2,2))],
                                     [sg.Tab("archive", layout=archive_layout, pad=(2,2))],            
                                     [sg.Tab("table", layout=table_layout, pad=(2,2))],
                                     [sg.Tab("append", layout=append_layout, pad=(2,2))],
                                     [sg.Tab("mark", layout=mark_layout, pad=(2,2))],
                                     [sg.Tab("about", layout=about_layout, pad=(2,2))]])
     layout = [[sg.Text(f"ALACORDER 78.4",font="Courier 22", pad=(5,5))],[tabs],
     [sg.ProgressBar(100, size=[5,10], expand_y=False, orientation='h', expand_x=True, key="PROGRESS", bar_color="black")],
     [sg.Multiline(expand_x=True,expand_y=True,background_color="black",reroute_stdout=True,pad=(5,5),font="Courier 11",write_only=True,autoscroll=True,no_scrollbar=True,size=[None,3],border_width=0)]]

     window = sg.Window(title="alacorder", layout=layout, grab_anywhere=True, resizable=True, size=[510,525])
     progress_total = 100
     virgin = True
     while True:
           event, values = window.read()
           if event in ["Exit","Quit",sg.WIN_CLOSED]:
                 window.close()
                 break
           elif "TOTAL" in event and "PROGRESS" in event:
               window['PROGRESS'].update(max=values[event],current_count=0)
           elif "PROGRESS" in event and "TOTAL" not in event:
               window["PROGRESS"].update(current_count=values[event])
           elif "COMPLETE" in event:
               window['AA'].update(disabled=False)
               window['SQ'].update(disabled=False)
               window['MA'].update(disabled=False)
               window['TB'].update(disabled=False)
               window['MQ'].update(disabled=False)
               window['MA'].update(disabled=False)
               window['PROGRESS'].update(current_count=0, max=100)
               sg.popup("Alacorder completed the task.")
               virgin = True
               continue
           elif event == "TB":
                 try:
                         assert window["TB-INPUTPATH-"].get() != "" and window["TB-OUTPUTPATH-"].get() != ""
                 except:
                         continue
                 if bool(window["TB-ALL-"]) == True:
                         tabl = "all"
                 elif bool(window["TB-CASES-"]) == True:
                         tabl = "cases"
                 elif bool(window["TB-CHARGES-"]) == True:
                         tabl = "charges"
                 elif bool(window["TB-DISPOSITION-"]) == True:
                         tabl = "disposition"
                 elif bool(window["TB-FILING-"]) == True:
                         tabl = "filing"
                 elif bool(window["TB-FEES-"]) == True:
                         tabl = "fees"
                 else:
                         continue
                 try:
                         try:
                               count = int(window['TB-COUNT-'].get().strip())
                         except:
                               count = 0
                         cf = setpaths(window['TB-INPUTPATH-'].get(), window['TB-OUTPUTPATH-'].get(), count=count,table=tabl,overwrite=window['TB-OVERWRITE-'].get(),compress=window['TB-COMPRESS-'].get(),no_prompt=True,log=True, debug=True,archive=False,window=window)
                         virgin = False
                         window['TB'].update(disabled=True)
                         threading.Thread(target=init,args=(cf,window), daemon=True).start()
                 except:
                         continue
           elif event == "MA":
                  try:
                        count = int(window['MA-COUNT-'].get().strip())
                  except:
                        count = 0
                  aa = setpaths(window['MA-INPUTPATH-'].get(),window['MA-OUTPUTPATH-'].get(),count=count, archive=True,overwrite=window['MA-OVERWRITE-'].get(), append=window['MA-APPEND-'].get(), no_prompt=True,log=True,window=window)
                  virgin = False
                  window['MA'].update(disabled=True)
                  threading.Thread(target=archive, args=(aa, window), daemon=True).start()
                  continue
           elif event == "SQ":
                 try:
                         assert window["SQ-INPUTPATH-"].get() != ""
                         pwd = window["SQ-PASSWORD-"].get()
                         try:
                               sq_max = int(window['SQ-MAX-'].get().strip())
                               sq_skip = int(window['SQ-SKIP-'].get().strip())
                         except:
                               sq_max = 0
                               sq_skip = 0
                         virgin = False
                         window['SQ'].update(disabled=True)
                         threading.Thread(target=fetch, args=(window['SQ-INPUTPATH-'].get(),window['SQ-OUTPUTPATH-'].get(),window['SQ-CUSTOMERID-'].get(),window['SQ-USERID-'].get(),pwd,sq_max,sq_skip,False,False,False,window), daemon=True).start()
                         continue
                 except:
                         continue
           elif event == "MQ":
                 try:
                         assert window["MQ-INPUTPATH-"].get() != ""
                         virgin = False
                         window['MQ'].update(disabled=True)
                         threading.Thread(target=mark, args=(window['MQ-INPUTPATH-'].get(),window['MQ-OUTPUTPATH-'].get()), kwargs={'window':window},daemon=True)
                         continue
                 except:
                         continue
           elif event == "AA":
                 try:
                         assert window["AA-INPUTPATH-"].get() != ""
                         virgin = False
                         window['AA'].update(disabled=True)
                         threading.Thread(target=append_archive, args=(window['MQ-INPUTPATH-'].get(),window['MQ-OUTPUTPATH-'].get()), kwargs={'window':window},daemon=True)
                         continue
                 except:
                         print("Error: check configuration.")
                         window['AA'].update(disabled=False)
                         window['SQ'].update(disabled=False)
                         window['MA'].update(disabled=False)
                         window['TB'].update(disabled=False)
                         window['MQ'].update(disabled=False)
                         window['MA'].update(disabled=False)
                         continue
           else:
                 pass

################### COMMAND LINE INTERFACE ##################


@click.group(invoke_without_command=True)
@click.version_option(f"{version}", package_name="alacorder")
@click.pass_context
def cli(ctx):
    """
    ALACORDER beta 78.4

    Alacorder retrieves case detail PDFs from Alacourt.com and processes them into text archives and data tables suitable for research purposes.

    """
    if ctx.invoked_subcommand is None:
        loadgui()

@cli.command(name="start", help="Launch graphical user interface")
def cli_start():
    loadgui()


@cli.command(name="table", help="Export data tables from archive or directory")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=title(),
              help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=both(), help="Path to output table (.xls, .xlsx, .csv, .json, .dta)")
@click.option('--table', '-t', help="Table export choice (cases, fees, charges, disposition, filing, or all)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (Excel files not supported)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-prompt','-s', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--no-batch','-b', default=True, is_flag=True, help="Process all inputs as one batch")
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def cli_table(input_path, output_path, count, table, overwrite, log, no_write, no_prompt, debug, no_batch, compress): 

    ogtable = table
    archive = False
    show_options_menu = False

    log = not log 

    show_options_menu = True if no_prompt == False and overwrite == False and log == True and no_write == False and no_prompt == False and debug == False and no_batch == False and compress == False else False

    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.secho(inputs.ECHO, italic=True)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = setoutputs(output_path,archive=False)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, italic=True)
    if not outputs.GOOD:
        raise Exception("Invalid output path!")
    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm(click.style("Existing file at output path will be written over! Continue?",bold=True)):
                pass
            else:
                raise Exception("Existing file at output path!")

    # prompt table
    if outputs.MAKE == "multiexport" and table != "cases" and table != "fees" and table != "charges" and table != "disposition" and table != "filing":
        table = "all"
    if outputs.MAKE == "singletable" and table != "cases" and table != "fees" and table != "charges" and table != "disposition" and table != "filing":
        if no_prompt:
            raise Exception("Invalid/missing table selection!")
        else:
            pick = click.prompt(pick_table_only())  # add str
            if pick == "B" or pick == "cases":
                table = "cases"
            elif pick == "C" or pick == "fees":
                table = "fees"
            elif pick == "D" or pick == "charges":
                table = "charges"
            elif pick == "E" or pick == "disposition":
                table = "disposition"
            elif pick == "F" or pick == "filing":
                table = "filing"
            else:
                click.secho("Invalid table selection!", bold=True)

    # finalize config
    cf = set(inputs, outputs, count=count, table=table, overwrite=overwrite, log=log, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)

    if cf.DEBUG:
        click.echo(cf)

    if cf.MAKE == "multiexport" and cf.TABLE == "all":
        o = cases(cf)
    if cf.TABLE == "fees":
        o = fees(cf)
    if cf.TABLE == "charges" or cf.TABLE == "disposition" or cf.TABLE == "filing":
        o = charges(cf)
    if cf.TABLE == "cases":
        o = cases(cf)

@cli.command(name="archive", help="Create full text archive from case PDFs")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=title(), help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=just_archive(), help="Path to archive (.pkl.xz, .json.zip, .csv.zip, .parquet)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--dedupe / --ignore','dedupe', default=True, is_flag=True, help="Remove duplicate cases from archive outputs")
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--append', '-a', default=False, help="Append to archive at output path", is_flag=True, show_default=False)
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.option('--no-batch','-b', default=True, is_flag=True, help="Process all inputs as one batch")
@click.option('--skip','-skip', default='', type=click.Path(), help="Skip paths in archive at provided skip path")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def cli_archive(input_path, output_path, count, overwrite, append, dedupe, log, no_write, no_batch, no_prompt, debug, compress, skip):

    # show_options_menu = False
    table = ""

    log = not log

    if append and skip == "":
        skip = output_path
    if append:
        overwrite = True
        no_prompt = True


    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.secho(inputs.ECHO, italic=True)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    if append:
        overwrite = True

    # outputs - configure and log
    outputs = setoutputs(output_path,archive=True)
    if debug:
        click.echo(outputs)
    if log:
        click.secho(outputs.ECHO, italic=True)

    if not outputs.GOOD:
        raise Exception("Invalid output path!")

    if outputs.OUTPUT_EXT != ".xlsx" and outputs.OUTPUT_EXT != ".xls" and outputs.OUTPUT_EXT != ".dta" and outputs.OUTPUT_EXT != ".json" and outputs.OUTPUT_EXT != ".csv" and outputs.OUTPUT_EXT != ".zip" and outputs.OUTPUT_EXT != ".pkl" and outputs.OUTPUT_EXT != ".xz" and outputs.OUTPUT_EXT != ".parquet":
        raise Exception("Bad format!")

    # skip paths in provided archive
    if skip != "" and inputs.IS_FULL_TEXT == False:
        try:
            if log or debug:
                click.secho(f"Collecting paths from archive at --skip/--append path...",italic=True)
            skip_paths = read(skip)
            skip_paths = skip_paths['Path'].tolist()
        except:
            if debug:
                click.echo("Key Error when reading --skip/--append archive!")
            pass
        match_skip = pd.Series(inputs.QUEUE).map(lambda x: x not in skip_paths)
        inputs.QUEUE = inputs.QUEUE[match_skip]
        len_dif = inputs.FOUND - inputs.QUEUE.shape[0]
        if len(skip_paths) > 0 and log or debug:
                click.secho(f"Identified {len_dif} paths already in archive at path --skip/--append.")
    # append priority over overwrite
    if append and outputs.EXISTING_FILE == True:
        overwrite = True

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm("Existing file at output path will be written over! Continue?"):
                pass
            else:
                raise Exception("Existing file at output path!")


    cf = set(inputs, outputs, count=count, table="", overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress, append=append)

    if debug:
        click.echo(cf)

    o = archive(cf)

# fetch

@cli.command(name="fetch", help="Fetch cases from Alacourt.com with input query spreadsheet headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE.")
@click.option("--input-path", "-in", "listpath", required=True, prompt="Path to query table", help="Path to query table/spreadsheet (.xls, .xlsx, .csv, .json)", type=click.Path())
@click.option("--output-path", "-out", "path", required=True, prompt="PDF download path", type=click.Path(), help="Desired PDF output directory")
@click.option("--customer-id", "-c","cID", required=True, prompt="Alacourt Customer ID", help="Customer ID on Alacourt.com")
@click.option("--user-id", "-u","uID", required=True, prompt="Alacourt User ID", help="User ID on Alacourt.com")
@click.option("--password", "-p","pwd", required=True, prompt="Alacourt Password", help="Password on Alacourt.com", hide_input=True)
@click.option("--max", "-max","qmax", required=False, type=int, help="Maximum queries to conduct on Alacourt.com",default=0)
@click.option("--skip", "-skip", "qskip", required=False, type=int, help="Skip entries at top of query file",default=0)
@click.option("--no-log","-nl", is_flag=True, default=False, help="Do not print logs to console")
@click.option("--no-update","-w", is_flag=True, default=False, help="Do not update query template after completion")
@click.option("--ignore-complete","-g", is_flag=True, default=False, help="Ignore initial completion status in query template")
@click.option("--debug","-d", is_flag=True, default=False, help="Print detailed runtime information to console")
def cli_fetch(listpath, path, cID, uID, pwd, qmax, qskip, no_log, no_update, ignore_complete, debug):
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
        no_log (bool, optional): Do not print logs to console
        no_update (bool, optional): Do not update input query file with completion status
        debug (bool, optional): Print detailed logs to console

    Returns:
        [driver, query_out, query_writer]:
            driver[0]: Google Chrome WebDriver() object 
            query_out[1]: (pd.Series) Fetchr queue
            query_writer[2]: (pd.DataFrame) Updated input query file
    """
    if debug:
        sys.tracebacklimit = 10
    rq = readPartySearchQuery(listpath, qmax, qskip, no_log)

    query = pd.DataFrame(rq[0]) # for fetchr - only search columns
    query_writer = pd.DataFrame(rq[1]) # original sheet for write completion 
    incomplete = query.RETRIEVED_ON.map(lambda x: True if x == "" else False)
    query = query[incomplete]

    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {
        "download.default_directory": path, #Change default directory for downloads
        "download.prompt_for_download": False, #To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
    })

    driver = webdriver.Chrome(options=options)

    # start browser session, auth
    if not no_log:
        click.secho("Starting browser... Do not close while in progress!",bold=True)

    login(driver, cID=cID, uID=uID, pwd=pwd, no_log=no_log)

    if not no_log:
        click.secho("Authentication successful. Fetching cases via party search...",bold=True)

    for i, n in enumerate(query.index):
        if debug:
            click.secho(driver.current_url)
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
                login(driver, cID=cID, uID=uID, pwd=pwd, no_log=no_log)
        driver.implicitly_wait(4)
        results = party_search(driver, name=query.NAME[n], party_type=query.PARTY_TYPE[n], ssn=query.SSN[n], dob=query.DOB[n], county=query.COUNTY[n], division=query.DIVISION[n], case_year=query.CASE_YEAR[n], filed_before=query.FILED_BEFORE[n], filed_after=query.FILED_AFTER[n], no_log=no_log, debug=debug)
        driver.implicitly_wait(4)
        if len(results) == 0:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = "0"
            if not no_log:
                click.secho(f"Found no results for query: {query.NAME[n]}")
            continue
        for url in tqdm.rich.tqdm(results, desc=f"#{n}: {query.NAME[n]}"):
            downloadPDF(driver, url)
            driver.implicitly_wait(0.5)
            time.sleep(1)
        if not no_update:
            query_writer['RETRIEVED_ON'][n] = str(math.floor(time.time()))
            query_writer['CASES_FOUND'][n] = str(len(results))
            query_writer.to_excel(listpath,sheet_name="PartySearchQuery",index=False)

@cli.command(name="mark", help="Mark query template sheet with cases found in archive or PDF directory input")
@click.option("--input-path", "-in", "in_path", required=True, prompt="Path to archive / PDF directory", help="Path to query template spreadsheet (.csv, .xls(x), .json)", type=click.Path())
@click.option("--output-path", "-out", "out_path", required=True, prompt="Query template spreadsheet path", type=click.Path(), help="Path to output query template spreadsheet")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
def cli_mark(in_path, out_path, no_write=False):

    # get input text, names, dob
    input_archive = read(in_path)
    mapinputs = setinputs(input_archive)
    mapoutputs = setoutputs()
    mapconf = set(mapinputs, mapoutputs, no_write=True, no_prompt=True, overwrite=True, log=False, debug=True)

    caseinfo = map(mapconf, lambda x: x, getCaseNumber, getName, getDOB, names=['TEXT','CASE','NAME','DOB'])

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
    output_query['CASES_FOUND'] = output_query['CASES_FOUND'].map(lambda x: pd.to_numeric(x))
    output_query['RETRIEVED_ON'] = output_query['RETRIEVED_ON'].map(lambda x: pd.to_numeric(x))
    if not no_write:
        with pd.ExcelWriter(out_path) as writer:
            output_query.to_excel(writer, sheet_name="MarkedQuery", engine="openpyxl")
    return output_query


@cli.command(name="append", help="Append one case text archive to another")
@click.option("--input-path", "-in", "in_path", required=True, prompt="Path to archive / PDF directory", help="Path to input archive", type=click.Path())
@click.option("--output-path", "-out", "out_path", required=True, prompt="Path to output archive", type=click.Path(), help="Path to output archive")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
def cli_append(in_path, out_path, no_write=False):
    print("Appending archives...")
    input_archive = read(in_path)
    output_archive = read(out_path)
    new_archive = pd.concat([output_archive, input_archive], ignore_index=True)
    if not no_write:
        cin = setinputs(input_archive)
        cout = setoutputs(out_path)
        conf = set(cin, cout)
        conf.OVERWRITE = True
        conf.NO_PROMPT = True
        write(conf, new_archive)
    return new_archive


if __name__ == "__main__":
    cli()

