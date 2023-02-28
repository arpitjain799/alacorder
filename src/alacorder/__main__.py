# main 76
# sam robson

import warnings
import cython
import pyximport; pyximport.install()
try:
    import cal
except:
    from alacorder import alac as cal
import os
import sys
import click
import pandas as pd

warnings.filterwarnings('ignore')

pd.set_option("mode.chained_assignment", None)
pd.set_option("display.notebook_repr_html", True)
pd.set_option("display.width", None)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)

## COMMAND LINE INTERFACE

@click.command()
@click.option('--input-path', '-in', required=True, type=click.Path(), prompt=cal.title(),
              help="Path to input archive or PDF directory", show_choices=False)
@click.option('--output-path', '-out', required=True, type=click.Path(), prompt=cal.both(), help="Path to output table (.xls, .xlsx, .csv, .json, .dta) or archive (.pkl.xz, .json.zip, .parquet)")
@click.option('--table', '-t', help="Table export choice (cases, fees, charges, disposition, filing, or all)")
@click.option('--archive', '-a', is_flag=True, help="Create full text archive at output path")
@click.option('--count', '-c', default=0, help='Total cases to pull from input', show_default=False)
@click.option('--dedupe / --ignore','dedupe', default=True, is_flag=True, help="Remove duplicate cases from archive outputs")
@click.option('--compress','-z', default=False, is_flag=True,
              help="Compress exported file (archives compress with or without flag)")
@click.option('--overwrite', '-o', default=False, help="Overwrite existing files at output path", is_flag=True,show_default=False)
@click.option('--no-log','-q','log', default=False, is_flag=True, help="Don't print logs or progress to console")
@click.option('--no-write','-n', default=False, is_flag=True, help="Do not export to output path", hidden=True)
@click.option('--no-prompt', '-p', default=False, is_flag=True, help="Skip user input / confirmation prompts")
@click.option('--debug','-d', default=False, is_flag=True, help="Print extensive logs to console for developers")
@click.option('--no-batch','-b', default=False, is_flag=True, help="Process all inputs as one batch")
@click.version_option(package_name='alacorder', prog_name='ALACORDER', message='%(prog)s beta %(version)s')
def cli(input_path, output_path, count, table, archive, overwrite, dedupe, log, no_write, no_prompt, debug, no_batch,
        compress):

    ogtable = table
    ogarchive = archive

    log = not log 

    show_options_menu = True if no_prompt == False and overwrite == False and dedupe == True and log == True and no_write == False and no_prompt == False and debug == False and no_batch == False and compress == False else False

    # assume archive if .zip and no table spec
    if (table == "" or table == None) and archive != True and (os.path.splitext(output_path)[1] == ".zip" or compress == True):
        archive = True
        if log or debug:
            click.echo("Defaulting to archive... To reconfigure in tables mode, specify table with --table flag.")

    if archive == True:
        table == ""

    # suppress tracebacks unless debug
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    else:
        sys.tracebacklimit = 10

    # inputs - configure and log
    inputs = cal.setinputs(input_path)
    if debug:
        click.echo(inputs)
    if log:
        click.echo(inputs.ECHO)
    if not inputs.GOOD:
        raise Exception("Invalid input path!")

    # outputs - configure and log
    outputs = cal.setoutputs(output_path,archive=archive)
    if debug:
        click.echo(outputs)
    if log:
        click.echo(outputs.ECHO)
    if not outputs.GOOD:
        raise Exception("Invalid output path!")

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
            if pick == "A" or pick == "archive":
                table = ""
                archive = True
            elif pick == "B" or pick == "cases":
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
                cal.echo_yellow("Invalid table selection!", echo=True)

    #if outputs.MAKE == "archive" or archive == True:
     #   compress = True

    # prompt options
    change = False

    if show_options_menu and not no_prompt:
        if not click.confirm("Continue with current settings?"):
            change = True
            cli.main(['alacorder', '--help'], standalone_mode=False)
            p = click.prompt('\nEnter the <option> you would like to set, or type \'skip\' to start with current settings.')
            if p == "count" or p == "-c" or p == "--count":
                count = click.prompt("Set total case count to pull from input", type=int)
            elif p == "skip":
                pass
            elif p == "overwrite" or p == "--overwrite" or p == "-o":
                overwrite = click.prompt(
                    "Should Alacorder OVERWRITE any existing files at output file paths? [y/N]", type=bool)
            elif p == "dedupe" or p == "--dedupe" or p == "ignore" or p == "--ignore":
                dedupe = click.prompt("Should Alacorder remove duplicate cases from outputs? [y/N]", type=bool)
            elif p == "log" or p == "--log" or p == "no-log" or p == "--no-log" or p == "nl" or p == "-nl" or p == "no log" or p == "-n":
                log = click.prompt("Should Alacorder print logs to console? [y/N]", type=bool)
            elif p == "no_prompt" or p == "--no-prompt" or p == "-np" or p == "np" or p == "p" or p == "-p":
                no_prompt = click.prompt("Should Alacorder proceed without prompting for user input? [y/N]", type=bool)
            elif p == "debug" or p == "--debug" or p == "-db" or p == "db" or p == "-d" or p == "d":
                debug = click.prompt("Should Alacorder print detailed debug logs? [y/N]", type=bool)
            elif p == "no_batch" or p == "--no-batch" or p == "-nb" or p == "nb" or p == "nobatch" or p == "no batch" or p == "-b" or p == "b":
                no_batch = click.prompt("Should Alacorder process all cases in one batch? [y/N]", type=bool)
            elif p == "compress" or p == "--compress" or p == "-zip" or p == "zip" or p == "-z" or p == "z":
                compress = click.prompt("Should Alacorder compress exports? [y/N]", type=bool)
            elif p == "archive" or p == "--archive" or p == "-a" or p == "-archive" or p == "a":
                archive = click.prompt("Should Alacorder create full text archive at output path? [y/N]", type=bool)
            elif p == "table" or p == "--table" or p == "-t" or p == "t":
                archive = False
                pick = click.prompt(cal.pick_table())
                if pick == "A" or pick == "archive":
                    table = ""
                    archive = True
                elif pick == "B" or pick == "cases":
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
                    cal.echo_yellow("Invalid table selection!", echo=True)
    
    if table != ogtable or archive != ogarchive:
        # inputs - configure and log
        inputs = cal.setinputs(input_path)
        if debug:
            click.echo(inputs)
        if log:
            click.echo(inputs.ECHO)
        if not inputs.GOOD:
            raise Exception("Invalid input path!")

        # outputs - configure and log
        outputs = cal.setoutputs(output_path,archive=archive)
        if debug:
            click.echo(outputs)
        if log:
            click.echo(outputs.ECHO)
        if not outputs.GOOD:
            raise Exception("Invalid output path!")

    # finalize config
    cf = cal.set(inputs, outputs, count=count, table=table, overwrite=overwrite, log=log, dedupe=dedupe, no_write=no_write, no_prompt=no_prompt, no_batch=no_batch, debug=debug, compress=compress)

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
