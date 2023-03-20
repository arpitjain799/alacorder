## SETUP: Install all dependencies, then run this code block to load Alacorder in the notebook interface. 
import IPython.display
import ipywidgets, itables
from itables import init_notebook_mode
init_notebook_mode(all_interactive=True)
load_out = ipywidgets.Output()

with load_out:
    display(IPython.display.Markdown("This notebook can be used to interface with Alacorder directly. Once Alacorder is installed, launch Jupyter Notebook with the command line prompt `python3 -m jupyter notebook` or `python -m jupyter notebook`, then open `ALACORDER.ipynb` in the browser window that opens to begin. If your Python kernel is active and the notebook is trusted, Alacorder will load in this notebook automatically. Alacorder can run on most devices. If your device can run Python 3.7 or later, it can run Alacorder. The `fetch` tool for PDF retrieval requires an up-to-date installation of Google Chrome. Learn more at [PyPI](https://pypi.org/project/alacorder/) or [GitHub](https://github.com/sbrobson959/alacorder). **Click `Run > Run All Cells` to start notebook interface.** If installation fails, scroll to bottom of notebook and run frozen `%pip` cell (may have to \"unfreeze\" cell using toolbar), then restart kernel (`Kernel > Restart & Run All`)"))

import os, sys, warnings
import pandas as pd
from alacorder import alac

warnings.filterwarnings('ignore')

fetch_launcher = ipywidgets.Output() # frame: user input for fetch    
fetch_logs = ipywidgets.Output() # frame: logs, progress bars for fetch
fetch_table = ipywidgets.Output() # frame: logs, table for fetch
archive_launcher = ipywidgets.Output() # frame: user input for archive
archive_logs = ipywidgets.Output() # frame: logs, progress bars for archive
archive_table = ipywidgets.Output() # frame: logs, progress bars for archive
multitable_launcher = ipywidgets.Output() # frame: user input for multitable
multitable_logs = ipywidgets.Output() # frame: logs, progress bars for multitable
multitable_table = ipywidgets.Output() # frame: logs, table for multitable
singletable_launcher = ipywidgets.Output() # frame: user input for singletable
singletable_logs = ipywidgets.Output() # frame: logs, progress bars for singletable
singletable_table = ipywidgets.Output() # frame: logs, progress bars for singletable
debug_console = ipywidgets.Output() # feed debug logs here, pop 'er at the bottom


query_path = ipywidgets.Text(description="Input Path:", layout=ipywidgets.Layout(width='90%'), tooltip="Path to query template spreadsheet (list of names, etc. to search)")
output_dir = ipywidgets.Text(description="Output Path:", layout=ipywidgets.Layout(width='90%'))
cID = ipywidgets.Text(description="Customer ID: ")
uID = ipywidgets.Text(description="User ID: ")
pwd = ipywidgets.Password(description="Password: ")
btn = ipywidgets.Button(description="Login")
speed = ipywidgets.FloatText(description="Speed", value=1, min=0.1, max=3, step=0.1, layout=ipywidgets.Layout(width='40%'))
qskip = ipywidgets.IntText(description="Skip rows", value=0, min=0, step=1, layout=ipywidgets.Layout(width='40%'))
qmax = ipywidgets.IntText(description="Max rows", value=0, min=0, step=1, layout=ipywidgets.Layout(width='40%'))
fetch_opts = ipywidgets.HBox([speed, qskip, qmax], layout=ipywidgets.Layout(width='95%'))

def startFetch(*args):
    global clicked, query_path, output_dir, cID, uID, pwd, btn, speed, qskip, qmax, fetch_launcher, fetch_logs, fetch_table
    if os.path.isdir(output_dir.value) and os.path.isfile(query_path.value) and cID.value != "" and uID.value != "" and pwd.value != "":
        if qskip.value > 0 and qmax.value > 0:
            return alac.fetch(query_path.value,output_dir.value,cID=cID.value, uID=uID.value, pwd=pwd.value, speed=speed.value, qskip=qskip.value, qmax=qmax.value)
        elif qskip.value > 0:
            return alac.fetch(query_path.value,output_dir.value,cID=cID.value, uID=uID.value, pwd=pwd.value, speed=speed.value, qskip=qskip.value)
        elif qmax.value > 0:
            return alac.fetch(query_path.value,output_dir.value,cID=cID.value, uID=uID.value, pwd=pwd.value, speed=speed.value, qmax=qmax.value)
        else:
            return alac.fetch(query_path.value,output_dir.value,cID=cID.value, uID=uID.value, pwd=pwd.value, speed=speed.value)
    else:
        print("Ensure all fields are correctly filled, then try again.")
        return None

oQueryTable = ipywidgets.Output()
oQueryTable_hidden = True

