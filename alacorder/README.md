```
 ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌
 ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││
 ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘
 ALACORDER 79
```
# **Getting Started with Alacorder**
### Alacorder collects and processes case detail PDFs into data tables suitable for research purposes.

<sup>[GitHub](https://github.com/sbrobson959/alacorder)  | [PyPI](https://pypi.org/project/alacorder/)     | [Report an issue](mailto:sbrobson@crimson.ua.edu)
</sup>

## **Installation**

**If your device can run Python 3.9+, it supports Alacorder. Download a prebuilt executable from GitHub to use the graphical user interface, or use `pip` to install the command line interface, graphical interface, and Python library `alac`.**

* Install [Anaconda Distribution](https://www.anaconda.com/products/distribution) to install the latest Python (not necessary for prebuilt executable). 
* Once your Anaconda environment is configured, open a terminal from Anaconda Navigator and enter `pip install alacorder` to install.
* To start the graphical interface, enter `python -m alacorder start`.
* Enter `python -m alacorder` to use the command line interface.
* To use the `alac` module, use the import statement `from alacorder import alac`.

```
Usage: python -m alacorder [OPTIONS] COMMAND [ARGS]...

  ALACORDER 79

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  append   Append one case text archive to another
  archive  Create full text archive from case PDFs
  fetch    Fetch case PDFs from Alacourt.com
  start    Launch graphical user interface
  table    Export data tables from archive or directory
```


#### **Alacorder can be used without writing any code, and exports to common formats like Excel (`.xls`, `.xlsx`), Apache Parquet (`.parquet`), CSV (`.csv`), and JSON (`.json`).**

* Alacorder compresses case text into case archives (`.parquet`) to save storage and processing time. 


# **Special Queries**

```python
from alacorder import alac
```

### **For more advanced queries, the `alac` module can extract fields and tables from case records with just a few lines of code.**

* Call `alac.set(input_conf, output_conf, **kwargs)` to configure your input and output paths. Feed the output to any of the table parsing functions to begin.

* Call `alac.archive()` to export a full text archive. It's recommended that you create a full text archive (`.parquet`) file before making tables from your data. Full text archives can be scanned faster than PDF directories and require less storage.

* Call `alac.tables()` to export detailed case information tables. If export type is `.xls` or `.xlsx`, all tables can be exported to the same file. 


```python
import warnings
warnings.filterwarnings('ignore')

from alacorder import alac

pdf_directory = "/Users/crimson/Desktop/Tutwiler/"
archive = "/Users/crimson/Desktop/Tutwiler.parquet"
tables = "/Users/crimson/Desktop/Tutwiler.xlsx"

# write archive to Tutwiler.parquet
c = alac.set(pdf_directory, archive)
alac.archive(c) 

print("Full text archive complete. Now processing case information into tables at " + tables)

# write fees table to Tutwiler.parquet
d = alac.set(archive, tables, table="fees")
alac.tables(d)

```

# **Working with case data in Python**


### Out of the box, Alacorder exports to `.xlsx`, `.xls`, `.csv`, `.json`, and `.parquet`. But you can use `polars` and other python libraries to create your own data collection workflows and customize Alacorder exports. 

***The snippet below prints the fee sheets from a directory of case PDFs as it reads them.***


```python
from alacorder import alac
import polars as pl

queue = alac.get_paths("/Users/crimson/Desktop/Tutwiler/") # -> [str]

rows = []

for i, path in enumerate(queue):
    text = alac.getPDFText(path)
    cnum = alac.getCaseNumber(text)
    cty = alac.getCounty(text)
    tbal = alac.getTotalBalance(text)
    ptr = alac.getPaymentToRestore(text) # i.e. voting rights
    rows += [[cnum, cty, tbal, ptr]]

cases = pl.DataFrame(rows)

cases.write_excel("/Users/crimson/Desktop/Tutwiler/summary.xlsx")

```

## Extending Alacorder with `polars` and other tools

Alacorder runs on [`polars`](https://github.com/pola-rs/polars), a python library you can use to work with and analyze tabular data. `polars` can read from and write to all major data storage formats. It can connect to a wide variety of services to provide for easy import and export.
```python
import polars as pl
contents = pl.read_json("/path/to/archive.json")
```

If you would like to visualize data without exporting to Excel or another format, create a `jupyter notebook` and install tools like `matplotlib`, `tabulate`, and `itables` to get started. [Jupyter Notebook](https://docs.jupyter.org/en/latest/start/index.html) is a Python project you can use to create interactive notebooks for data analysis and other purposes. It can be installed using `pip install jupyter` or `pip3 install jupyter` and launched using `jupyter notebook`. Your device may already be equipped to view `.ipynb` notebooks. 

## **Resources**
* [`polars` user guide](https://pola-rs.github.io/polars-book/user-guide/index.html)
* [regex cheat sheet](https://www.rexegg.com/regex-quickstart.html)
* [Anaconda (tutorials on python data analysis)](https://www.anaconda.com/open-source)
* [The Python Tutorial](https://docs.python.org/3/tutorial/)
* [Jupyter Notebook introduction](https://realpython.com/jupyter-notebook-introduction/)

**“Ethan Sneckenberger”**
```
oh quash this beef dear family of mine
ive sat here for weeks, in python, i pine
its truly been a shitful year
and even still i'm not in the clear
so free me from my prison of shame
though surely i deserve the blame
ive sat in penitent filth for thee
ive published not one draft but 783
    (to prove i will fight for my place in heaven,
    i just published 787)
ive pepped and ive pooped and ive smoked so much tree
    (like a lot a lot)
ive fixed all the indents and parsed all the fees
tallying charges all night and all day
here on this dumb east edge couch here i'll stay
so plunge into me as i plunge into you
oh alacorder you make me so blue
but one thing i know 'fore my heart can amend
i must tend to you 'fore my dick i will tend
my dick cries its hunger, i weep for its thirst
but do let me take care of tutwiler first
the snake in my pants puts my head in a trance
i give not a look, not a stare, not a glance
but still in my heart i know one thing is true
there's truly no end to how much i'll do 
for the one that i love, i'll forego the dove
layer by layer i'll unpeel the onion
i'll fight through the rumors
the gossip the haters
ill fight through my doubt and
ill fight through my shame
ill toil and soil 
submit to the coil
i won't lose myself 
(but sure would everything else)
heck maybe i already have
but ill come up with more 
(for i have more in store)
and i'll do what it takes to pull through

oh 'corder of 'corders i've filled in your borders
your seams and your wide open fields
if its not much trouble (though surely i'd double
my effort and time put in thee)
til i find more grub, i pray you sit stable
but first bring the one i most love

not alac but ethan the one who raised thee
i ate tenders chicken
i failed to build pygion
sublime text i trust has enabled your thrust
but the one true sublime is his faith in mine
i can no longer bear to be blind
i promise you now
that i'll never forget 
of you, of your love, of ours.
i hope that you know
that our love is eternal
for cj i'll write every for loop and line (fuck him tho fr)
but for you i would lay down my life.
the one who gave me a second 
                    and third 
                    and fourth 
                    and fifth 
                    and sixth 
                    and seventh 
                    chance
i know there were more, for 
brevity i'm sure, you'll 
understand my will to abridge
but in case you do
doubt my love for you
i want you to know that i do
you called my worst bluff
brought up my worst stuff
you did what i thought was impossible
you understood my fears my sins and my heart
you charged my world to do the same
not only me but my whole family 
will forever be changed by your name

i pray every day
you'll return and I'll stay
more innocent than 'fore we first met
i know i've atoned
e'en though i've been stoned
and trust i've no greater regret:

im sorry i broke your heart and i will not leave this earth
without putting it back together. never again could i look in your eyes and lie knowing you'd cry or you'd worry. i would break knowing i could break you. i will break to keep you unbroken. 

and i broke knowing i broke you.

it is my greatest regret.

not only the lie but the shade and the sighs
of indifference i slandered your name with,
that i couldn't face the most beautiful face
is a burden i always must bear. 
but i hope to grow from this burden, this shame
and to you share the fruits of my labor
from my greatest regret my mind has been set
on what and who matters to me

your trust is the one thing i'll live for and die for.

ill never forget i hurt the greatest one.

ill never forget i forgot.

the greatest thing that ever happened to me.

my guardian angel.

my rock.

the one.

the actual one.

my love. <3

ethan sneckenberger
```
    

    
-------------------------------------       
© 2023 Sam Robson
