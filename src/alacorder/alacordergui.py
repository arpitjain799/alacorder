# main 78
# sam robson
try:
	import pyximport; pyximport.install()
	from alacorder import guialac as alac
except:
	try:
		from alacorder import guialac as alac
	except:
		import guialac as alac
import threading
import PySimpleGUI as sg
import os
import sys
import warnings
import pandas as pd

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.min_rows', 50)
pd.set_option('display.max_colwidth', 50)
pd.set_option('compute.use_bottleneck', True)
pd.set_option('compute.use_numexpr', True)
pd.set_option('display.max_categories', 16)
pd.set_option('display.precision',2)


warnings.filterwarnings('ignore')


version = "ALACORDER beta 78.4.5"

sg.theme("DarkBlack")
# sg.theme("DarkRed1")

sg.set_options(font="Default 12")


current_label = f"{version}"
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
create an archive with supported file extensions .pkl.xz, .json(.zip), and .csv
(.zip). Once archived, use your case text archive as an input for multitable or
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
with detailed cases information(cases), fee sheets (fees), and charges
information (charges, disposition, filing), or select a table to export to
another format (.json, .csv). Note: It is recommended that you create a
case text archive from your target PDF directory before exporting tables.
Case text archives can be processed into tables at a much faster rate and
require far less storage.""", pad=(5,5))],
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
      [sg.Text("""Case text archives require a fraction of the storage capacity
and processing time used to process PDF directories. Before exporting your
data to tables, create an archive with supported file extensions .pkl.xz,
.json(.zip), and .csv(.zip). Once archived, use your case text archive as
an input for multitable or single table export.""", pad=(5,5))],
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
      [sg.Text(f"""\n{version}""",font="Courier 22", pad=(5,5))],[sg.Text("""Alacorder retrieves and processes\nAlacourt case detail PDFs into\ndata tables and archives.""",font="Default 22", pad=(5,5))],
      [sg.Text(
            """1.  fetch - Retrieve case detail PDFs in bulk from Alacourt.com
2.  archive - Create full text archives from PDF directory
3.  table - Export data tables from case archive or directory
4.  append - Append contents of one archive to another
5.  mark - Mark already collected cases on query template""")],
      [sg.Text("""View documentation, source code, and latest updates at
github.com/sbrobson959/alacorder.\n\n© 2023 Sam Robson""")],
      ] # "ABOUT"
tabs = sg.TabGroup(expand_x=True, expand_y=False, size=[0,0], font="Courier",layout=[
                                [sg.Tab("fetch", layout=fetch_layout, pad=(2,2))],
                                [sg.Tab("archive", layout=archive_layout, pad=(2,2))],            
                                [sg.Tab("table", layout=table_layout, pad=(2,2))],
                                [sg.Tab("append", layout=append_layout, pad=(2,2))],
                                [sg.Tab("mark", layout=mark_layout, pad=(2,2))],
                                [sg.Tab("about", layout=about_layout, pad=(2,2))]])


layout = [[tabs],
     [sg.ProgressBar(100, size=[5,10], expand_y=False, orientation='h', expand_x=True, key="PROGRESS", bar_color="black")],
     [sg.Multiline(expand_x=True,expand_y=True,background_color="black",reroute_stdout=True,pad=(5,5),font="Courier 11",write_only=True,autoscroll=True,no_scrollbar=True,size=[None,3],border_width=0)]]



def loadgui():
     window = sg.Window(title="alacorder", layout=layout, grab_anywhere=True, resizable=True, size=[510,520])
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
                         cf = alac.setpaths(window['TB-INPUTPATH-'].get(), window['TB-OUTPUTPATH-'].get(), count=count,table=tabl,overwrite=window['TB-OVERWRITE-'].get(),compress=window['TB-COMPRESS-'].get(),no_prompt=True,log=True, debug=True,archive=False,window=window)
                         virgin = False
                         window['TB'].update(disabled=True)
                         threading.Thread(target=alac.init,args=(cf,window), daemon=True).start()
                 except:
                         continue
           elif event == "MA":
                  try:
                        count = int(window['MA-COUNT-'].get().strip())
                  except:
                        count = 0
                  aa = alac.setpaths(window['MA-INPUTPATH-'].get(),window['MA-OUTPUTPATH-'].get(),count=count, archive=True,overwrite=window['MA-OVERWRITE-'].get(), append=window['MA-APPEND-'].get(), no_prompt=True,log=True,window=window)
                  virgin = False
                  window['MA'].update(disabled=True)
                  threading.Thread(target=alac.archive, args=(aa, window), daemon=True).start()
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
                         threading.Thread(target=alac.fetch, args=(window['SQ-INPUTPATH-'].get(),window['SQ-OUTPUTPATH-'].get(),window['SQ-CUSTOMERID-'].get(),window['SQ-USERID-'].get(),pwd,sq_max,sq_skip,False,False,False,window), daemon=True).start()
                         continue
                 except:
                         continue
           elif event == "MQ":
                 try:
                         assert window["MQ-INPUTPATH-"].get() != ""
                         virgin = False
                         window['MQ'].update(disabled=True)
                         threading.Thread(target=alac.mark, args=(window['MQ-INPUTPATH-'].get(),window['MQ-OUTPUTPATH-'].get()), kwargs={'window':window},daemon=True)
                         continue
                 except:
                         continue
           elif event == "AA":
                 try:
                         assert window["AA-INPUTPATH-"].get() != ""
                         virgin = False
                         window['AA'].update(disabled=True)
                         threading.Thread(target=alac.append_archive, args=(window['MQ-INPUTPATH-'].get(),window['MQ-OUTPUTPATH-'].get()), kwargs={'window':window},daemon=True)
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
           else:
                 pass

if __name__ == "__main__":
    loadgui()

