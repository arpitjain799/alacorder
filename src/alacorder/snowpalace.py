'''
    ___  _  __  _   _   __  ___   _   __    _    __  ___    
  ,' _/ / |/ /,' \\ ///7/ / / o |.' \\ / /  .' \\ ,'_/ / _/    
 _\\ `. / || // o || V V / / _,'/ o // /_ / o // /_ / _/     
/___,'/_/|_/ |_,' |_n_,' /_/  /_n_//___//_n_/ |__//___/     
                                                                                                 
'''

# snowpalace alpha2
# alacorder on polars
# Sam Robson
# Dependencies: click, polars, pandas, openpyxl, xlsxwriter, xlsx2csv, tqdm, PyMuPdf
# Requires Python >=3.9

name = "SNOWPALACE"
version = "a2.1"

import click, fitz, tqdm, os, sys, time, glob, inspect, math, re, warnings, xlsxwriter, threading, platform
import polars as pl
import pandas as pd


fname = f"{name} {version}"
fshort_name = f"{name} {version.rsplit('.')[0]}"
warnings.filterwarnings('ignore')
pl.Config.set_tbl_rows(50)
pl.Config.set_fmt_str_lengths(100)
pl.Config.set_tbl_cols(10)
pd.set_option("mode.chained_assignment", None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.min_rows', 50)
pd.set_option('display.max_colwidth', 25)
pd.set_option('display.precision',2)

################### GRAPHICAL USER INTERFACE ##################

def loadgui():
     import PySimpleGUI as sg
     psys = platform.system()
     plat = platform.platform()
     if "Darwin" in (plat, psys) or "macOS" in (plat, psys):
          inferred_platform = "mac"
     elif "Windows" in (plat, psys):
          inferred_platform = "windows"
     elif "Linux" in (plat, psys):
          inferred_platform = "linux"
     else:
          inferred_platform = None
     if inferred_platform == "mac":
          HEADER_FONT = "Default 22"
          LOGO_FONT = "Courier 20"
          BODY_FONT = "Default 12"
          WINDOW_RESIZE = False
          WINDOW_SIZE = [480, 500]
     elif inferred_platform == "windows":
          HEADER_FONT = "Default 14"
          LOGO_FONT = "Courier 15"
          BODY_FONT = "Default 10"
          WINDOW_RESIZE = True
          WINDOW_SIZE = [550, 600]
     elif inferred_platform == "linux":
          HEADER_FONT = "Default 14"
          LOGO_FONT = "Courier 15"
          BODY_FONT = "Default 10"
          WINDOW_RESIZE = True
          WINDOW_SIZE = [550, 600]
     else:
          HEADER_FONT = "Default 14"
          LOGO_FONT = "Courier 15"
          BODY_FONT = "Default 10"
          WINDOW_RESIZE = True
          WINDOW_SIZE = [550, 600]
     sg.theme("DarkBlack")
     sg.set_options(font=BODY_FONT)
     archive_layout = [
           [sg.Text("""Create full text archives from a\ndirectory with PDF cases.""", font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""Case text archives require a fraction of the storage capacity and processing
time used to process PDF directories. Before exporting your data to tables,
create an archive with supported file extensions .pkl.xz, .json, .csv, and
.parquet. Once archived, use your case text archive as an input for
multitable or single table export.""", pad=(5,5))],
           [sg.Text("Input Directory: "), sg.InputText(tooltip="PDF directory or full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)",size=[25,1], key="MA-INPUTPATH-",focus=True), sg.FolderBrowse(button_text="Select Folder", button_color=("white","black"))],
           [sg.Text("Output Path: "), sg.InputText(tooltip="Output archive file path (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[39,1], key="MA-OUTPUTPATH-")],
           [sg.Text("Skip Cases From: "), sg.Input(tooltip="Skip all input cases found in PDF directory or archive (.parquet, .pkl, .pkl.xz, .json, .csv)", key="MA-SKIP-",size=[24,1],pad=(0,10))],
           [sg.Text("Max cases: "), sg.Input(key="MA-COUNT-", default_text="0", size=[5,1]), sg.Checkbox("Allow Overwrite",default=True,key="MA-OVERWRITE-"), sg.Checkbox("Try to Append",key="MA-APPEND-", default=False)],
           [sg.Button("Make Archive",button_color=("white","black"),key="MA",enable_events=True,bind_return_key=True, disabled_button_color=("grey","black"), mouseover_colors=("grey","black"), pad=(10,10))]] # "MA"
     table_layout = [
           [sg.Text("""Export data tables from\ncase archive or directory.""", font=HEADER_FONT, pad=(5,5))],
           [sg.Text("""Alacorder processes case detail PDFs and case text archives into data
tables suitable for research purposes. Export an Excel spreadsheet
with detailed cases information (cases), fee sheets (fees), and
charges information (charges), or select a table
choice to export to a single-table format.""", pad=(5,5))],
           [sg.Text("Input Path: "), sg.InputText(tooltip="PDF directory or full text archive (.parquet, .pkl, .pkl.xz, .json, .csv)", size=[28,10], key="TB-INPUTPATH-",focus=True), sg.FolderBrowse(button_text="Select Folder", button_color=("white","black"))],
           [sg.Text("Output Path: "), sg.InputText(tooltip="Multitable export (.xlsx, .xls) or single-table export (.xlsx, .xls, .json, .csv, .dta, .parquet)", size=[39,10], key="TB-OUTPUTPATH-")],
           [sg.Radio("All Tables (.xlsx, .xls)", "TABLE", key="TB-ALL-", default=True), 
                 sg.Radio("Cases", "TABLE", key="TB-CASES-", default=False), 
                 sg.Radio("Charges", "TABLE", key="TB-CHARGES-", default=False), 
                 sg.Radio("Fee Sheets","TABLE",key="TB-FEES-",default=False)],
           [sg.Text("Max cases: "), sg.Input(key="TB-COUNT-", default_text="0", size=[5,1]), sg.Checkbox("Allow Overwrite", key="TB-OVERWRITE-", default=True), sg.Checkbox("Compress", key="TB-COMPRESS-")],
           [sg.Button("Export Table",key="TB",button_color=("white","black"), pad=(10,10), disabled_button_color=("grey","black"), mouseover_colors=("grey","black"),bind_return_key=True)]] # "TB"

     about_layout = [
           [sg.Text("""    ___  _  __  _   _   __  ___   _   __    _    __  ___    
  ,' _/ / |/ /,' \\ ///7/ / / o |.' \\ / /  .' \\ ,'_/ / _/    
 _\\ `. / || // o || V V / / _,'/ o // /_ / o // /_ / _/     
/___,'/_/|_/ |_,' |_n_,' /_/  /_n_//___//_n_/ |__//___/     
                                                                                                 

           """,font="Courier")],
           [sg.Text("""Alacorder retrieves and processes\nAlacourt case detail PDFs into data\ntables and archives.""",font=BODY_FONT, pad=(5,5))],
           [sg.Text("""View documentation, source code, and latest updates at\ngithub.com/sbrobson959/alacorder.\n\n© 2023 Sam Robson""", font=BODY_FONT)],
           ] # "ABOUT"
     tabs = sg.TabGroup(expand_x=True, expand_y=False, size=[0,0], font="Courier",layout=[
                                     [sg.Tab("archive", layout=archive_layout, pad=(2,2))],            
                                     [sg.Tab("table", layout=table_layout, pad=(2,2))],
                                     [sg.Tab("about", layout=about_layout, pad=(2,2))]])
     layout = [[sg.Text(fshort_name,font=LOGO_FONT, pad=(5,5))],[tabs],
              [sg.ProgressBar(100, size=[5,10], expand_y=False, orientation='h', expand_x=True, key="PROGRESS", bar_color="black")],
              [sg.Multiline(expand_x=True,expand_y=True,background_color="black",reroute_stdout=True,pad=(5,5),font="Courier 11",write_only=True,autoscroll=True,no_scrollbar=True,size=[None,4],border_width=0)]]
     window = sg.Window(title=name, layout=layout, grab_anywhere=True, resizable=WINDOW_RESIZE, size=WINDOW_SIZE)
     virgin = True
     while True:
           event, values = window.read()
           if event in ("Exit","Quit",sg.WIN_CLOSED):
                 window.close()
                 break
           elif "TOTAL" in event and "PROGRESS" in event:
               window['PROGRESS'].update(max=values[event],current_count=0)
           elif "PROGRESS" in event and "TOTAL" not in event:
               window["PROGRESS"].update(current_count=values[event])
           elif "COMPLETE" in event:
               window['MA'].update(disabled=False)
               window['TB'].update(disabled=False)
               window['PROGRESS'].update(current_count=0, max=100)
               sg.popup("Alacorder completed the task.")
               virgin = True
               continue
           elif event == "TB":
                 if window["TB-INPUTPATH-"].get() == "" or window["TB-OUTPUTPATH-"].get() == "":
                    sg.popup("Check configuration and try again.")
                 if bool(window["TB-ALL-"]) == True:
                         tabl = "all"
                 elif bool(window["TB-CASES-"]) == True:
                         tabl = "cases"
                 elif bool(window["TB-CHARGES-"]) == True:
                         tabl = "charges"
                 elif bool(window["TB-FEES-"]) == True:
                         tabl = "fees"
                 else:
                         continue
                 try:
                         try:
                               count = int(window['TB-COUNT-'].get().strip())
                         except:
                               count = 0
                         try:
                               cf = set(window['TB-INPUTPATH-'].get(), window['TB-OUTPUTPATH-'].get(), count=count,table=tabl,overwrite=window['TB-OVERWRITE-'].get(),compress=window['TB-COMPRESS-'].get(),no_prompt=True, debug=True,archive=False,window=window)
                         except:
                               print("Check configuration and try again.")
                               window['TB'].update(disabled=False)
                               continue
                         virgin = False
                         window['TB'].update(disabled=True)
                         threading.Thread(target=init,args=(cf,window), daemon=True).start()
                         continue
                 except:
                         print("Check configuration and try again.")
                         window['TB'].update(disabled=False)
                         continue
           elif event == "MA":
                  if window["MA-INPUTPATH-"].get() == "" or window["MA-OUTPUTPATH-"].get() == "":
                        sg.popup("Check configuration and try again.")
                        window['MA'].update(disabled=False)
                        continue
                  try:
                        count = int(window['MA-COUNT-'].get().strip())
                  except:
                        count = 0
                  try:
                  		aa = set(window['MA-INPUTPATH-'].get(),window['MA-OUTPUTPATH-'].get(),count=count, archive=True,overwrite=window['MA-OVERWRITE-'].get(), append=window['MA-APPEND-'].get(), no_prompt=True,window=window)
                  except:
                        sg.popup("Check configuration and try again.")
                        window['MA'].update(disabled=False)
                        continue
                  virgin = False
                  window['MA'].update(disabled=True)
                  threading.Thread(target=archive, args=(aa, window), daemon=True).start()
                  continue
           else:
                 pass

################### COMMAND LINE INTERFACE ##################

@click.group(invoke_without_command=True)
@click.version_option(f"{version}", package_name=name)
@click.pass_context
def cli(ctx):
     """SNOWPALACE alpha 2
     * alacorder on polars
     * Sam Robson
     * Dependencies: polars, pandas, openpyxl, xlsxwriter, xlsx2csv, tqdm, PyMuPdf, PySimpleGUI
     * Requires Python >=3.9
     """
     if ctx.invoked_subcommand == None:
     	loadgui()

@cli.command(name="table", help="Export data tables from archive or directory")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt="Input Path", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt="Output Path")
@click.option('--table', '-t', default='', help="Table (all, cases, fees, charges)")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (Excel files not supported)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-prompt','-s', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--debug','-d', default=False, is_flag=True, help="Print debug logs to console")
@click.version_option(package_name='alacorder', prog_name=name, message='%(prog)s beta %(version)s')
def cli_table(input_path, output_path, count, table, overwrite, no_write, no_prompt, debug, compress): 
    cf = set(input_path, output_path, count=count, table=table, overwrite=overwrite,  no_write=no_write, no_prompt=no_prompt, debug=debug, compress=compress)
    if cf['DEBUG']:
        print(cf)
    o = init(cf)
    return o

@cli.command(name="archive", help="Create full text archive from case PDFs")
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt="PDF directory or archive input")
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt="Path to archive output")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.version_option(package_name=name.lower(), prog_name=name.upper(), message='%(prog)s %(version)s')
def cli_archive(input_path, output_path, count, overwrite, no_write, no_prompt, debug, compress):
    cf = set(input_path, output_path, archive=True, count=count, overwrite=overwrite, no_write=no_write, no_prompt=no_prompt, debug=debug, compress=compress)
    if debug:
        click.echo(cf)
    o = archive(cf)
    return o

def set(inputs, outputs=None, count=0, table='', archive=False, no_prompt=True, debug=False, overwrite=False, no_write=False, fetch=False, cID='', uID='', pwd='', qmax=0, qskip=0, append=False, mark=False, compress=False, window=None, force=False, init=False):
     # flag checks
     good = True
     append = False if archive else append
     outputs = None if no_write else outputs
     no_write = True if outputs == None else no_write
     found = 0

     # check output
     if no_write:
          outputext = "none"
          existing_output = False
     elif os.path.isdir(outputs):
          outputext = "directory"
          existing_output = False
     elif os.path.isfile(outputs):
          assert overwrite or append # Existing file at output path!
          outputext = os.path.splitext(outputs)[1]
          existing_output = True
     else:
          outputext = os.path.splitext(str(outputs))[1]
          existing_output = False

     # flag checks - compression
     if outputext == ".zip":
          outputs, outputext = os.path.splitext(outputs)
     if outputext in (".xz",".parquet",".zip"):
          compress = True

     #flag checks - output extension
     support_multitable = True if outputext in (".xls",".xlsx","none") else False
     support_singletable = True if outputext in (".xls",".xlsx","none",".json",".dta",".parquet", ".csv") else False
     support_archive = True if outputext in (".xls",".xlsx",".csv",".parquet",".zip",".json",".dta",".pkl",".xz",".zip","none") else False
     compress = False if outputext in (".xls",".xlsx","none") else compress
     assert force or outputext in (".xls",".xlsx",".csv",".parquet",".zip",".json",".dta",".pkl",".xz",".zip","none","directory")
     if support_multitable == False and archive == False and fetch == False and table not in ("cases","charges","fees"):
          raise Exception("Single table export choice required! (cases, charges, fees)")
     if archive and append and existing_output and not no_write:
          try:
               old_archive = read(outputs)
          except:
               print("Append failed! Archive at output path could not be read.")

     ## DIRECTORY INPUTS
     if os.path.isdir(inputs):
          queue = glob.glob(inputs + '**/*.pdf', recursive=True)
          found = len(queue)
          assert force or found > 0
          is_full_text = False
          itype = "directory"

     ## FILE INPUTS
     elif os.path.isfile(inputs):
          queue = read(inputs)
          found = queue.shape[0]
          fetch = True if os.path.splitext(inputs)[1] in (".xls",".xlsx") else False
          is_full_text = True
          itype = "query" if os.path.splitext(inputs)[1] in (".xls",".xlsx") else "archive"

     ## OBJECT INPUTS 
     elif isinstance(inputs, pl.dataframe.frame.DataFrame):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = inputs
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pl.series.series.Series):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = inputs
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pd.core.frame.DataFrame):
          assert force or "AllPagesText" in inputs.columns
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = pl.from_pandas(inputs)
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     elif isinstance(inputs, pd.core.series.Series):
          assert force or "ALABAMA" in inputs['AllPagesText'][0]
          queue = pl.DataFrame({'AllPagesText':pl.from_pandas(inputs)})
          found = queue.shape[0]
          is_full_text = True
          itype = "object"
     else:
          raise Exception("Failed to determine input type.")

     if count == 0:
          count = found
     if count > found:
          count = found
     if found > count:
          queue = queue[0:count]

     out = {
          'QUEUE': queue,
          'INPUTS': inputs,
          'NEEDTEXT': bool(not is_full_text),
          'INPUT_TYPE': itype,
          'FOUND': found,
          'COUNT': count,
          'OUTPUT_PATH': outputs,
          'OUTPUT_EXT': outputext,

          'TABLE': table,
          'SUPPORT_MULTITABLE': support_multitable,
          'SUPPORT_SINGLETABLE': support_singletable,
          'SUPPORT_ARCHIVE': support_archive,

          'ARCHIVE': archive,
          'APPEND': append,
          'MARK': mark,

          'FETCH': fetch,
          'ALA_CUSTOMER_ID': cID,
          'ALA_USER_ID': uID,
          'ALA_PASSWORD': pwd,
          'FETCH_SKIP': qskip,
          'FETCH_MAX': qmax,

          'COMPRESS': compress,
          'NO_WRITE': no_write,
          'NO_PROMPT': no_prompt,
          'OVERWRITE': overwrite,
          'EXISTING_OUTPUT': existing_output,
          'DEBUG': debug,
          'WINDOW': window
     }
     if init:
          init(out)
     return out

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

def archive(cf, window=None):
     a = read(cf, window)
     write(cf, a)
     if window:
          window.write_event_value("COMPLETE-MA",True)
     return a

def read(cf='', window=None):
     if isinstance(cf, dict):
          if cf['NEEDTEXT'] == False or "ALABAMA" in cf['QUEUE'][0]:
               return cf['QUEUE']
          if cf['NEEDTEXT'] == True:
               queue = cf['QUEUE']
               aptxt = []
               print("Extracting text...")
               if window:
                    window.write_event_value("PROGRESS_TOTAL",len(queue))
                    for i, pp in enumerate(queue):
                         aptxt += [getPDFText(pp)]
                         window.write_event_value("PROGRESS",i+1)
               else:
                    for pp in tqdm.tqdm(queue):
                         aptxt += [getPDFText(pp)]
          # allpagestext = pl.Series(aptxt)
          archive = pl.DataFrame({
               'Timestamp': time.time(),
               'AllPagesText': aptxt,
               'Path': queue
               })
          return archive
     elif os.path.isdir(cf):
          queue = glob.glob(path + '**/*.pdf', recursive=True)
          aptxt = []
          print("Extracting text...")
          if window:
               window.write_event_value("PROGRESS_TOTAL",len(queue))
               for i, pp in enumerate(queue):
                    aptxt += [getPDFText(pp)]
                    window.write_event_value("PROGRESS",i+1)
          else:
               for pp in tqdm.tqdm(queue):
                    aptxt += [getPDFText(pp)]
          # allpagestext = pl.Series(aptxt)
          archive = pl.DataFrame({
          'Timestamp': time.time(),
          'AllPagesText': aptxt,
          'Path': queue
          })
          return archive
     
     elif os.path.isfile(cf):
          ext = os.path.splitext(cf)[1]
          nzext = os.path.splitext(cf.replace(".zip","").replace(".xz","").replace(".gz","").replace(".tar","").replace(".bz",""))[1]
          if nzext in (".xls",".xlsx") and ext in (".xls",".xlsx"):
               parchive = pd.read_excel(cf)
               archive = pl.from_pandas(parchive)
               return archive
          if nzext == ".pkl" and ext == ".xz":
               parchive = pd.read_pickle(cf, compression="xz")
               archive = pl.from_pandas(parchive)
               return archive
          if nzext == ".pkl" and ext == ".pkl":
               parchive = pd.read_pickle(cf)
               archive = pl.from_pandas(parchive)
               return archive
          elif nzext == ".json" and ext == ".zip":
               parchive = pd.read_json(cf, orient='table', compression="zip")
               archive = pl.from_pandas(parchive)
               return archive
          elif nzext == ".json" and ext == ".json":
               try:
                    archive = pl.read_json(cf)
                    return archive
               except:
                    dlog(conf, "Warning: Read JSON with pandas after polars exception.")
                    parchive = pd.read_json(cf, orient='table')
                    archive = pl.from_pandas(parchive)
          elif nzext == ".csv" and ext == ".zip":
               archive = pd.read_csv(cf, compression="zip")
               return archive
          elif nzext == ".csv" and ext == ".csv":
               try:
                    archive = pl.read_csv(cf)
                    return archive
               except:
                    dlog(conf, "Warning: Read CSV with pandas after polars exception.")
                    parchive = pd.read_csv(cf)
                    archive = pl.from_pandas(parchive)
                    return archive
          elif nzext == ".parquet" and ext == ".parquet":
               try:
                    archive = pl.read_parquet(cf)
                    return archive
               except:
                    dlog(conf, "Warning: Read Parquet with pandas after polars exception.")
                    parchive = pd.read_parquet(cf)
                    archive = pl.from_pandas(parchive)
                    return archive
     else:
          return None

def append_archive(conf=None, inpath='', outpath='', window=None):
     if conf and inpath == '':
          inpath = conf.INPUT_PATH
     if conf and outpath == '':
          outpath = conf.OUTPUT_PATH

     assert os.path.isfile(inpath) and os.path.isfile(outpath)
     try:
          inarc = read(inpath).select("AllPagesText","Path","Timestamp")
          outarc = read(outpath).select("AllPagesText","Path","Timestamp")
     except:
          try:
               print("Could not find column Timestamp in archive.")
               inarc = read(inpath).select("AllPagesText","Path")
               outarc = read(outpath).select("AllPagesText","Path")
          except:
               print("Could not find column Path in archive.")
               inarc = read(inpath).select("AllPagesText")
               outarc = read(outpath).select("AllPagesText")

     out = pl.concat([inarc, outarc])
     if window:
               window.write_event_value("COMPLETE-AA",True)

def multi(cf, window=None):
     df = read(cf, window)
     print("Extracting case info...")
     ca, ac, af = splitCases(df)
     print("Parsing charges...")
     ch = splitCharges(ac)
     print("Parsing fees tables...")
     fs = splitFees(af)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     write(cf, [ca, ch, fs], sheet_names=["cases","charges","fees"])
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ca, ch, fs
     
def charges(cf, window=None):
     df = read(cf, window)
     print("Extracting charges...")
     ca, ac, af = splitCases(df)
     print("Parsing charges...")
     ch = splitCharges(ac)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     write(cf, ch)
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ch

def cases(cf, window=None):
     df = read(cf, window)
     print("Extracting case info...")
     ca, ac, af = splitCases(df)
     write(cf, ca)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return ca

def fees(cf, window=None):
     df = read(cf, window)
     print("Extracting fee sheets...")
     ca, ac, af = splitCases(df)
     print("Parsing fees tables...")
     fs = splitFees(af)
     write(cf, fs)
     if not cf['NO_WRITE']:
          print("Writing to export...")
     if window:
          window.write_event_value("COMPLETE-TB",True)
     return fs

def write(cf, outputs, sheet_names=[]):
     print(outputs)
     if isinstance(outputs, list):
          assert len(outputs) == len(sheet_names) or len(outputs) == 1
     if cf['NO_WRITE']==True:
          return outputs
     elif not cf['OVERWRITE'] and os.path.isfile(cf['OUTPUT_PATH']):
          raise Exception("Could not write to output path because overwrite mode is not enabled.")
     elif cf['OUTPUT_EXT'] in (".xlsx",".xls"):
          try:
               with xlsxwriter.Workbook(cf['OUTPUT_PATH']) as workbook:
                    if len(sheet_names) > 1:
                         for i, x in enumerate(outputs):
                              x.write_excel(workbook=workbook,worksheet=sheet_names[i])
                    elif len(sheet_names) == 1:
                         outputs.write_excel(workbook=workbook,worksheet=sheet_names[0])
                    elif len(sheet_names) == 0:
                         try:
                              outputs.write_excel(workbook=workbook)
                         except:
                              print("598")
                              outputs.to_pandas().to_excel(cf['OUTPUT_PATH'], engine="openpyxl")
          except:
               print("Write xls(x) with polars / xlsxwriter failed. Falling back to pandas / openpyxl...")
               if len(sheet_names) == 0:
                    po = outputs.to_pandas()
                    po.to_excel(engine="openpyxl")
               if len(sheet_names) == 1:
                    po = outputs.to_pandas()
                    po.to_excel(engine="openpyxl", sheet_name=sheet_names[0])
               elif sheet_names == ["cases","charges","fees"]:
                    ca = outputs[0].to_pandas()
                    ca.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="cases")
                    ch = outputs[1].to_pandas()
                    ch.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="charges")
                    fs = outputs[2].to_pandas()
                    fs.to_excel(cf['OUTPUT_PATH'], engine="openpyxl", sheet_name="fees")
               elif len(sheet_names) > 1:
                    with pd.ExcelWriter(conf.OUTPUT_PATH) as writer:
                         for i, x in enumerate(outputs):
                              x.to_excel(writer, sheet_name=sheet_names[0], engine="openpyxl")
               else:
                    for i, x in enumerate(outputs):
                         newpath = cf['OUTPUT_PATH'].replace(".xls","").replace(".xlsx","") + "-" + sheet_names[i] + ".xlsx"
     elif cf['COMPRESS'] and cf['OUTPUT_EXT'] == ".parquet":
          try:
               outputs.write_parquet(cf['OUTPUT_PATH'], compression='brotli') # add int flag for compress - 0min-11max
          except:
               outputs.write_parquet(cf['OUTPUT_PATH'], compression='snappy')
     elif not cf['COMPRESS'] and cf['OUTPUT_EXT'] == ".parquet":
          outputs.write_parquet(cf['OUTPUT_PATH'], compression="uncompressed")
     elif cf['OUTPUT_EXT'] == ".json":
          outputs.write_json(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] == ".csv":
          outputs.write_csv(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] == ".dta":
          import pandas as pd
          outputs_pd = outputs.to_pandas()
          outputs_pd.to_stata(cf['OUTPUT_PATH'])
     elif cf['OUTPUT_EXT'] not in ("none","","directory",None):
          outputs.write_csv(cf['OUTPUT_PATH'])
     else:
          pass
     return outputs

def init(cf, window=None):
     if cf['ARCHIVE'] == True:
          ar = archive(cf, window=window)
          return ar
     elif cf['TABLE'] == "charges" and cf['SUPPORT_SINGLETABLE']:
          ch = charges(cf, window=window)
          return ch
     elif cf['TABLE'] == "cases" and cf['SUPPORT_SINGLETABLE']:
          ca = cases(cf, window=window)
          return ca
     elif cf['TABLE'] == "fees" and cf['SUPPORT_SINGLETABLE']:
          fs = fees(cf, window=window)
          return fs
     elif cf['TABLE'] in ("all","","multi","multitable") and cf['SUPPORT_MULTITABLE']:
          ca, ch, fs = multi(cf, window=window)
          return ca, ch, fs
     else:
          print("Job not specified. Select a mode and reconfigure to start.")
          return None

def complete(cf, window):
	window.write_event_value("COMPLETE")

def dlog(cf=None, text=""):
     if cf == None:
          return None
     else:
          if cf['DEBUG'] == True:
               print(text)
               return text
          else:
               return None

def splitCases(df):
     cases = df.with_columns([
          pl.col("AllPagesText").str.extract(r'(?:VS\.|V\.{1})([A-Z\s]{10,100})(Case Number)*',group_index=1).str.replace_all("Case Number:","",literal=True).str.replace(r'C$','').str.strip().alias("Name"),
          pl.col("AllPagesText").str.extract(r'(?:SSN)(.{5,75})(?:Alias)', group_index=1).str.replace(":","",literal=True).str.strip().alias("Alias"),
          pl.col("AllPagesText").str.extract(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)', group_index=1).str.replace(r'[^\d/]','').str.strip().alias("DOB"),
          pl.col("AllPagesText").str.extract(r'(\w{2}\-\d{4}\-\d{6}\.\d{2})').alias("SHORTCASENO"),
          pl.col("AllPagesText").str.extract(r'(?:County: )(\d{2})').alias("SHORTCOUNTY"),
          pl.col("AllPagesText").str.extract(r'(Phone: )(.+)', group_index=2).str.replace_all(r'[^0-9]','').str.slice(0,10).alias("RE_Phone"),
          pl.col("AllPagesText").str.extract(r'(B|W|H|A)/(?:F|M)').alias("Race"),
          pl.col("AllPagesText").str.extract(r'(?:B|W|H|A)/(F|M)').alias("Sex"),
          pl.col("AllPagesText").str.extract(r'(?:Address 1:)(.+)(?:Phone)*?', group_index=1).str.replace(r'(Phone.+)','').str.strip().alias("StreetAddress"),
          pl.col("AllPagesText").str.extract(r'(?:Zip: )(.+)',group_index=1).str.replace(r'[A-Z].+','').alias("ZipCode"),
          pl.col("AllPagesText").str.extract(r'(?:City: )(.*)(?:State: )(.*)', group_index=1).alias("City"),
          pl.col("AllPagesText").str.extract(r'(?:City: )(.*)(?:State: )(.*)', group_index=2).alias("State"),
          pl.col("AllPagesText").str.extract_all(r'(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}.{10,75})').alias("RE_Charges"),
          pl.col("AllPagesText").str.extract_all(r'(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^\n]*)').alias('RE_Fees')])

     # clean Phone, concat CaseNumber
     cases = cases.with_columns(
          pl.col("RE_Phone").str.replace_all(r'[^0-9]','').alias("CLEAN_Phone"),
          pl.concat_str([pl.col("SHORTCOUNTY"),pl.lit("-"),pl.col("SHORTCASENO")]).alias("CaseNumber"),
          pl.col("Name"))
     cases = cases.with_columns(
          pl.when(pl.col("CLEAN_Phone").str.n_chars()<7).then(None).otherwise(pl.col("CLEAN_Phone")).alias("Phone"))

     # clean Charges strings
     # explode Charges for table parsing
     all_charges = cases.explode("RE_Charges").select([
          pl.col("CaseNumber"),
          pl.col("RE_Charges").str.replace_all(r'[A-Z][a-z][A-Za-z\s\$]+.+','').str.strip().alias("Charges")])
     cases.drop_in_place("RE_Charges")

     # clean Fees strings
     # explode Fees for table parsing
     all_fees = cases.explode("RE_Fees").select([
          pl.col("CaseNumber"),
          pl.col("RE_Fees").str.replace_all(r"[^A-Z0-9|\.|\s|\$|\n]"," ").str.strip().alias("Fees")])
     cases.drop_in_place("RE_Fees")

     # add Charges, Fees [str] to cases table
     clean_ch_list = all_charges.groupby("CaseNumber").agg(pl.col("Charges"))
     clean_fs_list = all_fees.groupby("CaseNumber").agg(pl.col("Fees"))
     cases = cases.join(clean_ch_list, on="CaseNumber", how="left")
     cases = cases.join(clean_fs_list, on="CaseNumber", how="left")
     cases = cases.with_columns(pl.col("Charges").arr.join("; ").str.replace_all(r'(null;?)',''))
     cases = cases.with_columns(pl.col("Fees").arr.join("; ").str.replace_all(r'(null;?)',''))
     cases = cases.fill_null('')
     cases = cases.select("CaseNumber","Name","Alias","DOB","Race","Sex","Phone","StreetAddress","City","State","ZipCode")
     return cases, all_charges, all_fees

def splitCharges(df):
     charges = df.with_columns([
          pl.col("Charges").str.slice(0,3).alias("Num"),
          pl.col("Charges").str.slice(4,4).alias("Code"),
          pl.col("Charges").str.slice(9,1).alias("Sort"), # 0-9: disposition A-Z: filing else: None
          pl.col("Charges").str.extract(r'(\d{1,2}/\d\d/\d\d\d\d)', group_index=1).alias("CourtActionDate"),
          pl.col("Charges").str.extract(r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}\({0,1}[A-Z]{0,1}\){0,1}\.{0,1}\d{0,1}',group_index=0).alias("Cite"),
          pl.col("Charges").str.extract(r'(BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', group_index=1).alias("CourtAction"),
          pl.col("Charges").apply(lambda x: re.split(r'[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\s{0,1}-[A-Z0-9]{3}\({0,1}?[A-Z]{0,1}?\){0,1}?\.{0,1}?\d{0,1}?',str(x))).alias("Split")
          ])
     charges = charges.with_columns([
          pl.col("Charges").str.contains(pl.col("CourtActionDate")).alias("Disposition"),
          pl.col("Charges").str.contains(pl.col("CourtActionDate")).is_not().alias("Filing"),
          pl.col("Charges").str.contains(pl.lit("FELONY")).alias("Felony"),
          pl.col("Charges").str.contains("GUILTY PLEA").alias("GUILTY_PLEA"),
          pl.col("Charges").str.contains("CONVICTED").alias("CONVICTED")
          ])
     charges = charges.with_columns([
          pl.when(pl.col("Disposition")).then(pl.col("Split").arr.get(1)).otherwise(pl.col("Split").arr.get(0).str.slice(9)).str.strip().alias("Description"),
          pl.when(pl.col("Disposition")).then(pl.col("Split").arr.get(0).str.slice(19)).otherwise(pl.col("Split").arr.get(1)).str.strip().alias("SEG_2")
          ])
     charges = charges.with_columns([
          pl.col("SEG_2").str.extract(r'(TRAFFIC MISDEMEANOR|BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', group_index=1).str.replace("TRAFFIC MISDEMEANOR","MISDEMEANOR").alias("TypeDescription"),
          pl.col("SEG_2").str.extract(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', group_index=1).alias("Category"),
          pl.col("Description").str.contains(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)').is_not().alias("A_S_C_DISQ"),
          pl.col("Code").str.contains('(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)').alias("CERV_DISQ_MATCH"),
          pl.col("Code").str.contains(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)').alias("PARDON_DISQ_MATCH"),
          pl.col("Charges").str.contains(r'(CM\d\d|CMUR)|(CAPITAL)').alias("PERM_DISQ_MATCH")
          ])
     charges = charges.with_columns(
          pl.when(pl.col("GUILTY_PLEA") | pl.col("CONVICTED")).then(pl.lit(True)).otherwise(False).alias("Conviction")
          )
     charges = charges.with_columns([
          pl.when(pl.col("CERV_DISQ_MATCH") & pl.col("Felony") & pl.col("Conviction") & pl.col("A_S_C_DISQ")).then(True).otherwise(False).alias("CERVDisqConviction"),
          pl.when(pl.col("PARDON_DISQ_MATCH") & pl.col("A_S_C_DISQ") & pl.col("Conviction") & pl.col("Felony")).then(True).otherwise(False).alias("PardonDisqConviction"),
          pl.when(pl.col("PERM_DISQ_MATCH") & pl.col("A_S_C_DISQ") & pl.col("Felony") & pl.col("Conviction")).then(True).otherwise(False).alias("PermanentDisqConviction")
          ])
     charges.drop_in_place("A_S_C_DISQ")
     charges.drop_in_place("CERV_DISQ_MATCH")
     charges.drop_in_place("PARDON_DISQ_MATCH")
     charges.drop_in_place("PERM_DISQ_MATCH")
     charges.drop_in_place("GUILTY_PLEA")
     charges.drop_in_place("CONVICTED")
     charges.drop_in_place("Sort")
     charges.drop_in_place("Split")
     charges.drop_in_place("SEG_2")
     charges.drop_in_place("Charges")

     charges = charges.drop_nulls()
     charges = charges.fill_null(pl.lit(''))

     return charges

def splitFees(df):
     df = df.select([
          pl.col("CaseNumber"),
          pl.col("Fees").str.replace(r'(?:\$\d{1,2})( )','\2').str.split(" ").alias("SPACE_SEP"),
          pl.col("Fees").str.strip().str.replace(" ","").str.extract_all(r'\$\d+\.\d{2}').alias("FEE_SEP")
          ])
     df = df.select([
          pl.col("CaseNumber"),
          pl.col("SPACE_SEP").arr.get(0).alias("AdminFee1"), # good
          pl.col("SPACE_SEP").arr.get(1).alias("FeeStatus1"), # good
          pl.col("FEE_SEP").arr.get(0).alias("AmtDue"), # good
          pl.col("FEE_SEP").arr.get(1).alias("AmtPaid"), # good
          pl.col("FEE_SEP").arr.get(-1).alias("AmtHold1"),
          pl.col("SPACE_SEP").arr.get(5).alias("Code"), # good
          pl.col("SPACE_SEP").arr.get(6).alias("Payor2"), # good
          pl.col("SPACE_SEP").arr.get(7).alias("Payee2"), # good
          pl.col("FEE_SEP").arr.get(-1).alias("Balance") # good
          ])
     out = df.with_columns([
          pl.col("CaseNumber"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then(True).otherwise(False).alias("Total"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then('').otherwise(pl.col("AdminFee1")).alias("AdminFee"),
          pl.when(pl.col("Payor2").str.contains(r"[^R0-9]\d{3}").is_not()).then(pl.lit('')).otherwise(pl.col("Payor2")).alias("Payor1"),
          pl.when(pl.col("Payor2").str.contains(r"[^R0-9]\d{3}").is_not()).then(pl.col("Payor2")).otherwise(pl.col("Payee2")).alias("Payee1"),
          pl.when(pl.col("AdminFee1")=="Total:").then(pl.lit(None)).otherwise(pl.col("FeeStatus1")).alias("FeeStatus2"),
          pl.when(pl.col("AmtHold1")=="L").then("$0.00").otherwise(pl.col("AmtHold1").str.replace_all(r'[A-Z]|\$','')).alias("AmtHold")
          ])
     out = out.select([
          pl.col("CaseNumber"),
          pl.col("Total"),
          pl.col("AdminFee"),
          pl.when(pl.col("FeeStatus2").str.contains("$", literal=True)).then(pl.lit(None)).otherwise(pl.col("FeeStatus2")).alias("FeeStatus"),
          pl.col("Code"),
          pl.when(pl.col("AdminFee1")!="ACTIVE").then('').otherwise(pl.col("Payor1")).alias("Payor"),
          pl.when(pl.col("Payee1").str.contains(r'\$|\.')).then('').otherwise(pl.col("Payee1")).alias("Payee"),
          pl.col("AmtDue"),
          pl.col("AmtPaid"),
          pl.col("Balance"),
          pl.col("AmtHold")
          ])
     out = out.drop_nulls("AmtDue")
     out = out.fill_null('')
     return out

if __name__ == "__main__":
     cli()