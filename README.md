<a href="https://colab.research.google.com/github/sbrobson959/alacorder/blob/main/index.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/sbrobson959/alacorder/main?labpath=index.ipynb)
```
    ___    __                          __         
   /   |  / /___  _________  _________/ /__  _____
  / /| | / / __ `/ ___/ __ \/ ___/ __  / _ \/ ___/
 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
/_/  |_/_/\__,_/\___/\____/_/   \__,_/\___/_/     

ALACORDER beta 76
```
# **Getting Started with Alacorder**
### Alacorder processes case detail PDFs into data tables suitable for research purposes. Alacorder also generates compressed text archives from the source PDFs to speed future data collection from the same set of cases.

<sup>[GitHub](https://github.com/sbrobson959/alacorder)  | [PyPI](https://pypi.org/project/alacorder/)     | [Report an issue](mailto:sbrobson@crimson.ua.edu)
</sup>
```
Usage: python -m alacorder [OPTIONS]

Options:
  -in, --input-path PATH    Path to input archive or PDF directory  [required]
  -out, --output-path PATH  Path to output table (.xls, .xlsx, .csv, .json,
                            .dta) or archive (.pkl.xz, .json.zip, .parquet)
                            [required]
  -t, --table TEXT          Table export choice (cases, fees, charges,
                            disposition, filing, or all)
  -a, --archive             Create full text archive at output path
  -c, --count INTEGER       Total cases to pull from input
  --dedupe / --ignore       Remove duplicate cases from archive outputs
  -z, --compress            Compress exported file (archives compress with or
                            without flag)
  -o, --overwrite           Overwrite existing files at output path
  -q, --no-log              Don't print logs or progress to console
  -p, --no-prompt           Skip user input / confirmation prompts
  -d, --debug               Print extensive logs to console for developers
  -b, --no-batch            Process all inputs as one batch
```

## **Installation**

**Alacorder can run on most devices. If your device can run Python 3.7 or later, it can run Alacorder.**
* To install on Windows and Mac, open Command Prompt (Terminal) and enter `pip install alacorder` or `pip3 install alacorder`. 
* On Mac, open the Terminal and enter `pip install alacorder` or `pip3 install alacorder`.
* Install [Anaconda Distribution](https://www.anaconda.com/products/distribution) to install Alacorder if the above methods do not work, or if you would like to open an interactive browser notebook equipped with Alacorder on your desktop.
    * After installation, create a virtual environment, open a terminal, and then repeat these instructions. If your copy of Alacorder is corrupted, use `pip uninstall alacorder` or `pip3 uninstall alacorder` and then reinstall it. There may be a newer version available.

> **Alacorder should automatically download and install missing dependencies upon setup, but you can also install them yourself with `pip`: `pandas`, `numpy`, `PyPDF2`, `openpyxl`, `xlrd`, `xlwt`, `xarray`, `numexpr`, `bottleneck`, `cython`, `pyarrow`, `jupyter`, and `click`. Recommended dependencies: `xlsxwriter`, `tabulate`, `matplotlib`.**


```python
pip install alacorder
```

## **Using the command line interface**

#### **Once you have a Python environment up and running, you can launch the guided interface in two ways:**

1.  *Utilize the `alacorder` module in your command line:* Use the command line tool `python -m alacorder`, or `python3 -m alacorder`. If  the guided version is launched instead of the command line tool, update your installation with `pip install --upgrade alacorder`.

2. *Conduct custom searches with `alac`:* Use the import statement `from alacorder import alac` to use the Alacorder APIs to collect custom data from case detail PDFs. See how you can make `alacorder` work for you in the code snippets below.

#### **Alacorder can be used without writing any code, and exports to common formats like Excel (`.xls`, `.xlsx`), Stata (`.dta`), CSV (`.csv`), and JSON (`.json`).**

* Alacorder compresses case text into `pickle` archives (`.pkl.xz`) to save storage and processing time. If you need to unpack a `pickle` archive without importing `alac`, use a `.xz` compression tool, then read the `pickle` into Python with the `pandas` method [`pd.read_pickle()`](https://pandas.pydata.org/docs/reference/api/pandas.read_pickle.html).


# **Special Queries with `alac`**

```python
from alacorder import alac
```

### **For more advanced queries, the `alac` module can extract fields and tables from case records with just a few lines of code.**

* Call `alac.setinputs("/pdf/dir/")` and `alac.setoutputs("/to/table.xlsx")` to configure your input and output paths. Then call `alac.set(input_conf, output_conf, **kwargs)` to complete the configuration process. Feed the output to any of the `alac.write...()` functions to start a task.

* Call `alac.archive(config)` to export a full text archive. It's recommended that you create a full text archive (`.pkl.xz`) file before making tables from your data. Full text archives can be scanned faster than PDF directories and require less storage. Full text archives can be imported to Alacorder the same way as PDF directories. 

* Call `alac.tables(config)` to export detailed case information tables. If export type is `.xls` or `.xlsx`, the `cases`, `fees`, and `charges` tables will be exported.

* Call `alac.charges(config)` to export `charges` table only.

* Call `alac.fees(config)` to export `fees` table only.

* Call `alac.caseinfo(config)` to export `cases` table only. 


```python
import warnings
warnings.filterwarnings('ignore')

