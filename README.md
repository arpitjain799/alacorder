```
    ___    __                          __         
   /   |  / /___  _________  _________/ /__  _____
  / /| | / / __ `/ ___/ __ \/ ___/ __  / _ \/ ___/
 / ___ |/ / /_/ / /__/ /_/ / /  / /_/ /  __/ /    
/_/  |_/_/\__,_/\___/\____/_/   \__,_/\___/_/     

ALACORDER 78.5
```
# **Getting Started with Alacorder**
### Alacorder collects and processes case detail PDFs into data tables suitable for research purposes.

<sup>[GitHub](https://github.com/sbrobson959/alacorder)  | [PyPI](https://pypi.org/project/alacorder/)     | [Report an issue](mailto:sbrobson@crimson.ua.edu)
</sup>

## **Installation**

**Alacorder can run on most devices. If your device can run Python 3.9 or later, it can run Alacorder.**
* To skip installation, download prebuilt executable for your OS (MacOS or Windows) from GitHub.
* If you already have Python installed, open Command Prompt or Terminal and enter `pip install alacorder` or `pip3 install alacorder`. 
* Install [Anaconda Distribution](https://www.anaconda.com/products/distribution) to install Alacorder if the above methods do not work.
    * After installation, create a virtual environment, open a terminal, and then repeat these instructions. 

```
Usage: python -m alacorder [OPTIONS] COMMAND [ARGS]...

  Alacorder retrieves case detail PDFs from Alacourt.com and processes them
  into text archives and data tables suitable for research purposes. Invoke
  `python -m alacorder start`) to launch graphical user interface.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  append   Append one case text archive to another
  archive  Create full text archive from case PDFs
  fetch    Fetch cases from Alacourt.com with input query spreadsheet...
  mark     Mark query template sheet with cases found in archive or PDF...
  start    Launch graphical user interface
  table    Export data tables from archive or directory
```

## **The `alacorder` package includes a desktop interface, a command line interface, and a python module for parsing case PDFs.**

#### **Once you have a Python environment up and running, you can launch the guided interface in two ways:**

1.  *Utilize the graphical interface:* Use the command line tool `python -m alacorder start`, or `python3 -m alacorder start`. 

2. *Use the command line interface:* Add the flag `--help` or simply run `python -m alacorder` to access list of subcommands for command line interface.

#### **Alacorder can be used without writing any code, and exports to common formats like Excel (`.xls`, `.xlsx`), Stata (`.dta`), CSV (`.csv`), JSON (`.json`), and Apache Parquet (.parquet).**

* Alacorder compresses case text into case archives (`.pkl.xz`, `.parquet`) to save storage and processing time.


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

* Call `alac.cases(config)` to export `cases` table or `all` if output extension supports `multitable` export. 


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

alac.map(c, findName, alac.getPaymentToRestore) # Name, Convictions table
```


# **Working with case data in Python**


### Out of the box, Alacorder exports to `.xlsx`, `.xls`, `.csv`, `.json`, `.dta`, and `.parquet`. But you can use `alac`, `pandas`, and other python libraries to create your own data collection workflows and customize Alacorder exports. 

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

Alacorder runs on [`pandas`](https://pandas.pydata.org/docs/getting_started/index.html#getting-started), a python library you can use to work with and analyze tabular data. `pandas` can read from and write to all major data storage formats. It can connect to a wide variety of services to provide for easy export.
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
