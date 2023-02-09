<a href="https://colab.research.google.com/github/sbrobson959/alacorder/blob/main/index.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>


	    ___    __                          __         
	   /   |  / /___ __________  _________/ /__  _____
	  / /| | / / __ `/ ___/ __ \/ ___/ __  / _ \/ ___/
	 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
	/_/  |_/_/\__,_/\___/\____/_/   \__,_/\___/_/     
								
		ALACORDER beta 7.4.1 


# **Getting Started with Alacorder**

<sup>[GitHub](https://github.com/sbrobson959/alacorder)  | [PyPI](https://pypi.org/project/alacorder/)     | [Report an issue](mailto:sbrobson@crimson.ua.edu)
</sup>

### Alacorder processes case detail PDFs into data tables suitable for research purposes. Alacorder also generates compressed text archives from the source PDFs to speed future data collection from the same set of cases.

## **Installation**

**Alacorder can run on most devices. If your device can run Python 3.7 or later, it can run alacorder.**
* To install on Windows, open Command Prompt and enter `pip install alacorder`. 
    * To start the interface, enter `python -m alacorder` or `python3 -m alacorder`.
* On Mac, open the Terminal and enter `pip3 install alacorder` then `python3 -m alacorder`.
    * To start the interface, enter `python3 -m alacorder` or `python -m alacorder`.
* Install [Anaconda Distribution](https://www.anaconda.com/products/distribution) to install Alacorder if the above methods do not work, or if you would like to open and edit this interactive tutorial on your desktop.
    * After installation, create a virtual environment, open a terminal, and then repeat these instructions. If your copy of alacorder is corrupted, use `pip uninstall alacorder` or `pip3 uninstall alacorder` and then reinstall it. There may be a newer version. Type `jupyter notebook` after installation to load the notebook viewing interface. Even though it appears in your browser, it is an offline notebook, so you can edit and interact with it as you choose.

> **Alacorder should automatically download and install dependencies upon setup, but you can also install the dependencies yourself with `pip`, `conda`, or another package manager (`pandas`, `numpy`, `PyPDF2`, `openpyxl`, `xlrd`, `xlwt`, `build`, `setuptools`, `xarray`).**


```python
%pip uninstall -y alacorder
%pip install alacorder
```

# **Using the guided interface**

#### **Once you have a Python environment up and running, you can launch the guided interface in two ways:**

1.  Importing the module from your command line. Depending on your Python configuration, enter `python -m alacorder` or `python3 -m alacorder` to launch the command line interface. 

2.  Importing the alacorder module in Python. Use the import statement `from alacorder import __main__` to run the command line interface.

#### **Alacorder can be used without writing any code, and exports to common formats like Excel (`.xls`), Stata (`.dta`), CSV (`.csv`), and JSON (`.json`).**

* Alacorder compresses case text into `pickle` archives (`.pkl.xz`) to save storage and processing time. If you need to unpack a `pickle` archive without the `alac` module, use a `.xz` compression tool, then read the `pickle` into Python with the standard library module `pickle`.**

* Once installed, enter `python -m alacorder` or `python3 -m alacorder` to start the interface. If you are using `iPython`, launch the `iPython` shell and enter `from alacorder import __main__` to launch the guided interface. 





```python
from alacorder import __main__
```

# **Writing basic scripts with `alac`**
------------

### **For advanced queries, the `alacorder` module `alac` can be used to extract fields and tables from Alacourt records with only a few lines of code.**

#### The `run` module creates the full text archives and detailed case summary tables outputted by the guided interface. 

* Call `alac.config(in_path: str, out_path='', flags='', print_log=True, warn=False)` and assign it to a variable to hold your configuration object. This tells the imported alacorder modules where and how to input and output. If `out-path` is left blank, `alac.write` methods will print to console instead of export. 

* Call `alac.writeArchive(config)` to export a full text archive. It's recommended that you create a full text archive and save it as a `.pkl` file before making tables from your data. Full text archives can be scanned faster than PDF directories and require much less storage. Full text archives can be used just like PDF directories. 

* Call `alac.writeTables(config)` to export detailed case information tables. If export type is `.xls`, the "`cases`", "`fees`", and "`charges`" tables will all be exported. Otherwise, you can select which table you would like to export. 

* Call `alac.writeCharges(config)` to export `charges` table only.

* Call `alac.writeFees(config)` to export `fee` tables only.


```python
import warnings
warnings.filterwarnings('ignore')

from alacorder import alac

pdf_directory = "/Users/crimson/Desktop/Tutwiler/"
archive = "/Users/crimson/Desktop/Tutwiler.pkl.xz"
tables = "/Users/crimson/Desktop/Tutwiler.xls"

