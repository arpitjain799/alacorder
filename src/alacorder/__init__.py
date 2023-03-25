"""
Usage: python -m alacorder [OPTIONS] COMMAND [ARGS]...

  Alacorder retrieves case detail PDFs from Alacourt.com and processes them
  into text archives and data tables suitable for research purposes. Invoke
  without subcommand (i.e. `python -m alacorder`) to launch graphical user
  interface or add flag `--help` for list of command line interface
  subcommands.)

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
"""