from alacorder import alac

pdf_directory = "/Users/crimson/Desktop/Tutwiler/"
archive = "/Users/crimson/Desktop/Tutwiler.pkl.xz"
tables = "/Users/crimson/Desktop/Tutwiler.xlsx"

pdfconf = alac.setinputs(pdf_directory)
arcconf = alac.setoutputs(archive)

# write archive to Tutwiler.pkl.xz
c = alac.set(pdfconf, arcconf)
alac.archive(c) 

print("Full text archive complete. Now processing case information into tables at " + tables)

d = alac.setpaths(archive, tables) # runs setinputs(), setoutputs() and set() at once
alac.tables(d)

# write tables to Tutwiler.xlsx
alac.tables(tabconf)
```

## **Custom Parsing with `alac.map()`**
### If you need to conduct a custom search of case records, Alacorder has the tools you need to extract custom fields from case PDFs without any fuss. Try out `alac.map()` to search thousands of cases in seconds.


```python
from alacorder import alac
import re

archive = "/Users/crimson/Desktop/Tutwiler.pkl.xz"
tables = "/Users/crimson/Desktop/Tutwiler.xlsx"

def findName(text):
    name = ""
    if bool(re.search(r'(?a)(VS\.|V\.)(.+)(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.)(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    return name

c = alac.setpaths(archive, tables, count=2000) # set configuration

alac.map(c, findName, alac.getConvictions) # Name, Convictions table
```


| Method | Description |
| ------------- | ------ |
| `getPDFText(path) -> text` | Returns full text of case |
| `getCaseInfo(text) -> [case_number, name, alias, date_of_birth, race, sex, address, phone]` | Returns basic case details | 
| `getFeeSheet(text, cnum = '') -> [total_amtdue, total_balance, total_d999, feecodes_w_bal, all_fee_codes, table_string, feesheet: pd.DataFrame]` | Returns fee sheet and summary as `str` and `pd.DataFrame` |
| `getCharges(text, cnum = '') -> [convictions_string, disposition_charges, filing_charges, cerv_eligible_convictions, pardon_to_vote_convictions, permanently_disqualifying_convictions, conviction_count, charge_count, cerv_charge_count, pardontovote_charge_count, permanent_dq_charge_count, cerv_convictions_count, pardontovote_convictions_count, charge_codes, conviction_codes, all_charges_string, charges: pd.DataFrame]` |  Returns charges table and summary as `str`, `int`, and `pd.DataFrame` |
| `getCaseNumber(text) -> case_number` | Returns case number
| `getName(text) -> name` | Returns name
| `getFeeTotals(text) -> [total_row, tdue, tpaid, tbal, tdue]` | Return totals without parsing fee sheet



# **Working with case data in Python**


### Out of the box, Alacorder exports to `.xlsx`, `.xls`, `.csv`, `.json`, and `.dta`. But you can use `alac`, `pandas`, and other python libraries to create your own data collection workflows and design custom exports. 

***The snippet below prints the fee sheets from a directory of case PDFs as it reads them.***


```python
from alacorder import alac

c = alac.setpaths("/Users/crimson/Desktop/Tutwiler/","/Users/crimson/Desktop/Tutwiler.xls")

for path in c['contents']:
    text = alac.getPDFText(path)
    cnum = alac.getCaseNumber(text)
    charges_outputs = alac.getCharges(text, cnum)
    if len(charges_outputs[0]) > 1:
        print(charges_outputs[0])
```

## Extending Alacorder with `pandas` and other tools

Alacorder runs on [`pandas`](https://pandas.pydata.org/docs/getting_started/index.html#getting-started), a python library you can use to perform calculations, process text data, and make tables and charts. `pandas` can read from and write to all major data storage formats. It can connect to a wide variety of services to provide for easy export. When Alacorder table data is exported to `.pkl.xz`, it is stored as a `pd.DataFrame` and can be imported into other python [modules](https://www.anaconda.com/open-source) and scripts with `pd.read_pickle()` like below:
```python
import pandas as pd
contents = pd.read_pickle("/path/to/pkl")
```

If you would like to visualize data without exporting to Excel or another format, create a `jupyter notebook` and import a data visualization library like `matplotlib` to get started. The resources below can help you get started. [`jupyter`](https://docs.jupyter.org/en/latest/start/index.html) is a Python kernel you can use to create interactive notebooks for data analysis and other purposes. It can be installed using `pip install jupyter` or `pip3 install jupyter` and launched using `jupyter notebook`. Your device may already be equipped to view `.ipynb` notebooks. 

## **Resources**

* [`pandas` cheat sheet](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)
* [regex cheat sheet](https://www.rexegg.com/regex-quickstart.html)
* [anaconda (tutorials on python data analysis)](https://www.anaconda.com/open-source)
* [The Python Tutorial](https://docs.python.org/3/tutorial/)
* [`jupyter` introduction](https://realpython.com/jupyter-notebook-introduction/)


	

	
-------------------------------------		
© 2023 Sam Robson