def viewQueryTable(*args):
    global oQueryTable
    global oQueryTable_hidden
    if oQueryTable_hidden:
        inputstab = """<style> table {float:left} </style> <table> <thead> <tr> <th>Field</th> <th>Description</th> </tr> </thead> <tbody> <tr> <td><code>NAME</code></td> <td>Last Name First</td> </tr> <tr> <td><code>PARTY_TYPE</code></td> <td>Social Security Number (Optional)</td> </tr> <tr> <td><code>SSN</code></td> <td>Applies to civil cases only (Optional)</td> </tr> <tr> <td><code>DOB</code></td> <td>Date of Birth (M/DD/YYYY)</td> </tr> <tr> <td><code>COUNTY</code></td> <td>Select a county if not statewide</td> </tr> <tr> <td><code>DIVISION</code></td> <td>Select a division if not all divisions.</td> </tr> <tr> <td><code>CASE_YEAR</code></td> <td>Four digit case year to limit results</td> </tr> <tr> <td><code>FILED_BEFORE</code></td> <td>Do not include cases filed after M/DD/YYYY</td> </tr> <tr> <td><code>FILED_AFTER</code></td> <td>Do not include cases filed after M/DD/YYYY</td> </tr> </tbody> </table> """
        oQueryTable_hidden = False
        with oQueryTable:
            display(IPython.display.HTML(inputstab))
    else:
        oQueryTable.clear_output()
        oQueryTable_hidden = True
        pass

alacfetchhead = """<a id="fetch"></a>
<h2 id="collect-case-pdfs-in-bulk-from-alacourt-com-from-a-list-of-names-or-search-parameters-">Collect case PDFs in bulk from Alacourt.com from a list of names or search parameters.</h2>
<p><strong>Use column headers <code>NAME</code>, <code>PARTY_TYPE</code>, <code>SSN</code>, <code>DOB</code>, <code>COUNTY</code>, <code>DIVISION</code>, <code>CASE_YEAR</code>, and/or <code>FILED_BEFORE</code> in an Excel spreadsheet to submit a list of queries for Alacorder to scrape. Each column corresponds to a search field in Party Search. Missing columns and entries will be left empty, i.e. if only the <code>NAME</code>&#39;s and <code>CASE_YEAR</code>&#39;s are relevant to the search, a file with two columns will work.</strong></p>
"""
btn2 = ipywidgets.Button(description="Read more")

def showFetch(*args):
    global fetch_launcher, fetch_opts, query_path, output_dir, cID, uID, pwd, btn, btn2
    with fetch_launcher:
        display(IPython.display.HTML(alacfetchhead))
        display(btn2, oQueryTable)
        btn2.on_click(viewQueryTable)
        display(fetch_opts)
        display(query_path) 
        display(output_dir) 
        display(cID)
        display(uID)
        display(pwd)
        btn.on_click(startFetch)
        display(btn)



arc_title = IPython.display.HTML("""<a id="arc"></a>
<h2 id="case-text-archives-require-a-fraction-of-the-storage-capacity-and-processing-time-used-to-process-pdf-directories-before-exporting-your-data-to-tables-create-an-archive-with-supported-file-extensions-pkl-xz-json-zip-parquet-and-csv-zip-">Case text archives require a fraction of the storage capacity and processing time used to process PDF directories. Before exporting your data to tables, create an archive with supported file extensions  <code>.pkl.xz</code>, <code>.json(.zip)</code>, <code>.parquet</code> and <code>.csv(.zip)</code>.</h2>
<p><strong>Once archived, use your case text archive as an input for multitable or single table export.</strong></p>
""")
arc_inpath = ipywidgets.Text(description="Input Path", 
                            layout=ipywidgets.Layout(width='90%'), 
                            tooltip="Path to PDF directory")

arc_outpath = ipywidgets.Text(description="Output Path", layout=ipywidgets.Layout(width='90%'))
arc_overwrite = ipywidgets.Checkbox(description="Don't allow overwrite")
arc_dedupe = ipywidgets.Checkbox(description="Remove duplicates")
arc_compress = ipywidgets.Checkbox(description="ZIP export (must be .json, .csv)")
arc_btn = ipywidgets.Button(description="Start archiving")
arc_count = ipywidgets.IntText(description="Max count", value=0, min=0, step=1, layout=ipywidgets.Layout(width='40%'))

def startArchive(*args):
    global arc_title, arc_inpath, arc_outpath, arc_count, arc_overwrite, arc_btn
    arcov = not arc_overwrite.value
    if arc_inpath.value.strip() != "" and arc_outpath.value.strip() != "":
        a = alac.setinit(arc_inpath.value, arc_outpath.value, archive=True, overwrite=arcov, no_prompt=arcov, no_batch=True, count=arc_count.value)
        return a
    else:
        return None

def showArchive():
    global arc_title, arc_inpath, arc_outpath, arc_count, arc_overwrite, arc_dedupe, arc_compress, arc_btn
    with archive_launcher:
        display(arc_title)
        display(arc_count)
        display(arc_inpath)
        display(arc_outpath)
        arc_chk = ipywidgets.HBox([arc_overwrite, arc_dedupe, arc_compress])
        display(arc_chk)
        display(arc_btn)
        arc_btn.on_click(startArchive)
        return None

