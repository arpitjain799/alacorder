# main 75 
# sam robson
try:
    import pyximport; pyximport.install()
    import cal
except:
    from alacorder import alac as cal
import glob
import inspect
import math
import os
import re
import sys
import time
import warnings
import PyPDF2
import click
import numpy as np
import pandas as pd

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option("display.width", None)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)

## COMMAND LINE INTERFACE

@click.command()
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=cal.title(),
              help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', prompt=cal.both(), type=click.Path(),
              help="Path to output table (.xls, .xlsx, .csv, .json, .dta) or archive (.pkl.xz)", show_choices=False)
@click.option('--count', '-c', default=0, help='Max cases to pull from input', show_default=False)
@click.option('--table', '-t', help="Table export choice (cases, fees, charges, disposition, filing)")
@click.option('--overwrite', '-o', default=False, help="Overwrite output path if exists", is_flag=True,
              show_default=False)
@click.option('--launch', default=False, is_flag=True, help="Launch export in default application", show_default=False)
@click.option('--dedupe', '-dd', default=False, is_flag=True, help="Remove duplicate cases from input archive")
@click.option('--log / --no-log', default=True, is_flag=True, help="Print outputs to console upon completion")
@click.option('--no-write', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', '-np', default=False, is_flag=True, help="Skip confirmation prompts")
@click.option('--debug', default=False, is_flag=True, help="Prints extensive logs to console for development purposes")
@click.option('--no-batch', default=False, is_flag=True, help="Process all inputs as one batch")
@click.option('--compress', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
def cli(input_path, output_path, count, table, overwrite, launch, dedupe, log, no_write, no_prompt, debug, no_batch,
        compress):
    show_options_menu = True if table is None and no_prompt == False and count == 0 and overwrite == False and launch == False and dedupe == False and log == True and no_write == False and no_prompt == False and debug == False and no_batch == False else False

    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')

    # inputs - configure and log
    inputs = cal.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.echo(inputs.ECHO)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = cal.setoutputs(output_path)
    if debug:
        click.echo(outputs)
    if log:
        click.echo(outputs.ECHO)
    if not outputs.GOOD:
        raise Exception("Invalid input path!")

    # prompt overwrite
    if outputs.EXISTING_FILE and not overwrite:
        if no_prompt:
            raise Exception("Existing file at output path! Repeat with flag --overwrite to replace file.")
        else:
            if click.confirm(cal.echo_yellow("Existing file at output path will be written over! Continue?", echo=False)):
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
            pick = click.prompt(cal.pick_table())  # add str
            if pick == "A":
                table = "cases"
            elif pick == "B":
                table = "fees"
            elif pick == "C":
                table = "charges"
            elif pick == "D":
                table = "disposition"
            elif pick == "E":
                table = "filing"
            else:
                raise Exception("Invalid table selection!")

    if outputs.MAKE == "archive":
        compress = True

    # prompt options
    if show_options_menu and not no_prompt:
        if not click.confirm("Continue with current settings?"):
            cli.main(['alacorder', '--help'], standalone_mode=False)
            p = click.prompt('\nEnter the <option> you would like to set.')
            if p == "count" or p == "-c" or p == "--count":
                count = click.prompt("Set max case count to pull from input", type=int)
            elif p == "overwrite" or p == "--overwrite" or p == "-o":
                overwrite = click.prompt(
                    "Should Alacorder OVERWRITE existing files at provided output file paths? [y/N]", type=bool)
            elif p == "launch" or p == "--launch":
                launch = click.prompt("Should Alacorder attempt to launch exported files once complete? [y/N]",
                                      type=bool)
            elif p == "dedupe" or p == "--dedupe" or p == "-dd":
                dedupe = click.prompt("Should Alacorder attempt to remove duplicate cases from outputs? [y/N]",
                                      type=bool)
            elif p == "log" or p == "--log" or p == "no-log" or p == "--no-log":
                log = click.prompt("Should Alacorder print logs to console? [y/N]", type=bool)
            elif p == "no_prompt" or p == "--no-prompt" or p == "-np":
                no_prompt = click.prompt("Should Alacorder proceed without prompting for user input? [y/N]", type=bool)
            elif p == "debug" or p == "--debug" or p == "-d":
                debug = click.prompt("Should Alacorder print detailed debug logs? [y/N]", type=bool)
            elif p == "no_batch" or p == "--no-batch":
                no_batch = click.prompt("Should Alacorder process all cases in one batch? [y/N]", type=bool)
            elif p == "compress" or p == "--compress":
                compress = click.prompt("Should Alacorder compress exports? [y/N]", type=bool)
            elif p == "table" or p == "--table" or p == "-t":
                pick = click.prompt(cal.pick_table())  # add str
                if pick == "A":
                    table = "cases"
                elif pick == "B":
                    table = "fees"
                elif pick == "C":
                    table = "charges"
                elif pick == "D":
                    table = "disposition"
                elif pick == "E":
                    table = "filing"
                else:
                    click.echo("Option not found.")
            if debug:
                click.echo(p)

    # finalize config
    cf = cal.set(inputs, outputs, count=count, table=table, overwrite=overwrite, launch=launch, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)

    if debug:
        click.echo(cf)
    if log:
        click.echo(cf.ECHO)

    if cf.MAKE == "archive":
        o = cal.archive(cf)
        cal.logdebug(cf, o.describe())
    if cf.MAKE == "multiexport" and cf.TABLE == "all":
        o = cal.cases(cf)
        cal.logdebug(cf, o[0].describe())
        cal.logdebug(cf, o[1].describe())
        cal.logdebug(cf, o[2].describe())
    if cf.TABLE == "fees":
        o = cal.fees(cf)
        cal.logdebug(cf, o.describe())
    if cf.TABLE == "charges" or cf.TABLE == "disposition" or cf.TABLE == "filing":
        o = cal.charges(cf)
        cal.logdebug(cf, o.describe())
    if cf.TABLE == "cases":
        o = cal.caseinfo(cf)
        cal.logdebug(cf, o.describe())


if __name__ == "__main__":
    cli()