# make full text archive from PDF directory 
c = alac.config(pdf_directory, archive)
alac.writeArchive(c)

print("Full text archive complete. Now processing case information into tables at " + tables)

# then scan full text archive for spreadsheet
d = alac.config(archive, tables)
alac.writeTables(d)
```

# **Custom Parsing with *`alac`***
----------------
### If you need to conduct a custom search of Alacorder records, the `alac` module has the tools you need to extract custom fields from case PDFs without any fuss. Try out `alac.write()` and `alac.search()` to search thousands of cases in just a few minutes.


```python
from alacorder import alac
import pandas as pd
import re

archive = "/Users/crimson/Desktop/Tutwiler.pkl.xz"
tables = "/Users/crimson/Desktop/Tutwiler.xls"

def findName(text):
    name = ""
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    return name

c = alac.config(archive, tables)

alac.write(c, findName)
```


| Method | Description |
| ------------- | ------ |
| `getPDFText(path) -> text` | Returns full text of case |
| `getCaseInfo(text) -> [case_number, name, alias, date_of_birth, race, sex, address, phone]` | Returns basic case details | 
| `getFeeSheet(text: str, cnum = '') -> [total_amtdue, total_balance, total_d999, feecodes_w_bal, all_fee_codes, table_string, feesheet: pd.DataFrame()]` | Returns fee sheet and summary as strings and pd.DataFrame() |
| `getCharges(text: str, cnum = '') -> [convictions_string, disposition_charges, filing_charges, cerv_eligible_convictions, pardon_to_vote_convictions, permanently_disqualifying_convictions, conviction_count, charge_count, cerv_charge_count, pardontovote_charge_count, permanent_dq_charge_count, cerv_convictions_count, pardontovote_convictions_count, charge_codes, conviction_codes, all_charges_string, charges: pd.DataFrame()]` | Returns charges table and summary as strings, int, and pd.DataFrame() |
| `getCaseNumber(text) -> case_number: str` | Returns case number
| `getName(text) -> name: str` | Returns name
| `getFeeTotals(text) -> [total_row: str, tdue: str, tpaid: str, tbal: str, tdue: str]` | Return totals without parsing fee sheet



# **Working with Python data types**

----------

### Out of the box, `alacorder` exports to `.xls`, `.csv`, `.json`, `.dta`, `.pkl.xz`, and `.txt`. But you can use `alac`, [`pandas`](https://pandas.pydata.org/docs/getting_started/index.html#getting-started), and other python modules to create your own data collection workflows and design custom exports. 

***The snippet below prints the fee sheets from a directory of case PDFs as it reads them.***


```python
from alacorder import alac

c = alac.config("/Users/crimson/Desktop/Tutwiler/","/Users/crimson/Desktop/Tutwiler.xls")

for path in c['contents']:
    text = alac.getPDFText(path)
    cnum = alac.getCaseNumber(text)
    charges_outputs = alac.getCharges(text, cnum)
    if len(charges_outputs[0]) > 1:
        print(charges_outputs[0])
```

## Extending alacorder with `pandas` and other tools

Alacorder runs on [`pandas`](https://pandas.pydata.org/docs/getting_started/index.html#getting-started), a python module you can use to perform calculations, process text data, and make tables and charts. `pandas` can read from and write to all major data storage formats. It can connect to a wide variety of services to expand the capability of `alacorder` data. When `alacorder` table data is exported to `.pkl.xz`, it is stored as a `DataFrame` and can be imported into other python [modules](https://www.anaconda.com/open-source) and libraries with `pd.read_pickle()` like below:
```
import pandas as pd
contents = pd.read_pickle("/path/to/pkl")
```

If you would like to visualize data without exporting to Excel or another format, create a `jupyter notebook`, and import a data visualization library like `matplotlib` to get started. The pandas tutorials and documentation can help you get started. `jupyter` is a Python [notebook](https://docs.jupyter.org/en/latest/start/index.html) kernel you can use to create interactive tools like this notebook. It can be installed using `pip install jupyter` or `pip3 install jupyter` and launched using `jupyter notebook`. Your computer may already be equipped to view `jupyter` notebooks. 

### Resources to get started

* [`pandas` cheat sheet](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)
* [regex cheat sheet](https://www.rexegg.com/regex-quickstart.html)
* [anaconda (tutorials on python data analysis)](https://www.anaconda.com/open-source)
* [The Python Tutorial](https://docs.python.org/3/tutorial/)




<sup>© 2023 Sam Robson</sup>