mtab_title = IPython.display.HTML("""<a id="mtab"></a>
<h2 id="multitable-export-processes-case-detail-pdfs-and-case-text-archives-into-data-tables-suitable-for-research-purposes-export-an-excel-spreadsheet-with-detailed-cases-information-cases-fee-sheets-fees-and-charges-information-charges-disposition-filing-">Multitable export processes case detail PDFs and case text archives into data tables suitable for research purposes. Export an Excel spreadsheet with detailed cases information (<code>cases</code>), fee sheets (<code>fees</code>), and charges information (<code>charges</code>, <code>disposition</code>, <code>filing</code>).</h2>
<p><strong><em>Note: It is recommended that you create a case text archive from your target PDF directory before exporting tables. Case text archives can be processed into tables at a much faster rate and require far less storage.</em></strong></p>""")
mtab_inpath = ipywidgets.Text(description="Input Path", 
                        layout=ipywidgets.Layout(width='95%'), 
                        tooltip="Path to input directory or archive")

mtab_outpath = ipywidgets.Text(description="Output Path", layout=ipywidgets.Layout(width='95%'))
mtab_count = ipywidgets.IntText(
    value=0,
    min=0,
    max=10000,
    step=1,
    description='Max count:',
    orientation='horizontal',
    readout=True,
    readout_format='d'
)
mtab_overwrite = ipywidgets.Checkbox(description="Don't allow overwrite")
mtab_btn = ipywidgets.Button(description="Start export")
mtab_obox = ipywidgets.HBox([mtab_count, mtab_overwrite])

def startMulti(*args):
    global mtab_title, mtab_inpath, mtab_outpath, mtab_count, mtab_overwrite, mtab_btn
    mtov = not mtab_overwrite.value
    if mtab_inpath.value.strip() != "":
        cf = alac.setpaths(mtab_inpath.value, mtab_outpath.value, overwrite=mtov, no_prompt=mtov, no_batch=True)
        a = alac.init(cf)
        with multitable_table:
            display(a[0],a[1],a[2])
        return a
    else:
        return None

def showMulti():
    with multitable_launcher:
        display(mtab_title)
        display(mtab_obox)
        display(mtab_inpath)
        display(mtab_outpath)
        mtab_btn.on_click(startMulti)
        display(mtab_btn)
        return None


stab_title = IPython.display.HTML("""<a id="stab"></a>
<h2 id="export-charges-including-disposition-only-and-filing-only-cases-or-fees-table-only-single-table-export-enables-file-types-without-support-for-multiple-sheets-this-mode-allows-export-to-csv-json-dta-xls-xlsx-pkl-and-parquet-files-">Export <code>charges</code> (including <code>disposition</code> only and <code>filing</code> only), <code>cases</code>, or <code>fees</code> table only. Single table export enables file types without support for multiple sheets. This mode allows export to <code>.csv</code>, <code>.json</code>, <code>.dta</code>, <code>.xls</code>, <code>.xlsx</code>, <code>.pkl</code>, and <code>.parquet</code> files.</h2>
<p><strong>Once archived, use your case text archive as an input for multitable or single table export.</strong></p>""")
stab_inpath = ipywidgets.Text(description="Input Path", 
                        layout=ipywidgets.Layout(width='90%'), 
                        tooltip="Path to input directory or archive")
stab_table = ipywidgets.Dropdown(options=['cases', 'charges', 'disposition', 'filing', 'fees'],description='Table:',layout=ipywidgets.Layout(orientation='horizontal'))

stab_outpath = ipywidgets.Text(description="Output Path", layout=ipywidgets.Layout(width='90%'))
stab_count = ipywidgets.IntText(
    value=0,
    min=0,
    max=10000,
    step=1,
    description='Max count:',
    orientation='horizontal',
    readout=True,
    readout_format='d'
)
stab_overwrite = ipywidgets.Checkbox(description="Don't allow overwrite")
stab_btn = ipywidgets.Button(description="Start export")

stab_obox = ipywidgets.HBox([stab_count, stab_overwrite])

def startSingle(*args):
    global stab_title, stab_inpath, stab_outpath, stab_count, stab_overwrite, stab_btn
    stov = not stab_overwrite.value
    if stab_inpath.value.strip() != "":
        a = alac.setinit(stab_inpath.value, stab_outpath.value, table=stab_table.value, overwrite=stov, no_prompt=stov, no_batch=True, count=stab_count.value)
        with singletable_table:
            display(a)
        return a
    else:
        return None

def showSingle():
    global singletable_launcher
    with singletable_launcher:
        display(stab_title)
        display(stab_obox)
        display(stab_inpath)
        display(stab_outpath)
        display(stab_table)
        stab_btn.on_click(startSingle)
        display(stab_btn)
        return None

with load_out:
    display(IPython.display.Markdown("**Notebook configuration succeeded. Run `%pip` cell at bottom of document, restart kernel and run all cells if `ALACORDER` does not function properly.**"))
