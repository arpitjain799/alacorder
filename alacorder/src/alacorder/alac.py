"""
 ALACORDER 79
 ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌
 ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││
 ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘
 (c) 2023 Sam Robson <sbrobson@crimson.ua.edu>

 Dependencies: 
    python = ^3.9
    brotli = ^1.0.9
    click = ^8.1.3
    polars = ^0.17.6
    PyMuPDF = ^1.21.1
    PySimpleGUI = ^4.60.4
    selenium = ^4.8.3
    tqdm = ^4.65.0
    xlsx2csv = ^0.8.1
    XlsxWriter = ^3.0.9
"""

name = "ALACORDER"
version = "79.8.9"
long_version = "partymountain"

autoload_graphical_user_interface = False

import polars as pl
import os, sys, time, glob, re
import click, fitz, selenium, xlsxwriter
from tqdm.auto import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

#   #   #   #               LOGS                 #   #   #   #

pl.Config.set_tbl_rows(20)
pl.Config.set_fmt_str_lengths(100)
pl.Config.set_tbl_width_chars(90)
pl.Config.set_tbl_formatting("NOTHING")
pl.Config.set_tbl_hide_column_data_types(True)
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

fname = f"{name} {version}"
fshort_name = f"{name} {'.'.join(version.split('.')[0:-1])}"

prt = print


def plog(*msg, cf=None):
    global prt
    if len(msg) == 1:
        msg = msg[0]
        if isinstance(cf, dict):
            try:
                if cf["LOG"] == True:
                    prt(msg)
            except:
                prt(msg)
        elif cf == None:
            prt(msg)
        elif type(cf) == bool and cf:
            prt(msg)
    elif len(msg) > 1:
        for m in msg:
            if isinstance(cf, dict):
                try:
                    if cf["LOG"] == True:
                        prt(m)
                except:
                    prt(m)
            elif cf == None:
                prt(m)
            elif type(cf) == bool and cf:
                prt(m)


print = plog


def dlog(*msg, cf=None):
    if type(cf) == bool:
        if cf:
            for m in msg:
                print(m)
            return msg
        else:
            return None
    elif type(cf) == dict:
        if cf["DEBUG"]:
            for m in msg:
                print(m)
            return msg
        else:
            return None
    else:
        return None


def error(*msg, cf=None):
    message = ""
    for m in msg:
        message += f"{m} "
    message = message.strip()
    if cf:
        if cf["WINDOW"]:
            cf["WINDOW"].write_event_value("POPUP", message)
        elif cf["FORCE"]:
            print(message)
        else:
            raise Exception(message)
    else:
        raise Exception(message)


def popup(*msg, cf=None):
    message = ""
    for m in msg:
        message += f"{m} "
    message = message.strip()
    if cf:
        if cf["WINDOW"]:
            cf["WINDOW"].write_event_value("POPUP", message)
        else:
            print(message)
    else:
        print(message)


#   #   #   #            TABLE PARSERS           #   #   #   #


def pairs(cf):
    """
    Create AIS / Unique ID pairs template using configuration object `cf`.
    """
    df = read(cf)
    tp = make_pairs_template(df)
    if not cf["NO_WRITE"]:
        write(
            tp, sheet_names=["Pairs"], path=cf["OUTPUT_PATH"], overwrite=cf["OVERWRITE"]
        )
    if cf["LOG"]:
        print("Created template successfully.")
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("MT-COMPLETE", True)
    return tp


def multi(cf):
    """
    Start multitable collection using configuration object `cf`.
    """
    df = read(cf)
    plog("Extracting case info...", cf=cf)
    ca, ac, af = split_cases(df, debug=cf["DEBUG"])
    print("Parsing charges...", cf=cf)
    ch = split_charges(ac, debug=cf["DEBUG"])
    print("Parsing fees...", cf=cf)
    fs = split_fees(af, debug=cf["DEBUG"])
    print("Parsing settings...", cf=cf)
    settings = explode_settings(df)
    print("Parsing case action summaries...", cf=cf)
    cas = explode_case_action_summary(df)
    print("Parsing witnesses...", cf=cf)
    wit = explode_witnesses(df)
    print("Parsing attorneys...", cf=cf)
    att = explode_attorneys(df)
    print("Parsing images...", cf=cf)
    img = explode_images(df)
    dlog(ca, ch, fs, settings, cas, wit, att, img, cf=cf)
    ch_filing = ch.filter(pl.col("Filing") == True).select(
        pl.exclude("CourtAction", "CourtActionDate")
    )
    ch_disposition = ch.filter(pl.col("Filing") == False)
    if not cf["NO_WRITE"]:
        print("Writing to export...", cf=cf)
        write(
            [ca, ch_filing, ch_disposition, fs, settings, cas, wit, att, img],
            sheet_names=[
                "cases",
                "filing-charges",
                "disposition-charges",
                "fees",
                "settings",
                "case-action-summary",
                "witnesses",
                "attorneys",
                "images",
            ],
            cf=cf,
        )
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    out = {
        "cases": ca,
        "charges": ch,
        "filing-charges": ch_filing,
        "disposition-charges": ch_disposition,
        "fees": fs,
        "settings": settings,
        "case-action-summary": cas,
        "witnesses": wit,
        "attorneys": att,
        "images": img,
    }
    return out


def cases(cf):
    """
    Start cases table collection using configuration object `cf`.
    """
    df = read(cf)
    print("Parsing case info...", cf=cf)
    ca, ac, af = split_cases(df)
    if not cf["NO_WRITE"]:
        print("Writing to export...")
        write(ca, cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return ca


def charges(cf):
    """
    Start charges table collection using configuration object `cf`.
    """
    df = read(cf)
    print("Parsing charges...", cf=cf)
    ac = explode_charges(df)
    ch = split_charges(ac)
    if not cf["NO_WRITE"]:
        print("Writing to export...", cf=cf)
        write(ch, cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return ch


def fees(cf):
    """
    Start fee sheet collection using configuration object `cf`.
    """
    df = read(cf)
    print("Parsing fee sheets...", cf=cf)
    af = explode_fees(df)
    fs = split_fees(af)
    if not cf["NO_WRITE"]:
        print("Writing to export...", cf=cf)
        write(fs, cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return fs


def witnesses(cf):
    """
    Collect witnesses tables using configuration object `cf`.
    """
    q = read(cf["QUEUE"])
    out = explode_witnesses(q)
    if not cf["NO_WRITE"]:
        write(out, sheet_names=["witnesses"], cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return out


def attorneys(cf):
    """
    Collect attorneys tables using configuration object `cf`.
    """
    q = read(cf["QUEUE"])
    out = explode_attorneys(q)
    if not cf["NO_WRITE"]:
        write(out, sheet_names=["attorneys"], cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return out


def settings(cf):
    """
    Collect settings tables using configuration object `cf`.
    """
    q = read(cf["QUEUE"])
    out = explode_settings(q)
    if not cf["NO_WRITE"]:
        write(out, sheet_names=["settings"], cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return out


def images(cf):
    """
    Collect images tables using configuration object `cf`.
    """
    q = read(cf["QUEUE"])
    out = explode_images(q)
    if not cf["NO_WRITE"]:
        write(out, sheet_names=["images"], cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return out


def vrr_summary(cf):
    """
    Summarize voting rights status from pairs using configuration object `cf`.
    """
    vr = vrr_summary_from_pairs(cf["INPUTS"], cf["PAIRS"])
    if not cf["NO_WRITE"]:
        write(
            vr, sheet_names=["VRR"], path=cf["OUTPUT_PATH"], overwrite=cf["OVERWRITE"]
        )
    if cf["LOG"]:
        print("Created table successfully.")
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("VRR-COMPLETE", True)
    return vr


def case_action_summary(cf):
    """
    Collect case action summaries using configuration object `cf`.
    """
    q = read(cf["QUEUE"])
    out = explode_case_action_summary(q)
    if not cf["NO_WRITE"]:
        write(out, sheet_names=["case-action-summary"], cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-TB", True)
    return out


def charges_summary(cf):
    """
    Summarize voting rights status from pairs using configuration object `cf`.
    """
    ch = charges_summary_from_pairs(cf["INPUTS"], cf["PAIRS"], debug=cf["DEBUG"])
    if not cf["NO_WRITE"]:
        write(
            ch,
            sheet_names=["ChargesSummary"],
            path=cf["OUTPUT_PATH"],
            overwrite=cf["OVERWRITE"],
        )
    if cf["LOG"]:
        print("Created table successfully.")
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("CHSUM-COMPLETE", True)
    return ch


def convictions_summary(cf):
    """
    Summarize voting rights status from pairs using configuration object `cf`.
    """
    conv = convictions_summary_from_pairs(cf["INPUTS"], cf["PAIRS"], debug=cf["DEBUG"])
    if not cf["NO_WRITE"]:
        write(
            conv,
            sheet_names=["ConvictionsSummary"],
            path=cf["OUTPUT_PATH"],
            overwrite=cf["OVERWRITE"],
        )
    if cf["LOG"]:
        print("Created table successfully.")
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("CONVSUM-COMPLETE", True)
    return conv


def init(cf):
    """
    Start Alacorder using configuration object `cf`.
    """
    if cf["FETCH"] == True:
        ft = fetch(cf=cf)
        return ft
    elif cf["ARCHIVE"] == True:
        ar = archive(cf)
        return ar
    elif cf["VRR_SUMMARY"] == True and cf["PAIRS"]:
        vr = vrr_summary(cf)
        return vr
    elif cf["CHARGES_SUMMARY"] == True and cf["PAIRS"]:
        ch = charges_summary(cf)
        return ch
    elif cf["CONVICTIONS_SUMMARY"] == True and cf["PAIRS"]:
        conv = convictions_summary(cf)
        return cf
    elif (
        cf["TABLE"].lower() in ("charges", "disposition", "filing")
        and cf["SUPPORT_SINGLETABLE"]
    ):
        ch = charges(cf)
        return ch
    elif cf["TABLE"].lower() in ("cases", "caseinfo") and cf["SUPPORT_SINGLETABLE"]:
        ca = cases(cf)
        return ca
    elif (
        cf["TABLE"].lower() in ("fees", "feesheet", "fines")
        and cf["SUPPORT_SINGLETABLE"]
    ):
        fs = fees(cf)
        return fs
    elif cf["TABLE"].lower() in ("witnesses", "witness") and cf["SUPPORT_SINGLETABLE"]:
        out = witnesses(cf)
        return out
    elif (
        cf["TABLE"].lower()
        in (
            "case-action-summary",
            "cas",
        )
        and cf["SUPPORT_SINGLETABLE"]
    ):
        out = case_action_summary(cf)
        return out
    elif cf["TABLE"].lower() in ("settings", "set") and cf["SUPPORT_SINGLETABLE"]:
        out = settings(cf)
        return out
    elif cf["TABLE"].lower() in ("images", "imgs", "img") and cf["SUPPORT_SINGLETABLE"]:
        out = images(cf)
        return out
    elif cf["TABLE"] in ("attorneys", "att") and cf["SUPPORT_SINGLETABLE"]:
        out = attorneys(cf)
        return out
    elif (
        cf["TABLE"].lower() in ("all", "", "multi", "multitable")
        and cf["SUPPORT_MULTITABLE"]
    ):
        mult = multi(cf)
        return mult
    else:
        print("Job not specified. Select a mode and reconfigure to start.")
        return None


def archive(cf):
    """
    Write a full text archive from inputs using configuration `cf`.
    """
    a = read(cf)
    write(a, cf=cf)
    if cf["WINDOW"]:
        cf["WINDOW"].write_event_value("COMPLETE-MA", True)
    return a


#   #   #   #         CONFIGURATION & I/O        #   #   #   #


def set(
    inputs,
    outputs=None,
    count=0,
    table="",
    archive=False,
    log=False,
    no_prompt=True,
    debug=False,
    overwrite=False,
    no_write=False,
    fetch=False,
    cID="",
    uID="",
    pwd="",
    qmax=0,
    qskip=0,
    pairs=None,
    vrr_summary=False,
    charges_summary=False,
    convictions_summary=False,
    append=False,
    window=None,
    force=False,
    no_update=False,
    now=False,
):
    """
    Check inputs and outputs and return a configuration object for Alacorder table parser functions to receive as parameter and complete task, or set `now = True` to run immediately.

    Args:
        inputs (Path | DataFrame): PDF directory, query, archive path, or DataFrame input
        outputs (Path | DataFrame, optional): Path to archive, directory, or file output
        count (int, optional): Max cases to pull from input
        table (str, optional): Table (all, cases, fees, charges, settings, witnesses, attorneys, case_action_summaries, images)
        archive (bool, optional): Write a full text archive from a directory of case detail PDFs
        log (bool, optional): Print logs and progress to console
        no_prompt (bool, optional): Skip user input / confirmation prompts
        debug (bool, optional): Print verbose logs to console for developers
        overwrite (bool, optional): Overwrite existing files at output path
        no_write (bool, optional): Do not export to output path
        fetch (bool, optional): Retrieve case detail PDFs from Alacourt.com
        cID (str, optional): Customer ID on Alacourt.com
        uID (str, optional): User ID on Alacourt.com
        pwd (str, optional): Password on Alacourt.com
        qmax (int, optional): Maximum queries to conduct on Alacourt.com
        qskip (int, optional): Skip entries at top of query file
        pairs (str, optional): Path to AIS / Unique ID pairs for grouped table functions
        vrr_summary (bool, optional): Create voting rights summary from pairs
        charges_summary (bool, optional): Create charges summary from pairs
        convictions_summary (bool, optional): Create convictions summary from pairs
        append (bool, optional): Append one archive to another
        window (None, optional): PySimpleGUI window element
        force (bool, optional): Do not raise exceptions
        no_update (bool, optional): Do not mark input query when fetching cases
        now (bool, optional): Start Alacorder upon successful configuration
    """
    return cf(
        inputs=inputs,
        outputs=outputs,
        count=count,
        table=table,
        archive=archive,
        log=log,
        no_prompt=no_prompt,
        debug=debug,
        overwrite=overwrite,
        no_write=no_write,
        fetch=fetch,
        cID=cID,
        uID=uID,
        pwd=pwd,
        qmax=qmax,
        qskip=qskip,
        pairs=pairs,
        vrr_summary=vrr_summary,
        charges_summary=charges_summary,
        convictions_summary=convictions_summary,
        append=append,
        window=window,
        force=force,
        no_update=no_update,
        now=now,
    )


def cf(
    inputs,
    outputs=None,
    count=0,
    table="",
    archive=False,
    log=False,
    no_prompt=True,
    debug=False,
    overwrite=False,
    no_write=False,
    fetch=False,
    cID="",
    uID="",
    pwd="",
    qmax=0,
    qskip=0,
    pairs=None,
    vrr_summary=False,
    charges_summary=False,
    convictions_summary=False,
    append=False,
    window=None,
    force=False,
    no_update=False,
    now=False,
):
    """
    Check inputs and outputs and return a configuration object for Alacorder table parser functions to receive as parameter and complete task, or set `now = True` to run immediately.

    Args:
        inputs (Path | DataFrame): PDF directory, query, archive path, or DataFrame input
        outputs (Path | DataFrame, optional): Path to archive, directory, or file output
        count (int, optional): Max cases to pull from input
        table (str, optional): Table (all, cases, fees, charges, settings, witnesses, attorneys, case_action_summaries, images)
        archive (bool, optional): Write a full text archive from a directory of case detail PDFs
        log (bool, optional): Print logs and progress to console
        no_prompt (bool, optional): Skip user input / confirmation prompts
        debug (bool, optional): Print verbose logs to console for developers
        overwrite (bool, optional): Overwrite existing files at output path
        no_write (bool, optional): Do not export to output path
        fetch (bool, optional): Retrieve case detail PDFs from Alacourt.com
        cID (str, optional): Customer ID on Alacourt.com
        uID (str, optional): User ID on Alacourt.com
        pwd (str, optional): Password on Alacourt.com
        qmax (int, optional): Maximum queries to conduct on Alacourt.com
        qskip (int, optional): Skip entries at top of query file
        pairs (str, optional): Path to AIS / Unique ID pairs for grouped table functions
        vrr_summary (bool, optional): Create voting rights summary from pairs
        charges_summary (bool, optional): Create charges summary from pairs
        convictions_summary (bool, optional): Create convictions summary from pairs
        append (bool, optional): Append one archive to another
        window (None, optional): PySimpleGUI window element
        force (bool, optional): Do not raise exceptions
        no_update (bool, optional): Do not mark input query when fetching cases
        now (bool, optional): Start Alacorder upon successful configuration
    """
    good = True
    outputs = None if no_write else outputs
    no_write = True if outputs == None else no_write
    found = 0

    if debug:
        sys.tracebacklimit = 10
        pl.Config.set_verbose(True)
        pl.Config.set_tbl_rows(100)
    else:
        sys.tracebacklimit = 2
        pl.Config.set_verbose(False)

    # raise overwrite error
    if no_write:
        outputext = "none"
        existing_output = False
    elif os.path.isdir(outputs):
        outputext = "directory"
        existing_output = False
    elif os.path.isfile(outputs):
        if not overwrite and not append:
            error(
                "Error: Existing file at output path.\nRepeat in overwrite mode to continue.",
                cf={"WINDOW": window, "FORCE": force},
            )
        outputext = os.path.splitext(outputs)[1]
        existing_output = True
    else:
        outputext = os.path.splitext(str(outputs))[1]
        existing_output = False

    support_multitable = True if outputext in (".xls", ".xlsx", "none") else False
    support_singletable = (
        True
        if outputext in (".xls", ".xlsx", "none", ".json", ".parquet", ".csv")
        else False
    )
    support_archive = (
        True
        if outputext in (".xls", ".xlsx", ".csv", ".parquet", ".zip", ".json", "none")
        else False
    )
    if force not in (  # raise file extension not supported
        ".xls",
        ".xlsx",
        ".csv",
        ".parquet",
        ".json",
        ".csv",
        "none",
        "directory",
    ) and outputext not in (
        ".xls",
        ".xlsx",
        ".csv",
        ".parquet",
        ".json",
        ".csv",
        "none",
        "directory",
    ):
        error(
            "Error: File extension not supported.\nRepeat with .xls, .xlsx, .parquet, .csv, or .json.",
            cf={"WINDOW": window, "FORCE": force},
        )

    if (  # raise no table selection
        support_multitable == False
        and archive == False
        and fetch == False
        and table
        not in (
            "cases",
            "charges",
            "fees",
            "disposition",
            "disposition-charges",
            "filing",
            "filing-charges",
            "attorneys",
            "settings",
            "images",
            "case-action-summary",
            "witnesses",
        )
    ):
        error(
            "Single table export choice required! (cases, charges, fees, disposition, filing, settings, attorneys, images, case-action-summary, witnesses)",
            cf={"WINDOW": window, "FORCE": force},
        )

    if archive and append and existing_output and not no_write:  # raise append failure
        try:
            old_archive = read(outputs)
        except:
            error(
                "Append failed! Archive at output path could not be read.",
                cf={"WINDOW": window, "FORCE": force},
            )

    if isinstance(inputs, pl.dataframe.frame.DataFrame):  # DataFrame inputs
        if not force and not "AllPagesText" in inputs.columns:
            error(
                "Alacorder could not read archive. Try again with another file.",
                cf={"WINDOW": window, "FORCE": force},
            )
        elif not force and not "ALABAMA" in inputs["AllPagesText"][0]:
            error(
                "Alacorder could not read archive. Try again with another file.",
                cf={"WINDOW": window, "FORCE": force},
            )
        queue = inputs
        found = queue.shape[0]
        is_full_text = True
        itype = "object"
    elif isinstance(inputs, pl.series.series.Series):  # series input
        if not force and not "AllPagesText" in pl.DataFrame(inputs).columns:
            error(
                "Alacorder could not read archive. Try again with another file.",
                cf={"WINDOW": window, "FORCE": force},
            )
        elif not force and not "ALABAMA" in inputs[0]:
            error(
                "Alacorder could not read archive. Try again with another file.",
                cf={"WINDOW": window, "FORCE": force},
            )
        queue = inputs
        found = queue.shape[0]
        is_full_text = True
        itype = "object"
    elif os.path.isdir(inputs):  # directory inputs
        queue = glob.glob(inputs + "**/*.pdf", recursive=True)
        found = len(queue)
        if not force and not found > 0:
            error("No cases found in archive.", cf={"WINDOW": window, "FORCE": force})
        is_full_text = False
        itype = "directory"
    elif os.path.isfile(inputs):  # file inputs
        queue = read(inputs)
        found = queue.shape[0]
        is_full_text = True
        itype = (
            "query" if os.path.splitext(inputs)[1] in (".xls", ".xlsx") else "archive"
        )
    else:
        error("Failed to determine input type.", cf={"WINDOW": window, "FORCE": force})

    if count == 0:
        count = found
    if count > found:
        count = found
    if found > count:
        queue = queue[0:count]

    out = {
        "QUEUE": queue,
        "INPUTS": inputs,
        "NEEDTEXT": bool(not is_full_text),
        "INPUT_TYPE": itype,
        "FOUND": found,
        "COUNT": count,
        "OUTPUT_PATH": outputs,
        "OUTPUT_EXT": outputext,
        "SUPPORT_MULTITABLE": support_multitable,
        "SUPPORT_SINGLETABLE": support_singletable,
        "SUPPORT_ARCHIVE": support_archive,
        "TABLE": table,
        "ARCHIVE": archive,
        "PAIRS": pairs,
        "VRR_SUMMARY": vrr_summary,
        "CHARGES_SUMMARY": charges_summary,
        "CONVICTIONS_SUMMARY": convictions_summary,
        "APPEND": append,
        "NO_UPDATE": no_update,
        "FETCH": fetch,
        "ALA_CUSTOMER_ID": cID,
        "ALA_USER_ID": uID,
        "ALA_PASSWORD": pwd,
        "FETCH_SKIP": qskip,
        "FETCH_MAX": qmax,
        "LOG": log,
        "NO_WRITE": no_write,
        "NO_PROMPT": no_prompt,
        "OVERWRITE": overwrite,
        "EXISTING_OUTPUT": existing_output,
        "DEBUG": debug,
        "WINDOW": window,
    }
    dlog(out, cf=debug)
    if now:
        return init(out)
    return out


def read(cf):
    """
    Read `cf` input PDF directory or case text archive into memory.
    """
    if isinstance(cf, pl.dataframe.frame.DataFrame):  # df input
        df = cf
        if "AllPagesTextNoNewLine" not in df.columns and "AllPagesText" in df.columns:
            df = df.with_columns(
                pl.col("AllPagesText")
                .str.replace_all(r"\n", " ")
                .alias("AllPagesTextNoNewLine")
            )
            return df
        else:
            return df
    elif isinstance(cf, list):  # [paths] input
        queue = cf
        aptxt = []
        for pp in queue:
            aptxt += [extract_text(pp)]
        archive = pl.DataFrame(
            {"Timestamp": time.time(), "AllPagesText": aptxt, "Path": queue}
        )
        archive = archive.with_columns(
            pl.col("AllPagesText")
            .str.replace_all(r"\n", " ")
            .alias("AllPagesTextNoNewLine")
        )
        return archive
    elif isinstance(cf, dict):  # cf input
        if cf["NEEDTEXT"] == False or "ALABAMA" in cf["QUEUE"][0]:
            return cf["QUEUE"]
        if cf["NEEDTEXT"] == True:
            queue = cf["QUEUE"]
            aptxt = []
            print("Extracting text...", cf=cf)
            if cf["WINDOW"]:
                cf["WINDOW"].write_event_value("PROGRESS_TOTAL", len(queue))
                for i, pp in enumerate(queue):
                    aptxt += [extract_text(pp)]
                    cf["WINDOW"].write_event_value("PROGRESS", i + 1)
            elif cf["LOG"]:
                for pp in tqdm(queue):
                    aptxt += [extract_text(pp)]
            else:
                for pp in queue:
                    aptxt += [extract_text(pp)]
        archive = pl.DataFrame(
            {"Timestamp": time.time(), "AllPagesText": aptxt, "Path": queue}
        )
        archive = archive.with_columns(
            pl.col("AllPagesText")
            .str.replace_all(r"\n", " ")
            .alias("AllPagesTextNoNewLine")
        )
        return archive
    elif os.path.isdir(cf):  # directory path input
        queue = glob.glob(cf + "**/*.pdf", recursive=True)
        aptxt = []
        print("Extracting text...", cf=cf)
        if cf["WINDOW"]:
            cf["WINDOW"].write_event_value("PROGRESS_TOTAL", len(queue))
            for i, pp in enumerate(queue):
                aptxt += [extract_text(pp)]
                cf["WINDOW"].write_event_value("PROGRESS", i + 1)
        elif cf["LOG"]:
            for pp in tqdm(queue):
                aptxt += [extract_text(pp)]
        else:
            for pp in queue:
                aptxt += [extract_text(pp)]
        archive = pl.DataFrame(
            {"Timestamp": time.time(), "AllPagesText": aptxt, "Path": queue}
        )
        archive = archive.with_columns(
            pl.col("AllPagesText")
            .str.replace_all(r"\n", " ")
            .alias("AllPagesTextNoNewLine")
        )
        return archive
    elif os.path.isfile(cf):  # file path input
        ext = os.path.splitext(cf)[1]
        if ext in (".xls", ".xlsx"):
            archive = pl.read_excel(
                cf,
                xlsx2csv_options={"ignore_errors": True},
                read_csv_options={"ignore_errors": True},
            )
            return archive
        elif ext == ".json":
            archive = pl.read_json(cf)
            if "AllPagesText" in archive.columns:
                archive = archive.with_columns(
                    pl.col("AllPagesText")
                    .str.replace_all(r"\n", " ")
                    .alias("AllPagesTextNoNewLine")
                )
            return archive
        elif ext == ".csv":
            archive = pl.read_csv(cf, ignore_errors=True)
            if "AllPagesText" in archive.columns:
                archive = archive.with_columns(
                    pl.col("AllPagesText")
                    .str.replace_all(r"\n", " ")
                    .alias("AllPagesTextNoNewLine")
                )
            return archive
        elif ext == ".parquet":
            archive = pl.read_parquet(cf)
            if "AllPagesText" in archive.columns:
                archive = archive.with_columns(
                    pl.col("AllPagesText")
                    .str.replace_all(r"\n", " ")
                    .alias("AllPagesTextNoNewLine")
                )
            return archive
    else:
        return None


def write(outputs, sheet_names=[], cf=None, path=None, overwrite=False):
    """Write `outputs` to output path at `cf['OUTPUT_PATH']` or `path`.

    Args:
        outputs ([DataFrame]): DataFrame(s) to write to output
        sheet_names (List[str], optional): Output Excel worksheet names

        cf (dict): Configuration object

        or:
            path (str): Output path
            overwrite (bool): Allow overwrite
    """
    if cf == None:
        cf = {
            "OUTPUT_PATH": path,
            "OUTPUT_EXT": os.path.splitext(path)[1],
            "NO_WRITE": False,
            "OVERWRITE": True,
            "FORCE": False,
        }
    else:  # cf trumps params if both given
        path = cf["OUTPUT_PATH"]
        overwrite = cf["OVERWRITE"]
    if isinstance(outputs, list):
        if len(outputs) != len(sheet_names) and len(outputs) != 1:
            error(
                "alac.write() missing sheet_names parameter. See documentation for details.",
                cf=cf,
            )
    if isinstance(outputs, pl.dataframe.frame.DataFrame):  # df input
        if "AllPagesTextNoNewLine" in outputs.columns:
            outputs = outputs.select(pl.exclude("AllPagesTextNoNewLine"))
    if cf["NO_WRITE"] == True:
        return outputs
    elif not cf["OVERWRITE"] and os.path.isfile(cf["OUTPUT_PATH"]):
        error(
            "Could not write to output path because overwrite mode is not enabled.",
            cf=cf,
        )
    elif cf["OUTPUT_EXT"] in (".xlsx", ".xls"):
        with xlsxwriter.Workbook(cf["OUTPUT_PATH"]) as workbook:
            if not isinstance(outputs, list):
                outputs = [outputs]
            if len(sheet_names) > 0:
                for i, x in enumerate(outputs):
                    x.write_excel(
                        workbook=workbook,
                        worksheet=sheet_names[i],
                        autofit=True,
                        float_precision=2,
                    )
            else:
                outputs[0].write_excel(
                    workbook=workbook, autofit=True, float_precision=2
                )
    elif cf["OUTPUT_EXT"] == ".parquet":
        outputs.write_parquet(cf["OUTPUT_PATH"], compression="brotli")
    elif cf["OUTPUT_EXT"] == ".json":
        outputs.write_json(cf["OUTPUT_PATH"])
    elif cf["OUTPUT_EXT"] in (".csv", ".txt"):
        outputs.write_csv(cf["OUTPUT_PATH"])
    elif cf["OUTPUT_EXT"] not in ("none", "", "directory", None):
        outputs.write_csv(cf["OUTPUT_PATH"])
    else:
        pass
    return outputs


#   #   #   #           TABLE PARSERS           #   #   #   #


def append_archive(inpath="", outpath="", cf=None):
    """
    Append the contents of one archive to another.

    Args:
        inpath (str): Input archive
        outpath (str): Output archive
        cf (dict): Configuration object

    Returns:
        DataFrame: Appended archive object
    """
    if cf and inpath == "":
        inpath = cf["INPUTS"]

    if cf and outpath == "":
        outpath = cf["OUTPUT_PATH"]

    if not os.path.isfile(inpath) and not os.path.isfile(outpath):
        error("Error: Invalid path.", cf=cf)

    inarc = read(inpath)
    outarc = read(outpath)

    try:
        inarc = inarc.select("AllPagesText", "Path", "Timestamp")
        outarc = outarc.select("AllPagesText", "Path", "Timestamp")
    except:
        try:
            dlog(inarc, outarc, cf=conf)
            print("Warning: Could not find column Timestamp in archive.")
            inarc = inarc.select("AllPagesText", "Path")
            outarc = outarc.select("AllPagesText", "Path")
        except:
            dlog(inarc, outarc, cf=conf)
            print("Warning: Could not find column Path in archive.")
            inarc = inarc.select("AllPagesText")
            outarc = outarc.select("AllPagesText")

    out = pl.concat([inarc, outarc])

    if window:
        window.write_event_value("COMPLETE-AA", True)
    write(out, path=outpath, overwrite=True)
    return out


def make_pairs_template(df, debug=False):
    if isinstance(df, str):
        df = read(df)
    names = df.with_columns(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(
                r"(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*",
                group_index=1,
            )
            .str.replace_all("Case Number:", "", literal=True)
            .str.replace(r"C$", "")
            .str.strip()
            .alias("Name"),
            pl.col("AllPagesText")
            .str.extract(r"(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)", group_index=1)
            .str.replace_all(r"[^\d/]", "")
            .str.strip()
            .alias("DOB"),
            pl.col("AllPagesText")
            .str.extract(r"(SSN)(.+)(Alias)", group_index=2)
            .str.replace(r"(SSN)", "")
            .str.replace(r"Alias", "")
            .str.replace(r"\:", "")
            .str.strip()
            .alias("Alias"),
        ]
    )
    names = (
        names.groupby("Name")
        .agg("CaseNumber", "DOB")
        .select(
            [
                pl.lit("").alias("AIS / Unique ID"),
                pl.col("Name"),
                pl.col("Alias").arr.get(0).str.replace("null", ""),
                pl.col("DOB").arr.get(0),
                pl.col("CaseNumber").arr.lengths().alias("CaseCount"),
                pl.col("CaseNumber").arr.join(", ").alias("Cases"),
            ]
        )
    )
    names = names.sort("Name")
    return names


def charges_summary_from_pairs(src, pairs, debug=False):
    if isinstance(src, str):
        arc = read(src)
        src = cf(arc, table="all", no_write=True, now=True)
    if isinstance(pairs, str):
        pairs = read(pairs)
    summary = (
        src["cases"]
        .join(pairs, on="Name", how="inner")
        .groupby("AIS / Unique ID")
        .agg("Name", "Alias", "DOB", "CaseNumber", "Race", "Sex")
    )
    ch = src["charges"].filter(pl.col("Filing"))  # filter convictions
    summary = summary.select(  # prepare summary for join w/ convictions
        [
            pl.col("AIS / Unique ID"),
            pl.col("Name").arr.get(0).alias("Name"),
            pl.col("Alias").arr.get(0).alias("Alias"),
            pl.col("DOB").arr.get(0),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("CaseNumber").arr.join(", "),
        ]
    )
    summary = summary.join(ch, on="Name", how="outer")  # join cases, convictions
    summary = summary.groupby("Name").agg(
        [
            pl.col("AIS / Unique ID"),
            pl.col("DOB"),
            pl.col("Race"),
            pl.col("Sex"),
            pl.col("CaseNumber"),
            pl.col("Alias"),
            pl.col("Cite"),
            pl.col("ChargesSummary"),
            pl.col("TypeDescription"),
            pl.col("CERVDisqCharge"),
            pl.col("PardonDisqCharge"),
            pl.col("PermanentDisqCharge"),
        ]
    )
    summary = summary.select(
        [
            pl.col("AIS / Unique ID").arr.get(0).cast(pl.Utf8).alias("AIS / Unique ID"),
            pl.col("Name"),
            pl.col("DOB").arr.get(0).alias("DOB"),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("ChargesSummary").arr.lengths().alias("ChargeCount"),
            pl.col("CERVDisqCharge").arr.count_match(True).alias("CERVChargeCount"),
            pl.col("PardonDisqCharge").arr.count_match(True).alias("PardonChargeCount"),
            pl.col("TypeDescription")
            .arr.count_match("MISDEMEANOR")
            .alias("MisdemeanorChargeCount"),
            pl.col("TypeDescription")
            .arr.count_match("FELONY")
            .alias("FelonyChargeCount"),
            pl.col("TypeDescription")
            .arr.count_match("TRAFFIC")
            .alias("TrafficChargeCount"),
            pl.col("PermanentDisqCharge")
            .arr.count_match(True)
            .alias("PermanentChargeCount"),
            pl.col("ChargesSummary")
            .arr.join(", ")
            .str.replace(r"null", "")
            .alias("ChargesSummary"),
        ]
    )
    summary = summary.filter(pl.col("Name") != "")
    summary = summary.fill_null("")
    return summary


def convictions_summary_from_pairs(src, pairs, debug=False):
    if isinstance(src, str):
        arc = read(src)
        src = cf(arc, table="all", no_write=True, now=True)
    if isinstance(pairs, str):
        pairs = read(pairs)
    summary = (
        src["cases"]
        .join(pairs, on="Name", how="inner")
        .groupby("AIS / Unique ID")
        .agg("Name", "Alias", "DOB", "CaseNumber", "Race", "Sex")
    )
    conv = src["charges"].filter(pl.col("Conviction"))  # filter convictions
    summary = summary.select(  # prepare summary for join w/ convictions
        [
            pl.col("AIS / Unique ID"),
            pl.col("Name").arr.get(0).alias("Name"),
            pl.col("Alias").arr.get(0).alias("Alias"),
            pl.col("DOB").arr.get(0),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("CaseNumber").arr.join(", "),
        ]
    )
    summary = summary.join(conv, on="Name", how="outer")  # join cases, convictions
    summary = summary.groupby("Name").agg(
        [
            pl.col("AIS / Unique ID"),
            pl.col("DOB"),
            pl.col("CaseNumber"),
            pl.col("Alias"),
            pl.col("Race"),
            pl.col("Sex"),
            pl.col("Cite"),
            pl.col("ChargesSummary"),
            pl.col("TypeDescription"),
            pl.col("CourtAction"),
            pl.col("CERVDisqConviction"),
            pl.col("PardonDisqConviction"),
            pl.col("PermanentDisqConviction"),
            pl.col("TotalBalance"),
            pl.col("PaymentToRestore"),
        ]
    )
    summary = summary.select(
        [
            pl.col("AIS / Unique ID").arr.get(0).cast(pl.Utf8).alias("AIS / Unique ID"),
            pl.col("Name"),
            pl.col("DOB").arr.get(0).alias("DOB"),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("ChargesSummary").arr.lengths().alias("ConvictionCount"),
            pl.col("CERVDisqConviction")
            .arr.count_match(True)
            .alias("CERVConvictionCount"),
            pl.col("PardonDisqConviction")
            .arr.count_match(True)
            .alias("PardonConvictionCount"),
            pl.col("TypeDescription")
            .arr.count_match("MISDEMEANOR")
            .alias("MisdemeanorConvictionCount"),
            pl.col("TypeDescription")
            .arr.count_match("FELONY")
            .alias("FelonyConvictionCount"),
            pl.col("TypeDescription")
            .arr.count_match("TRAFFIC")
            .alias("TrafficConvictionCount"),
            pl.col("CourtAction").arr.count_match("GUILTY").alias("GuiltyPleaCount"),
            pl.col("PermanentDisqConviction")
            .arr.count_match(True)
            .alias("PermanentConvictionCount"),
            pl.col("TotalBalance").arr.sum(),
            pl.col("PaymentToRestore").arr.sum(),
            pl.col("ChargesSummary")
            .arr.join(", ")
            .str.replace(r"null", "")
            .alias("ChargesSummary"),
        ]
    )
    summary = summary.filter(pl.col("Name") != "")
    summary = summary.fill_null("")
    return summary


def vrr_summary_from_pairs(src, pairs, debug=False):
    if isinstance(src, str):
        arc = read(src)
        src = cf(arc, table="all", no_write=True, now=True)
    if isinstance(pairs, str):
        pairs = read(pairs)
    summary = (  # pair AIS to cases sheet
        src["cases"]
        .join(pairs, on="Name", how="inner")
        .groupby("AIS / Unique ID")
        .agg("Name", "Alias", "DOB", "CaseNumber", "Race", "Sex")
    )
    disq = src["charges"].filter(  # filter disqualifying convictions
        pl.col("CERVDisqConviction")
        | pl.col("PardonDisqConviction")
        | pl.col("PermanentDisqConviction")
    )
    summary = summary.select(  # prepare summary for join w/ convictions
        [
            pl.col("AIS / Unique ID"),
            pl.col("Name").arr.get(0).alias("Name"),
            pl.col("Alias").arr.get(0).alias("Alias"),
            pl.col("DOB").arr.get(0),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("CaseNumber").arr.join(", "),
        ]
    )
    summary = summary.join(disq, on="Name", how="outer")  # join cases, convictions
    summary = summary.groupby("Name").agg(
        [
            pl.col("AIS / Unique ID"),
            pl.col("DOB"),
            pl.col("CaseNumber"),
            pl.col("Race"),
            pl.col("Sex"),
            pl.col("Alias"),
            pl.col("Cite"),
            pl.col("ChargesSummary"),
            pl.col("CERVDisqConviction"),
            pl.col("PardonDisqConviction"),
            pl.col("PermanentDisqConviction"),
            pl.col("TotalBalance"),
            pl.col("PaymentToRestore"),
        ]
    )
    summary = summary.select(
        [
            pl.col("AIS / Unique ID").arr.get(0).cast(pl.Utf8).alias("AIS / Unique ID"),
            pl.col("Name"),
            pl.col("DOB").arr.get(0).alias("DOB"),
            pl.col("Race").arr.get(0),
            pl.col("Sex").arr.get(0),
            pl.col("CERVDisqConviction")
            .arr.count_match(True)
            .alias("CERVConvictionCount"),
            pl.col("PardonDisqConviction")
            .arr.count_match(True)
            .alias("PardonConvictionCount"),
            pl.col("PermanentDisqConviction")
            .arr.count_match(True)
            .alias("PermanentConvictionCount"),
            pl.col("TotalBalance").arr.sum(),
            pl.col("PaymentToRestore").arr.sum(),
            pl.col("ChargesSummary")
            .arr.join(", ")
            .str.replace(r"null", "")
            .alias("ChargesSummary"),
        ]
    )
    summary = summary.filter(pl.col("Name") != "")
    summary = summary.fill_null("")
    return summary


def explode_charges(df, debug=False):
    all_charges = df.with_columns(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(
                r"(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*",
                group_index=1,
            )
            .str.replace_all("Case Number:", "", literal=True)
            .str.replace(r"C$", "")
            .str.strip()
            .alias("Name"),
            pl.col("AllPagesText")
            .str.extract_all(
                r"(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{0,75})"
            )
            .alias("RE_Charges"),
            pl.col("AllPagesText")
            .str.extract(r"(Total:.+\$[^\n]*)")
            .str.replace_all(r"[^0-9|\.|\s|\$]", "")
            .str.extract_all(r"\s\$\d+\.\d{2}")
            .arr.get(2)
            .str.replace_all(r"[^0-9\.]", "")
            .cast(pl.Float64, strict=False)
            .alias("RAWTotalBalance"),
            pl.col("AllPagesText")
            .str.extract(r"(ACTIVE[^\n]+D999[^\n]+)")
            .str.extract_all(r"\$\d+\.\d{2}")
            .arr.get(-1)
            .str.replace(r"[\$\s]", "")
            .cast(pl.Float64, strict=False)
            .alias("RAWD999"),
        ]
    )

    all_charges = all_charges.explode("RE_Charges").select(
        [
            pl.col("Name"),
            pl.col("CaseNumber"),
            pl.col("RE_Charges")
            .str.replace_all(r"[A-Z][a-z][A-Za-z\s\$]+.+", "")
            .str.strip()
            .alias("Charges"),
            pl.when(pl.col("RAWTotalBalance").is_null())
            .then(pl.lit(0.0))
            .otherwise(pl.col("RAWTotalBalance"))
            .alias("TotalBalance"),
            pl.when(pl.col("RAWD999").is_null())
            .then(pl.lit(0.0))
            .otherwise(pl.col("RAWD999"))
            .alias("TotalD999"),
        ]
    )

    dlog(all_charges, all_charges.columns, cf=debug)
    return all_charges


def explode_fees(df, debug=False):
    cases = df.with_columns(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract_all(
                r"(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^\n]*)"
            )
            .alias("RE_Fees"),
        ]
    )
    all_fees = cases.explode("RE_Fees").select(
        [
            pl.col("CaseNumber"),
            pl.col("RE_Fees")
            .str.replace_all(r"[^A-Z0-9|\.|\s|\$|\n]", " ")
            .str.strip()
            .alias("Fees"),
        ]
    )
    dlog(all_fees.columns, cf=debug)
    return all_fees


def split_cases(df, debug=False):
    cases = df.with_columns(
        [
            pl.col("AllPagesText")
            .str.extract(
                r"(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*",
                group_index=1,
            )
            .str.replace_all("Case Number:", "", literal=True)
            .str.replace(r"C$", "")
            .str.strip()
            .alias("Name"),
            pl.col("AllPagesTextNoNewLine")
            .str.extract(r"(SSN\:)(.{0,100})(Alias 1)", group_index=2)
            .str.replace(r"(SSN)", "")
            .str.replace(r"Alias", "")
            .str.replace(r"\:", "")
            .str.strip()
            .alias("Alias"),
            pl.col("AllPagesText")
            .str.extract(r"(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)", group_index=1)
            .str.replace_all(r"[^\d/]", "")
            .str.strip()
            .alias("DOB"),
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(r"(Phone: )(.+)", group_index=2)
            .str.replace_all(r"[^0-9]", "")
            .str.slice(0, 10)
            .str.replace_all(r"(.{3}0000000)", "")
            .alias("RE_Phone"),
            pl.col("AllPagesText").str.extract(r"(B|W|H|A)/(?:F|M)").alias("Race"),
            pl.col("AllPagesText").str.extract(r"(?:B|W|H|A)/(F|M)").alias("Sex"),
            pl.col("AllPagesText")
            .str.extract(r"(?:Address 1:)(.+)(?:Phone)*?", group_index=1)
            .str.replace(r"(Phone.+)", "")
            .str.strip()
            .alias("Address1"),
            pl.col("AllPagesText")
            .str.extract(r"(?:Address 2:)(.+)")
            .str.strip()
            .alias("Address2"),
            pl.col("AllPagesText")
            .str.extract(r"(?:Zip: )(.+)", group_index=1)
            .str.replace_all(r"[A-Z].+", "")
            .alias("ZipCode"),
            pl.col("AllPagesText")
            .str.extract(r"(?:City: )(.*)(?:State: )(.*)", group_index=1)
            .alias("City"),
            pl.col("AllPagesText")
            .str.extract(r"(?:City: )(.*)(?:State: )(.*)", group_index=2)
            .alias("State"),
            pl.col("AllPagesText")
            .str.extract_all(
                r"(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{0,75})"
            )
            .alias("RE_Charges"),
            pl.col("AllPagesText")
            .str.extract_all(
                r"(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^\n]*)"
            )
            .alias("RE_Fees"),
            pl.col("AllPagesText")
            .str.extract(r"(Total:.+\$[^\n]*)")
            .str.replace_all(r"[^0-9|\.|\s|\$]", "")
            .str.extract_all(r"\s\$\d+\.\d{2}")
            .alias("TOTALS"),
            pl.col("AllPagesText")
            .str.extract(r"(ACTIVE[^\n]+D999[^\n]+)")
            .str.extract_all(r"\$\d+\.\d{2}")
            .arr.get(-1)
            .str.replace(r"[\$\s]", "")
            .cast(pl.Float64, strict=False)
            .alias("D999RAW"),
            pl.col("AllPagesText")
            .str.extract_all(r"(\w{2}\d{12})")
            .arr.join("/")
            .alias("RelatedCases"),
            pl.col("AllPagesText")
            .str.extract(r"Filing Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("FilingDate"),
            pl.col("AllPagesText")
            .str.extract(r"Case Initiation Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("CaseInitiationDate"),
            pl.col("AllPagesText")
            .str.extract(r"Arrest Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("ArrestDate"),
            pl.col("AllPagesText")
            .str.extract(r"Offense Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("OffenseDate"),
            pl.col("AllPagesText")
            .str.extract(r"Indictment Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("IndictmentDate"),
            pl.col("AllPagesText")
            .str.extract(r"Youthful Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("YouthfulDate"),
            pl.col("AllPagesText")
            .str.extract(r"AL Institutional Service Num: ([^\na-z])")
            .str.strip()
            .alias("ALInstitutionalServiceNum"),
            pl.col("AllPagesText")
            .str.extract(r"Alacourt\.com (\d\d?/\d\d?/\d\d\d\d)")
            .alias("Retrieved"),
            pl.col("AllPagesText")
            .str.extract(
                r"Court Action: (BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)"
            )
            .alias("CourtAction"),
            pl.col("AllPagesText")
            .str.extract(r"Court Action Date: (\d\d?/\d\d?/\d\d\d\d)")
            .alias("CourtActionDate"),
            pl.col("AllPagesText")
            .str.extract(r"Charge: ([A-Z\.0-9\-\s]+)")
            .str.rstrip("C")
            .str.strip()
            .alias("Description"),
            pl.col("AllPagesText")
            .str.extract(r"Jury Demand: ([A-Z]+)")
            .str.strip()
            .alias("JuryDemand"),
            pl.col("AllPagesText")
            .str.extract(r"Inpatient Treatment Ordered: ([YES|NO]?)")
            .str.strip()
            .alias("InpatientTreatmentOrdered"),
            pl.col("AllPagesText")
            .str.extract(r"Trial Type: ([A-Z]+)")
            .str.replace(r"[S|N]$", "")
            .str.strip()
            .alias("TrialType"),
            pl.col("AllPagesText")
            .str.extract(r"Case Number: (\d\d-\w+) County:")
            .str.strip()
            .alias("County"),
            pl.col("AllPagesText")
            .str.extract(r"Judge: ([A-Z\-\.\s]+)")
            .str.rstrip("T")
            .str.strip()
            .alias("Judge"),
            pl.col("AllPagesText")
            .str.extract(r"Probation Office \#: ([0-9\-]+)")
            .alias("PROBATIONOFFICENUMBERRAW"),
            pl.col("AllPagesText")
            .str.extract(r"Defendant Status: ([A-Z\s]+)")
            .str.rstrip("J")
            .str.strip()
            .alias("DefendantStatus"),
            pl.col("AllPagesText")
            .str.extract(r"([^0-9]+) Arresting Agency Type:")
            .str.replace(r"\n", "")
            .str.strip()
            .alias("ArrestingAgencyType"),
            pl.col("AllPagesText")
            .str.extract(r"Arresting Officer: ([A-Z\s]+)")
            .str.rstrip("S")
            .str.rstrip("P")
            .str.strip()
            .alias("ArrestingOfficer"),
            pl.col("AllPagesText")
            .str.extract(r"Probation Office Name: ([A-Z0-9]+)")
            .alias("ProbationOfficeName"),
            pl.col("AllPagesText")
            .str.extract(r"Traffic Citation \#: ([A-Z0-9]+)")
            .alias("TrafficCitationNumber"),
            pl.col("AllPagesText")
            .str.extract(r"Previous DUI Convictions: (\d{3})")
            .str.strip()
            .cast(pl.Int64, strict=False)
            .alias("PreviousDUIConvictions"),
            pl.col("AllPagesText")
            .str.extract(r"Case Initiation Type: ([A-Z\s]+)")
            .str.rstrip("J")
            .str.strip()
            .alias("CaseInitiationType"),
            pl.col("AllPagesText")
            .str.extract(r"Domestic Violence: ([YES|NO])")
            .str.strip()
            .alias("DomesticViolence"),
            pl.col("AllPagesText")
            .str.extract(r"Agency ORI: ([A-Z\s]+)")
            .str.rstrip("C")
            .str.strip()
            .alias("AgencyORI"),
            pl.col("AllPagesText")
            .str.extract(r"Driver License N°: ([A-Z0-9]+)")
            .str.strip()
            .alias("DLRAW"),
            pl.col("AllPagesText")
            .str.extract(r"SSN: ([X\d]{3}\-[X\d]{2}-[X\d]{4})")
            .alias("SSN"),
            pl.col("AllPagesText")
            .str.extract(r"([A-Z0-9]{11}?) State ID:")
            .alias("SIDRAW"),
            pl.col("AllPagesText")
            .str.extract(r"Weight: (\d*)", group_index=1)
            .cast(pl.Int64, strict=False)
            .alias("Weight"),
            pl.col("AllPagesText")
            .str.extract(r"Height : (\d'\d{2})")
            .alias("RAWHEIGHT"),
            pl.col("AllPagesText")
            .str.extract(r"Eyes/Hair: (\w{3})/(\w{3})", group_index=1)
            .alias("Eyes"),
            pl.col("AllPagesText")
            .str.extract(r"Eyes/Hair: (\w{3})/(\w{3})", group_index=2)
            .alias("Hair"),
            pl.col("AllPagesText")
            .str.extract(r"Country: (\w*+)")
            .str.replace(r"(Enforcement|Party)", "")
            .str.strip()
            .alias("Country"),
            pl.col("AllPagesText")
            .str.extract(r"(\d\d?/\d\d?/\d\d\d\d) Warrant Issuance Date:")
            .str.strip()
            .alias("WarrantIssuanceDate"),
            pl.col("AllPagesText")
            .str.extract(r"Warrant Action Date: (\d\d?/\d\d?/\d\d\d\d)")
            .str.strip()
            .alias("WarrantActionDate"),
            pl.col("AllPagesText")
            .str.extract(r"Warrant Issuance Status: (\w)")
            .str.strip()
            .alias("WarrantIssuanceStatus"),
            pl.col("AllPagesText")
            .str.extract(r"Warrant Action Status: (\w)")
            .str.strip()
            .alias("WarrantActionStatus"),
            pl.col("AllPagesText")
            .str.extract(r"Warrant Location Status: (\w)")
            .str.strip()
            .alias("WarrantLocationStatus"),
            pl.col("AllPagesText")
            .str.extract(r"Number Of Warrants: (\d{3}\s\d{3})")
            .str.strip()
            .alias("NumberOfWarrants"),
            pl.col("AllPagesText")
            .str.extract(r"Bond Type: (\w)")
            .str.strip()
            .alias("BondType"),
            pl.col("AllPagesText")
            .str.extract(r"Bond Type Desc: ([A-Z\s]+)")
            .str.strip()
            .alias("BondTypeDesc"),
            pl.col("AllPagesText")
            .str.extract(r"([\d\.]+) Bond Amount:")
            .str.replace_all(r"[^0-9\.\s]", "")
            .cast(pl.Float64, strict=False)
            .alias("BondAmt"),
            pl.col("AllPagesText")
            .str.extract(r"Bond Company: ([A-Z0-9]+)")
            .str.rstrip("S")
            .str.strip()
            .alias("BondCompany"),
            pl.col("AllPagesText")
            .str.extract(r"Surety Code: ([A-Z0-9]{4})")
            .str.strip()
            .alias("SuretyCode"),
            pl.col("AllPagesText")
            .str.extract(r"Release Date: (\d\d?/\d\d?/\d\d\d\d)")
            .str.strip()
            .alias("BondReleaseDate"),
            pl.col("AllPagesText")
            .str.extract(r"Failed to Appear Date: (\d\d?/\d\d?/\d\d\d\d)")
            .str.strip()
            .alias("FailedToAppearDate"),
            pl.col("AllPagesText")
            .str.extract(
                r"Bondsman Process Issuance: ([^\n]*?) Bondsman Process Return:"
            )
            .str.strip()
            .alias("BondsmanProcessIssuance"),
            pl.col("AllPagesText")
            .str.extract(r"Bondsman Process Return: (.*?) Number of Subponeas")
            .str.strip()
            .alias("BondsmanProcessReturn"),
            pl.col("AllPagesText")
            .str.extract(r"([\n\s/\d]*?) Appeal Court:")
            .str.replace_all(r"[\n\s]", "")
            .str.strip()
            .alias("AppealDate"),
            pl.col("AllPagesText")
            .str.extract(r"([A-Z\-\s]+) Appeal Case Number")
            .str.strip()
            .alias("AppealCourt"),
            pl.col("AllPagesText")
            .str.extract(r"Orgin Of Appeal: ([A-Z\-\s]+)")
            .str.rstrip("L")
            .str.strip()
            .alias("OriginOfAppeal"),
            pl.col("AllPagesText")
            .str.extract(r"Appeal To Desc: ([A-Z\-\s]+)")
            .str.rstrip("D")
            .str.rstrip("T")
            .str.strip()
            .alias("AppealToDesc"),
            pl.col("AllPagesText")
            .str.extract(r"Appeal Status: ([A-Z\-\s]+)")
            .str.rstrip("A")
            .str.strip()
            .alias("AppealStatus"),
            pl.col("AllPagesText")
            .str.extract(r"Appeal To: (\w?) Appeal")
            .str.strip()
            .alias("AppealTo"),
            pl.col("AllPagesText")
            .str.extract(r"LowerCourt Appeal Date: (\d\d?/\d\d?/\d\d\d\d)")
            .str.replace_all(r"[\n\s:\-]", "")
            .str.strip()
            .alias("LowerCourtAppealDate"),
            pl.col("AllPagesText")
            .str.extract(r"Disposition Date Of Appeal: (\d\d?/\d\d?/\d\d\d\d)")
            .str.replace_all(r"[\n\s:\-]", "")
            .str.strip()
            .alias("DispositionDateOfAppeal"),
            pl.col("AllPagesText")
            .str.extract(r"Disposition Type Of Appeal: [^A-Za-z]+")
            .str.replace_all(r"[\n\s:\-]", "")
            .str.strip()
            .alias("DispositionTypeOfAppeal"),
            pl.col("AllPagesText")
            .str.extract(r"Number of Subponeas: (\d{3})")
            .str.replace_all(r"[^0-9]", "")
            .str.strip()
            .cast(pl.Int64, strict=False)
            .alias("NumberOfSubpoenas"),
            pl.col("AllPagesText")
            .str.extract(r"Updated By: (\w{3})")
            .str.strip()
            .alias("AdminUpdatedBy"),
            pl.col("AllPagesText")
            .str.extract(r"Transfer to Admin Doc Date: (\d\d?/\d\d?/\d\d\d\d)")
            .str.strip()
            .alias("TransferToAdminDocDate"),
            pl.col("AllPagesText")
            .str.extract(r"Transfer Desc: ([A-Z\s]{0,15} \d\d?/\d\d?/\d\d\d\d)")
            .str.replace_all(r"(Transfer Desc:)", "")
            .str.strip()
            .alias("TransferDesc"),
            pl.col("AllPagesText")
            .str.extract(r"Date Trial Began but No Verdict \(TBNV1\): ([^\n]+)")
            .str.strip()
            .alias("TBNV1"),
            pl.col("AllPagesText")
            .str.extract(r"Date Trial Began but No Verdict \(TBNV2\): ([^\n]+)")
            .str.strip()
            .alias("TBNV2"),
        ]
    )
    cases = cases.with_columns(
        [
            pl.when(pl.col("D999RAW").is_null())
            .then(pl.lit(0))
            .otherwise(pl.col("D999RAW"))
            .alias("D999")
        ]
    )
    cases = cases.with_columns(
        [
            pl.col("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract_all(r"(?:Requrements Completed: )([YES|NO]?)")
            .arr.join(", ")
            .str.replace_all(r"[\n:]|Requrements Completed", "")
            .str.strip()
            .alias("SentencingRequirementsCompleted"),
            pl.col("AllPagesText")
            .str.extract_all(r"(?:Sentence Date: )(\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.replace_all(r"(Sentence Date: )", "")
            .str.strip()
            .alias("SentenceDate"),
            pl.col("AllPagesText")
            .str.extract_all(r"Probation Period: ([^\.]+)")
            .arr.join(", ")
            .str.strip()
            .alias("ProbationPeriod"),
            pl.col("AllPagesText")
            .str.extract_all(r"License Susp Period: ([^\.]+)")
            .arr.join(", ")
            .str.replace_all(r"(License Susp Period:)", "")
            .str.strip()
            .alias("LicenseSuspPeriod"),
            pl.col("AllPagesText")
            .str.extract_all(r"Jail Credit Period: ([^\.]+)")
            .arr.join(", ")
            .str.replace_all(r"(Jail Credit Period:)", "")
            .str.strip()
            .alias("JailCreditPeriod"),
            pl.col("AllPagesText")
            .str.extract_all(r"Sentence Provisions: ([Y|N]?)")
            .arr.join(", ")
            .str.replace_all(r"(Sentence Provisions:)", "")
            .str.strip()
            .alias("SentenceProvisions"),
            pl.col("AllPagesText")
            .str.extract_all(r"Sentence Start Date: (\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.replace_all(r"(Sentence Start Date:)", "")
            .str.strip()
            .alias("SentenceStartDate"),
            pl.col("AllPagesText")
            .str.extract_all(r"Sentence End Date: (\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.replace_all(r"(Sentence End Date:)", "")
            .str.strip()
            .alias("SentenceEndDate"),
            pl.col("AllPagesText")
            .str.extract_all(r"Probation Begin Date: (\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.replace_all(r"(Probation Begin Date:)", "")
            .str.strip()
            .alias("ProbationBeginDate"),
            pl.col("AllPagesText")
            .str.extract_all(r"Updated By: (\w{3}?)")
            .arr.join(", ")
            .str.replace_all(r"(Updated By:)", "")
            .str.strip()
            .alias("SentenceUpdatedBy"),
            pl.col("AllPagesText")
            .str.extract_all(r"Last Update: (\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.strip()
            .alias("SentenceLastUpdate"),
            pl.col("AllPagesText")
            .str.extract_all(r"Probation Revoke: (\d\d?/\d\d?/\d\d\d\d)")
            .arr.join(", ")
            .str.replace_all(r"Probation Revoke: ", "")
            .str.strip()
            .alias("ProbationRevoke"),
        ]
    )

    dlog(cases.columns, cases.shape, "cases raw regex", cf=debug)

    # clean columns, unnest totals
    cases = cases.with_columns(
        pl.col("RE_Phone")
        .str.replace_all(r"[^0-9]|2050000000", "")
        .alias("CLEAN_Phone"),
        pl.concat_str([pl.col("Address1"), pl.lit(" "), pl.col("Address2")])
        .str.replace_all(r"JID: \w{3} Hardship.*|Defendant Information.*", "")
        .str.strip()
        .alias("StreetAddress"),
        pl.col("Name"),
        pl.when(pl.col("PROBATIONOFFICENUMBERRAW") == "0-000000-00")
        .then(pl.lit(""))
        .otherwise(pl.col("PROBATIONOFFICENUMBERRAW"))
        .alias("ProbationOfficeName"),
        pl.when(pl.col("DLRAW") == "AL")
        .then(pl.lit(""))
        .otherwise(pl.col("DLRAW"))
        .alias("DriverLicenseNo"),
        pl.when(pl.col("SIDRAW") == "AL000000000")
        .then(pl.lit(""))
        .otherwise(pl.col("SIDRAW"))
        .alias("StateID"),
        pl.col("TOTALS")
        .arr.get(0)
        .str.replace_all(r"[^0-9\.]", "")
        .cast(pl.Float64, strict=False)
        .alias("TotalAmtDue"),
        pl.col("TOTALS")
        .arr.get(1)
        .str.replace_all(r"[^0-9\.]", "")
        .cast(pl.Float64, strict=False)
        .alias("TotalAmtPaid"),
        pl.col("TOTALS")
        .arr.get(2)
        .str.replace_all(r"[^0-9\.]", "")
        .cast(pl.Float64, strict=False)
        .alias("TotalBalance"),
        pl.col("TOTALS")
        .arr.get(3)
        .str.replace_all(r"[^0-9\.]", "")
        .cast(pl.Float64, strict=False)
        .alias("TotalAmtHold"),
    )
    cases = cases.with_columns(
        pl.when(pl.col("CLEAN_Phone").str.n_chars() < 7)
        .then(None)
        .otherwise(pl.col("CLEAN_Phone"))
        .alias("Phone"),
    )

    # clean Charges strings
    # explode Charges for table parsing
    all_charges = cases.with_columns(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(
                r"(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*",
                group_index=1,
            )
            .str.replace_all("Case Number:", "", literal=True)
            .str.replace(r"C$", "")
            .str.strip()
            .alias("Name"),
            pl.col("AllPagesText")
            .str.extract_all(
                r"(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{0,75})"
            )
            .alias("RE_Charges"),
            pl.col("AllPagesText")
            .str.extract(r"(Total:.+\$[^\n]*)")
            .str.replace_all(r"[^0-9|\.|\s|\$]", "")
            .str.extract_all(r"\s\$\d+\.\d{2}")
            .arr.get(2)
            .str.replace_all(r"[^0-9\.]", "")
            .cast(pl.Float64, strict=False)
            .alias("RAWTotalBalance"),
            pl.col("AllPagesText")
            .str.extract(r"(ACTIVE[^\n]+D999[^\n]+)")
            .str.extract_all(r"\$\d+\.\d{2}")
            .arr.get(-1)
            .str.replace(r"[\$\s]", "")
            .cast(pl.Float64, strict=False)
            .alias("RAWD999"),
        ]
    )

    all_charges = all_charges.explode("RE_Charges").select(
        [
            pl.col("Name"),
            pl.col("CaseNumber"),
            pl.col("RE_Charges")
            .str.replace_all(r"[A-Z][a-z][A-Za-z\s\$]+.+", "")
            .str.strip()
            .alias("Charges"),
            pl.when(pl.col("RAWTotalBalance").is_null())
            .then(pl.lit(0.0))
            .otherwise(pl.col("RAWTotalBalance"))
            .alias("TotalBalance"),
            pl.when(pl.col("RAWD999").is_null())
            .then(pl.lit(0.0))
            .otherwise(pl.col("RAWD999"))
            .alias("TotalD999"),
        ]
    )

    # clean Fees strings
    # explode Fees for table parsing
    all_fees = cases.explode("RE_Fees").select(
        [
            pl.col("CaseNumber"),
            pl.col("RE_Fees")
            .str.replace_all(r"[^A-Z0-9|\.|\s|\$|\n]", " ")
            .str.strip()
            .alias("Fees"),
        ]
    )

    dlog(cases.columns, cases.shape, cf=debug)

    cases = cases.fill_null("")

    cases = cases.select(
        "Retrieved",
        "CaseNumber",
        "Name",
        "DOB",
        "Race",
        "Sex",
        "Description",
        "CourtAction",
        "CourtActionDate",
        "TotalAmtDue",
        "TotalAmtPaid",
        "TotalBalance",
        "TotalAmtHold",
        "D999",
        "BondAmt",
        "Phone",
        "StreetAddress",
        "City",
        "State",
        "ZipCode",
        "County",
        "Country",
        "Alias",
        "SSN",
        "Weight",
        "Eyes",
        "Hair",
        "FilingDate",
        "CaseInitiationDate",
        "ArrestDate",
        "OffenseDate",
        "IndictmentDate",
        "JuryDemand",
        "InpatientTreatmentOrdered",
        "TrialType",
        "Judge",
        "DefendantStatus",
        "ArrestingAgencyType",
        "ArrestingOfficer",
        "ProbationOfficeName",
        "PreviousDUIConvictions",
        "CaseInitiationType",
        "DomesticViolence",
        "AgencyORI",
        "WarrantIssuanceDate",
        "WarrantActionDate",
        "WarrantIssuanceStatus",
        "WarrantActionStatus",
        "WarrantLocationStatus",
        "NumberOfWarrants",
        "BondType",
        "BondTypeDesc",
        "BondCompany",
        "SuretyCode",
        "BondReleaseDate",
        "FailedToAppearDate",
        "BondsmanProcessIssuance",
        "AppealDate",
        "AppealCourt",
        "OriginOfAppeal",
        "AppealToDesc",
        "AppealStatus",
        "AppealTo",
        "NumberOfSubpoenas",
        "AdminUpdatedBy",
        "TransferDesc",
        "TBNV1",
        "TBNV2",
        "DriverLicenseNo",
        "StateID",
    )
    cases = cases.sort("CaseNumber")
    return cases, all_charges, all_fees


def split_charges(df, debug=False):
    dlog(df.columns, df.shape, "^ split_charges input param", cf=debug)
    charges = df.with_columns(
        [
            pl.col("Name"),
            pl.col("CaseNumber"),
            pl.col("Charges").str.slice(0, 3).alias("Num"),
            pl.col("Charges").str.slice(4, 4).alias("Code"),
            pl.col("Charges").str.slice(9, 1).alias("Sort"),
            pl.col("Charges")
            .str.extract(r"(\d\d/\d\d/\d\d\d\d)", group_index=1)
            .alias("CourtActionDate"),
            pl.col("Charges")
            .str.extract(
                r"[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}\({0,1}[A-Z]{0,1}\){0,1}\.{0,1}\d{0,1}",
                group_index=0,
            )
            .alias("RAWCITE"),
            pl.col("Charges")
            .str.extract(
                r"(BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)",
                group_index=1,
            )
            .alias("CourtAction"),
            pl.col("Charges")
            .apply(
                lambda x: re.split(
                    r"[A-Z0-9]{3}\s*?-[A-Z0-9]{3}\s*?-[A-Z0-9]{3}\(*?[A-Z]*?\)*?\(*?[A-Z0-9]*?\)*?\.*?\d*?",
                    str(x),
                )
            )
            .alias("Split"),
        ]
    )
    dlog(charges, charges.shape, cf=debug)
    charges = charges.filter(pl.col("Num").str.contains("0"))
    charges = charges.with_columns(
        [
            pl.col("Charges")
            .str.contains(r"\d\d?/\d\d?/\d\d\d\d")
            .alias("Disposition"),
            pl.col("Charges").str.contains(pl.lit("FELONY")).alias("Felony"),
            pl.col("Charges").str.contains("GUILTY PLEA").alias("GUILTY_PLEA"),
            pl.col("Charges").str.contains("CONVICTED").alias("CONVICTED"),
        ]
    )
    charges = charges.with_columns(
        [
            pl.when(pl.col("Disposition"))
            .then(pl.col("Split").arr.get(1))
            .otherwise(pl.col("Split").arr.get(0).str.slice(9))
            .str.replace(r"-   -", "", literal=True)
            .str.replace("1STS", "1ST", literal=True)
            .str.strip()
            .alias("RAWDESC"),
            pl.when(pl.col("Disposition"))
            .then(pl.col("Split").arr.get(0).str.slice(19))
            .otherwise(pl.col("Split").arr.get(1))
            .str.strip()
            .alias("SEG_2"),
            pl.when(pl.col("Disposition") == True)
            .then(False)
            .otherwise(True)
            .alias("Filing"),
        ]
    )
    dlog(charges.columns, charges.shape, cf=debug)
    charges = charges.with_columns(
        [
            pl.col("SEG_2")
            .str.extract(
                r"(TRAFFIC MISDEMEANOR|BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)",
                group_index=1,
            )
            .str.replace("TRAFFIC MISDEMEANOR", "MISDEMEANOR")
            .alias("TypeDescription"),
            pl.col("SEG_2")
            .str.extract(
                r"(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)",
                group_index=1,
            )
            .alias("Category"),
            pl.col("RAWDESC")
            .str.contains(r"(A ATT|ATTEMPT|S SOLICIT|CONSP)")
            .is_not()
            .alias("A_S_C_DISQ"),
            pl.col("Code")
            .str.contains(
                r"(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)"
            )
            .alias("CERV_DISQ_MATCH"),
            pl.col("Code")
            .str.contains(
                r"(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)"
            )
            .alias("PARDON_DISQ_MATCH"),
            pl.col("Charges")
            .str.contains(r"(CM\d\d|CMUR)|(CAPITAL)")
            .alias("PERM_DISQ_MATCH"),
        ]
    )
    charges = charges.filter(pl.col("TypeDescription").str.contains(r"[A-Za-z]"))
    charges = charges.with_columns(
        [
            pl.when(pl.col("GUILTY_PLEA") | pl.col("CONVICTED"))
            .then(True)
            .otherwise(False)
            .alias("Conviction")
        ]
    )
    charges = charges.with_columns(
        [
            pl.when(
                pl.col("CERV_DISQ_MATCH")
                & pl.col("Felony")
                & pl.col("Conviction")
                & pl.col("A_S_C_DISQ")
            )
            .then(True)
            .otherwise(False)
            .alias("CERVDisqConviction"),
            pl.when(pl.col("CERV_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ"))
            .then(True)
            .otherwise(False)
            .alias("CERVDisqCharge"),
            pl.when(
                pl.col("PARDON_DISQ_MATCH")
                & pl.col("A_S_C_DISQ")
                & pl.col("Conviction")
                & pl.col("Felony")
            )
            .then(True)
            .otherwise(False)
            .alias("PardonDisqConviction"),
            pl.when(
                pl.col("PARDON_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ")
            )
            .then(True)
            .otherwise(False)
            .alias("PardonDisqCharge"),
            pl.when(
                pl.col("PERM_DISQ_MATCH")
                & pl.col("A_S_C_DISQ")
                & pl.col("Felony")
                & pl.col("Conviction")
            )
            .then(True)
            .otherwise(False)
            .alias("PermanentDisqConviction"),
            pl.when(pl.col("PERM_DISQ_MATCH") & pl.col("Felony") & pl.col("A_S_C_DISQ"))
            .then(True)
            .otherwise(False)
            .alias("PermanentDisqCharge"),
            pl.concat_str([pl.col("CaseNumber"), pl.lit("-"), pl.col("Num")]).alias(
                "CASENONUM"
            ),
        ]
    )
    charges = charges.with_columns(
        [
            pl.col("TotalBalance"),
            pl.when(
                pl.col("CERVDisqConviction")
                | pl.col("PardonDisqConviction")
                | pl.col("PermanentDisqConviction")
            )
            .then((pl.col("TotalBalance") - pl.col("TotalD999")))
            .otherwise(None)
            .alias("PaymentToRestore"),
        ]
    )
    aggch = charges.groupby("CASENONUM").agg("CaseNumber", "RAWCITE", "RAWDESC")
    aggch = aggch.select(
        [
            pl.col("CASENONUM"),
            pl.col("CaseNumber").arr.get(0).alias("CaseNumber"),
            pl.col("RAWDESC").arr.get(0).alias("Description"),
            pl.col("RAWCITE").arr.get(0).alias("Cite"),
        ]
    )
    charges = charges.join(aggch, on="CASENONUM")
    charges = charges.fill_null("")
    charges = charges.with_columns(
        [
            pl.concat_str(
                [
                    pl.col("CaseNumber"),
                    pl.lit(" - "),
                    pl.col("Num"),
                    pl.lit(" "),
                    pl.col("Cite"),
                    pl.lit(" "),
                    pl.col("Description"),
                    pl.lit(" "),
                    pl.col("TypeDescription"),
                    pl.lit(" "),
                    pl.col("CourtAction"),
                    pl.lit(" "),
                    pl.col("CourtActionDate"),
                ]
            )
            .str.strip()
            .str.replace(r",$", "")
            .str.replace(r"\s+", " ")
            .alias("ChargesSummary")
        ]
    )

    charges = charges.select(
        "Name",
        "CaseNumber",
        "Num",
        "Code",
        "Cite",
        "Description",
        "TypeDescription",
        "Category",
        "CourtAction",
        "CourtActionDate",
        "Conviction",
        "Felony",
        "CERVDisqCharge",
        "CERVDisqConviction",
        "PardonDisqCharge",
        "PardonDisqConviction",
        "PermanentDisqCharge",
        "PermanentDisqConviction",
        "Filing",
        "Disposition",
        "TotalBalance",
        "PaymentToRestore",
        "ChargesSummary",
    )
    charges = charges.sort("CaseNumber")
    dlog(charges.columns, charges.shape, cf=debug)

    return charges


def split_fees(df, debug=False):
    df = df.with_columns(
        [
            pl.col("CaseNumber"),
            pl.col("Fees")
            .str.replace(r"(?:\$\d{1,2})( )", "\2")
            .str.split(" ")
            .alias("SPACE_SEP"),
            pl.col("Fees")
            .str.strip()
            .str.replace(" ", "")
            .str.extract_all(r"\s\$\d+\.\d{2}")
            .alias("FEE_SEP"),
        ]
    )
    dlog(df.columns, df.shape, cf=debug)
    df = df.with_columns(
        [
            pl.col("CaseNumber"),
            pl.col("SPACE_SEP").arr.get(0).alias("AdminFee1"),
            pl.col("SPACE_SEP").arr.get(1).alias("FeeStatus1"),
            pl.col("FEE_SEP").arr.get(0).str.replace(r"\$", "").alias("AmtDue"),  # good
            pl.col("FEE_SEP")
            .arr.get(1)
            .str.replace(r"\$", "")
            .alias("AmtPaid"),  # good
            pl.col("FEE_SEP").arr.get(2).str.replace(r"\$", "").alias("Balance1"),
            pl.col("SPACE_SEP").arr.get(5).alias("FeeCode"),
            pl.col("Fees").str.extract(r"(\w00\d)").alias("Payor"),
            pl.col("Fees").str.extract(r"\s(\d\d\d)\s").alias("Payee"),
        ]
    )
    out = df.with_columns(
        [
            pl.col("CaseNumber"),
            pl.when(pl.col("AdminFee1") != "ACTIVE")
            .then(True)
            .otherwise(False)
            .alias("TOT"),
            pl.when(pl.col("AdminFee1") == "Total")
            .then(pl.lit(None))
            .otherwise(pl.col("FeeStatus1"))
            .alias("FeeStatus2"),
            pl.when(pl.col("Balance1").is_in(["L", pl.Null]))
            .then("$0.00")
            .otherwise(pl.col("Balance1").str.replace_all(r"[A-Z]|\$", ""))
            .alias("AmtHold2"),
        ]
    )
    out = out.with_columns(
        pl.when(pl.col("TOT") == True)
        .then(pl.col("FEE_SEP").arr.get(-1).str.replace(r"\$", ""))
        .otherwise(pl.col("FEE_SEP").arr.get(2).str.replace(r"\$", ""))
        .alias("AmtHold"),
        pl.when(pl.col("TOT") == False)
        .then(pl.col("SPACE_SEP").arr.get(0))
        .otherwise(pl.lit(""))
        .alias("FeeStatus"),
        pl.when(pl.col("TOT") == False)
        .then(pl.col("SPACE_SEP").arr.get(1))
        .otherwise(pl.lit(""))
        .alias("AdminFee"),
        pl.when(pl.col("TOT") == True)
        .then(pl.lit("Total:"))
        .otherwise(pl.lit(""))
        .alias("Total"),
    )
    dlog(out.columns, out.shape, cf=debug)
    out = out.with_columns(
        [
            pl.col("AmtDue").str.strip().cast(pl.Float64, strict=False),
            pl.col("AmtPaid").str.strip().cast(pl.Float64, strict=False),
            pl.col("AmtHold").str.strip().cast(pl.Float64, strict=False),
        ]
    )
    out = out.with_columns([pl.col("AmtDue").sub(pl.col("AmtPaid")).alias("Balance")])
    out = out.select(
        "CaseNumber",
        "Total",
        "FeeStatus",
        "AdminFee",
        "FeeCode",
        "Payor",
        "Payee",
        "AmtDue",
        "AmtPaid",
        "Balance",
        "AmtHold",
    )
    dlog(out.columns, out.shape, cf=debug)
    out = out.fill_null("")
    out = out.drop_nulls("AmtDue")
    return out


def explode_images(df, debug=False):
    images = df.select(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(
                r"(Images\s+?Pages)([^\\n]*)(END OF THE REPORT)", group_index=2
            )
            .str.strip()
            .alias("ImagesChunk"),
        ]
    )
    images = images.select(
        [
            pl.col("CaseNumber"),
            pl.col("ImagesChunk")
            .str.replace_all("© Alacourt.com", "", literal=True)
            .str.split("\n")
            .alias("Images"),
        ]
    )
    images = images.explode("Images")
    images = images.filter(pl.col("Images").str.contains(r"[A-Za-z0-9]"))
    images = images.select(
        [
            pl.col("CaseNumber"),
            pl.col("Images")
            .str.replace_all(r"[A-Z][a-z]+", " ")
            .str.replace_all(r"[\s\:]+", " ")
            .str.strip(),
        ]
    )
    return images


def explode_case_action_summary(df, debug=False):
    cas = df.select(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesText")
            .str.extract(
                r"(Case Action Summary)([^\\]*)(Images\s+?Pages)", group_index=2
            )
            .str.replace_all(r"\s+", " ")
            .alias("CASChunk"),
        ]
    )
    cas = cas.select(
        [
            pl.col("CaseNumber"),
            pl.col("CASChunk")
            .str.replace(r"© Alacourt\.com|Date: Description Doc# Title|Operator", "")
            .str.replace(r"Date\: Time Code CommentsCase Action Summary", "")
            .str.strip()
            .str.rstrip()
            .str.split("\n")
            .alias("CaseActionSummary"),
        ]
    )
    cas = cas.explode("CaseActionSummary")
    cas = cas.filter(pl.col("CaseActionSummary").str.contains(r"[A-Za-z0-9]"))
    return cas


def explode_attorneys(df, debug=False):
    att = df.select(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesTextNoNewLine")
            .str.extract(
                r"(Type of Counsel Name Phone Email Attorney Code)(.+)(Warrant Issuance)",
                group_index=2,
            )
            .str.replace(r"Warrant.+", "")
            .str.replace_all(r"[A-Z][a-z]+", " ")
            .str.replace_all(r"[\s\:]+", " ")
            .str.strip()
            .alias("Attorneys"),
        ]
    )
    return att.drop_nulls()


def explode_witnesses(df, debug=False):
    wit = df.select(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesTextNoNewLine")
            .str.extract(r"Witness(.+)Case Action Summary", group_index=1)
            .str.replace(r"\# Date Served Service Type Attorney Issued Type", "")
            .str.replace(r"SJIS Witness List", "")
            .str.replace("Date Issued", "")
            .str.replace("Subpoena", "")
            .str.replace("List", "")
            .str.replace("Requesting Party Name Witness", "")
            .str.replace("Date: Time Code Comments", "")
            .str.replace(r"© Alacourt.com \d\d?/\d\d?/\d\d\d\d", "")
            .str.replace(
                r"Requesting Party Name Witness # Date Served Service Type Attorney Issued Type   Date Issued   Subpoena",
                "",
            )
            .str.replace_all(r"[A-Z][a-z]+", " ")
            .str.replace_all(r"[\s\:]+", " ")
            .str.strip()
            .alias("Witnesses"),
        ]
    )
    return wit.drop_nulls()


def explode_settings(df, debug=False):
    settings = df.select(
        [
            pl.concat_str(
                [
                    pl.col("AllPagesText").str.extract(
                        r"(County: )(\d{2})", group_index=2
                    ),
                    pl.lit("-"),
                    pl.col("AllPagesText").str.extract(r"(\w{2}\-\d{4}\-\d{6}\.\d{2})"),
                ]
            ).alias("CaseNumber"),
            pl.col("AllPagesTextNoNewLine")
            .str.extract(r"(Settings)(.+)(Court Action)", group_index=2)
            .str.replace(r"Settings", "")
            .str.replace(r"Date\:", "")
            .str.replace(r"Que\:", "")
            .str.replace(r"Time\:", "")
            .str.replace(r"Description\:", "")
            .str.replace(
                r"Disposition Charges   # Code Court Action Category Cite Court Action",
                "",
            )
            .str.replace(r"Parties Party 1 - Plaintiff", "")
            .str.replace(r"Court Action.+", "")
            .str.strip()
            .alias("SET1"),
        ]
    )
    settings = settings.select(
        [
            pl.col("CaseNumber"),
            pl.col("SET1")
            .str.replace_all(r"[A-Z][a-z]+", " ")
            .str.replace_all(r"[\s\:]+", " ")
            .str.strip()
            .alias("Settings"),
        ]
    )
    return settings.drop_nulls()


#   #   #   #         FETCH (PDF SCRAPER)       #   #   #   #


def read_query(path, qmax=0, qskip=0, window=None):
    if os.path.splitext(path)[1] in (".xlsx", ".xls"):
        query = pl.read_excel(
            path,
            xlsx2csv_options={"ignore_errors": True},
            read_csv_options={"ignore_errors": True},
        )
    elif os.path.splitext(path)[1] == ".csv":
        query = pl.read_csv(path, ignore_errors=True)
    elif os.path.splitext(path)[1] == ".json":
        query = pl.read_json(path)
    elif os.path.splitext(path)[1] == ".parquet":
        query = pl.read_parquet(path)
    else:
        return None
    query = query.fill_null("")
    if "TEMP_" in query.columns:
        if window:
            window.write_event_value(
                "POPUP",
                "Remove TEMP columns from input query spreadsheet and try again.",
            )
        else:
            raise Exception(
                "Remove TEMP columns from input query spreadsheet and try again."
            )

    if qskip > 0:
        qs = qskip - 1
        query = query[qs:-1]

    if qmax > query.shape[1]:
        query = query[0:qmax]

    pscols = [
        "NAME",
        "PARTY_TYPE",
        "SSN",
        "DOB",
        "COUNTY",
        "DIVISION",
        "CASE_YEAR",
        "NO_RECORDS",
        "FILED_BEFORE",
        "FILED_AFTER",
    ]
    tempcols = [
        "TEMP_NAME",
        "TEMP_PARTY_TYPE",
        "TEMP_SSN",
        "TEMP_DOB",
        "TEMP_COUNTY",
        "TEMP_DIVISION",
        "TEMP_CASE_YEAR",
        "TEMP_NO_RECORDS",
        "TEMP_FILED_BEFORE",
        "TEMP_FILED_AFTER",
    ]

    # add missing progress cols
    for col in ("RETRIEVED", "CASES_FOUND", "QUERY_COMPLETE"):
        if col not in query.columns:
            query = query.with_columns(pl.lit("").alias(col))

    # add matching temp columns for valid columns (i.e. 'Name' -> 'TEMP_NAME')
    goodquery = False
    for col in query.columns:
        if col.upper().strip().replace(" ", "_") in pscols:
            query = query.with_columns(
                [pl.col(col).alias(f"TEMP_{col.upper().strip().replace(' ','_')}")]
            )
            goodquery = True

    # add other temp columns as empty
    for col in tempcols:
        if col not in query.columns:
            query = query.with_columns([pl.lit("").alias(col)])

    if goodquery:
        print(f"{query.shape[0]} queries found in input query file.")
        return query
    else:
        print(
            "Try again with at least one valid column header: [NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, NO_RECORDS, FILED_BEFORE, FILED_AFTER, RETRIEVED, CASES_FOUND, QUERY_COMPLETE]"
        )
        return None


def fetch(
    querypath="",
    dirpath="",
    cID="",
    uID="",
    pwd="",
    qmax=0,
    qskip=0,
    cf=None,
    no_update=False,
    debug=False,
    window=None,
):
    """
    Fetch case PDFs from Alacourt.com.
    Input query spreadsheet with headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and FILED_BEFORE as `querypath`. Alacorder will Party Search non-blank fields on Alacourt.com and download to `dirpath`.
    Args:
       querypath (str): Path to query table/spreadsheet (.xls, .xlsx)
       dirpath (str): Path to PDF output directory
       cID (str): Customer ID on Alacourt.com
       uID (str): User ID on Alacourt.com
       pwd (str): Password on Alacourt.com
       qmax (int): Maximum queries to conduct on Alacourt.com
       qskip (int): Skip entries at top of query file
       no_update (bool): Do not update query template after completion
       debug (bool): Print detailed runtime information to console
    """
    if cf != None:
        querypath = cf["INPUTS"]
        dirpath = cf["OUTPUT_PATH"]
        cID = cf["ALA_CUSTOMER_ID"]
        uID = cf["ALA_USER_ID"]
        pwd = cf["ALA_PASSWORD"]
        qmax = cf["FETCH_MAX"]
        qskip = cf["FETCH_SKIP"]
    else:
        cf = {
            "INPUTS": querypath,
            "OUTPUT_PATH": dirpath,
            "ALA_CUSTOMER_ID": cID,
            "ALA_USER_ID": uID,
            "ALA_PASSWORD": pwd,
            "FETCH_MAX": qmax,
            "FETCH_SKIP": qskip,
        }

    query = read_query(cf["INPUTS"], qmax=qmax, qskip=qskip)

    # start browser and authenticate
    opt = webdriver.ChromeOptions()
    opt.add_experimental_option(
        "prefs",
        {
            "download.default_directory": dirpath,  # Change default directory for downloads
            "download.prompt_for_download": False,  # To auto download the file
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # It will not display PDF directly in chrome
        },
    )
    print("Starting browser... Do not close while in progress!")
    driver = webdriver.Chrome(options=opt)
    login(driver, cID=cID, uID=uID, pwd=pwd, window=window)

    for i, r in enumerate(query.rows(named=True)):
        if query[i, "QUERY_COMPLETE"] == "Y":
            continue
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
            login(driver, cID, uID, pwd, window=window)
        driver.implicitly_wait(1)
        results = party_search(
            driver,
            name=r["TEMP_NAME"],
            party_type=r["TEMP_PARTY_TYPE"],
            ssn=r["TEMP_SSN"],
            dob=r["TEMP_DOB"],
            county=r["TEMP_COUNTY"],
            division=r["TEMP_DIVISION"],
            case_year=r["TEMP_CASE_YEAR"],
            filed_before=r["TEMP_FILED_BEFORE"],
            filed_after=r["TEMP_FILED_AFTER"],
            window=window,
        )

        if len(results) > 0:
            print(
                f"#{i}/{query.shape[0]} {query[i, 'TEMP_NAME']}) ({len(results)} records returned)"
            )
            if window:
                window.write_event_value("PROGRESS-TEXT", 0)
                window.write_event_value("PROGRESS-TEXT-TOTAL", 100)
                for i, url in enumerate(results):
                    window.write_event_value("PROGRESS-TEXT", i + 1)
                    downloadPDF(driver, url)
            else:
                for i, url in enumerate(tqdm(results)):
                    downloadPDF(driver, url)
            query[i, "CASES_FOUND"] = len(results)
            query[i, "RETRIEVED"] = time.time()
            query[i, "QUERY_COMPLETE"] = "Y"
            if not no_update:
                qwrite = query.drop(
                    "TEMP_NAME",
                    "TEMP_PARTY_TYPE",
                    "TEMP_SSN",
                    "TEMP_DOB",
                    "TEMP_COUNTY",
                    "TEMP_DIVISION",
                    "TEMP_CASE_YEAR",
                    "TEMP_NO_RECORDS",
                    "TEMP_FILED_BEFORE",
                    "TEMP_FILED_AFTER",
                )
                write(qwrite, path=cf["INPUTS"], overwrite=True)
        else:
            print(f"Found no results: {query[i, 'TEMP_NAME']}")
            query[i, "QUERY_COMPLETE"] = "Y"
            query[i, "CASES_FOUND"] = 0
            query[i, "RETRIEVED"] = time.time()
            if not no_update:
                qwrite = query.drop(
                    "TEMP_NAME",
                    "TEMP_PARTY_TYPE",
                    "TEMP_SSN",
                    "TEMP_DOB",
                    "TEMP_COUNTY",
                    "TEMP_DIVISION",
                    "TEMP_CASE_YEAR",
                    "TEMP_NO_RECORDS",
                    "TEMP_FILED_BEFORE",
                    "TEMP_FILED_AFTER",
                )
                write(qwrite, path=cf["INPUTS"], overwrite=True)

    if window:
        window.write_event_value("COMPLETE-SQ", time.time())
    print("Completed query template.")
    return query


def party_search(
    driver,
    name="",
    party_type="",
    ssn="",
    dob="",
    county="",
    division="",
    case_year="",
    filed_before="",
    filed_after="",
    debug=False,
    cID="",
    uID="",
    pwd="",
    window=None,
):
    """
    Collect PDFs via SJIS Party Search Form from Alacourt.com
    Returns list of URLs for downloadPDF() to download

    Args:
        driver (WebDriver): selenium/chrome web driver object
        name (str, optional): Name (LAST FIRST)
        party_type (str, optional): "Defendants" | "Plaintiffs" | "ALL"
        ssn (str, optional): Social Security Number
        dob (str, optional): Date of Birth
        county (str, optional): County
        division (str, optional): "All Divisions"
             "Criminal Only"
             "Civil Only"
             "CS - CHILD SUPPORT"
             "CV - CIRCUIT - CIVIL"
             "CC - CIRCUIT - CRIMINAL"
             "DV - DISTRICT - CIVIL"
             "DC - DISTRICT - CRIMINAL"
             "DR - DOMESTIC RELATIONS"
             "EQ - EQUITY-CASES"
             "MC - MUNICIPAL-CRIMINAL"
             "TP - MUNICIPAL-PARKING"
             "SM - SMALL CLAIMS"
             "TR - TRAFFIC"
        case_year (str, optional): YYYY
        filed_before (str, optional): M/DD/YYYY
        filed_after (str, optional): M/DD/YYYY
        debug (bool, optional): Print detailed logs.
        cID (str, optional): Customer ID on Alacourt.com
        uID (str, optional): User ID on Alacourt.com
        pwd (str, optional): Password on Alacourt.com

    Returns:
        List[str] of URLs to PDF
    """

    if "frmIndexSearchForm" not in driver.current_url:
        driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

    driver.implicitly_wait(5)

    has_window = False if window == "None" else True

    # connection error
    try:
        party_name_box = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$txtName"
        )
    except selenium.common.exceptions.NoSuchElementException:
        if debug:
            print(
                """NoSuchElementException on alac.py 2173: party_name_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder1$txtName")"""
            )
        if driver.current_url == "https://v2.alacourt.com/frmlogin.aspx":
            time.sleep(10)
            login(driver, cID=cID, uID=uID, pwd=pwd)
            driver.implicitly_wait(1)
        driver.get("https:v2.alacourt.com/frmIndexSearchForm.aspx")
        print("Successfully connected and logged into Alacourt!")

    # field search
    if name != "":
        party_name_box.send_keys(name)
    if ssn != "":
        ssn_box = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$txtSSN"
        )
        ssn_box.send_keys(ssn)
    if dob != "":
        date_of_birth_box = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$txtDOB"
        )
        date_of_birth_box.send_keys(dob)
    if party_type != "":
        party_type_select = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$rdlPartyType"
        )
        pts = Select(party_type_select)
        if party_type == "plaintiffs":
            pts.select_by_visible_text("Plaintiffs")
        if party_type == "defendants":
            pts.select_by_visible_text("Defendants")
        if party_type == "all":
            pts.select_by_visible_text("ALL")

    if county != "":
        county_select = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCounties"
        )
        scounty = Select(county_select)
        scounty.select_by_visible_text(county)
    if division != "":
        division_select = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$UcddlDivisions1$ddlDivision"
        )
        sdivision = Select(division_select)
        sdivision.select_by_visible_text(division)
    if case_year != "":
        case_year_select = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlCaseYear"
        )
        scase_year = Select(case_year_select)
        scase_year.select_by_visible_text(case_year)
    no_records_select = driver.find_element(
        by=By.NAME, value="ctl00$ContentPlaceHolder1$ddlNumberOfRecords"
    )
    sno_records = Select(no_records_select)
    sno_records.select_by_visible_text("1000")
    if filed_before != "":
        filed_before_box = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$txtFrom"
        )
        filed_before_box.send_keys(filed_before)
    if filed_after != "":
        filed_after_box = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder1$txtTo"
        )
        filed_after_box.send_keys(filed_after)

    driver.implicitly_wait(1)

    # submit search
    search_button = driver.find_element(by=By.ID, value="searchButton")

    driver.implicitly_wait(1)
    try:
        search_button.click()
    except:
        driver.implicitly_wait(5)
        time.sleep(5)

    if debug:
        print("Submitted party search form...")

    driver.implicitly_wait(1)

    # count pages
    try:
        page_counter = driver.find_element(
            by=By.ID, value="ContentPlaceHolder1_dg_tcPageXofY"
        ).text
        pages = int(page_counter.strip()[-1])

    except:
        pages = 1

    # count results
    try:
        results_indicator = driver.find_element(
            by=By.ID, value="ContentPlaceHolder1_lblResultCount"
        )
        results_count = int(
            results_indicator.text.replace("Search Results: ", "")
            .replace(" records returned.", "")
            .strip()
        )
    except:
        pass

    if debug:
        print(f"Found {results_count} results, fetching URLs and downloading PDFs...")

    # get PDF links from each page
    pdflinks = []
    i = 0
    for i in range(0, pages):
        driver.implicitly_wait(0.5)
        hovers = driver.find_elements(By.CLASS_NAME, "menuHover")
        for x in hovers:
            try:
                a = x.get_attribute("href")
                if "PDF" in a:
                    pdflinks.append(a)
            except:
                pass
        driver.implicitly_wait(0.5)
        try:
            pager_select = Select(
                driver.find_element(
                    by=By.NAME, value="ctl00$ContentPlaceHolder1$dg$ctl18$ddlPages"
                )
            )
            next_pg = int(pager_select.text) + 1
            driver.implicitly_wait(0.5)
        except:
            try:
                driver.implicitly_wait(0.5)
                time.sleep(0.5)
                next_button = driver.find_element(
                    by=By.ID, value="ContentPlaceHolder1_dg_ibtnNext"
                )
                next_button.click()
            except:
                continue
    return pdflinks


def downloadPDF(driver, url, cID="", uID="", pwd="", window=None):
    """
    With selenium WebDriver `driver`, download PDF at `url`.

    Args:
        driver (WebDriver): Google Chrome selenium.WebDriver() object
        url (str): URL to Alacourt case detail PDF download
        cID (str, optional): Customer ID on Alacourt.com
        uID (str, optional): User ID on Alacourt.com
        pwd (str, optional): Password on Alacourt.com

    """
    if (
        driver.current_url == "https://v2.alacourt.com/frmlogin.aspx"
        and cID != ""
        and uID != ""
        and pwd != ""
    ):
        login(driver, cID=cID, uID=uID, pwd=pwd, window=window)
    a = driver.get(url)
    driver.implicitly_wait(0.5)


def login(driver, cID, uID="", pwd="", path="", window=None):
    """Login to Alacourt.com using (driver) and auth (cID, username, pwd) for browser download to directory at (path)

    Args:
        driver (WebDriver): Google Chrome selenium.WebDriver() object
        cID (str): Alacourt.com Customer ID
        uID (str): Alacourt.com User ID
        pwd (str): Alacourt.com Password
        path (str, optional): Set browser download path

    Returns:
        driver (WebDriver): selenium engine
    """
    if driver == None:
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": path,  # Change default directory for downloads
                "download.prompt_for_download": False,  # To auto download the file
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,  # It will not display PDF directly in chrome
            },
        )
        driver = webdriver.Chrome(options=options)

    print("Connecting to Alacourt...")

    login_screen = driver.get("https://v2.alacourt.com/frmlogin.aspx")

    print("Logging in...")

    driver.implicitly_wait(1)

    cID_box = driver.find_element(by=By.NAME, value="ctl00$ContentPlaceHolder$txtCusid")
    username_box = driver.find_element(
        by=By.NAME, value="ctl00$ContentPlaceHolder$txtUserId"
    )
    pwd_box = driver.find_element(
        by=By.NAME, value="ctl00$ContentPlaceHolder$txtPassword"
    )
    login_button = driver.find_element(by=By.ID, value="ContentPlaceHolder_btLogin")

    cID_box.send_keys(cID)
    username_box.send_keys(uID)
    pwd_box.send_keys(pwd)

    driver.implicitly_wait(1)

    login_button.click()

    driver.implicitly_wait(1)

    try:
        continueLogIn = driver.find_element(
            by=By.NAME, value="ctl00$ContentPlaceHolder$btnContinueLogin"
        )
        continueLogIn.click()
    except:
        pass

    driver.get("https://v2.alacourt.com/frmIndexSearchForm.aspx")

    print("Successfully connected and logged into Alacourt!")

    driver.implicitly_wait(1)

    return driver


def empty_query(path):
    """Create empty spreadsheet to fill and import as query submit search list to retrieve matching case records from Alacourt.com.

    Args:
        path (str): Desired output path (.xls, .xlsx)

    """
    success = True
    empty = pl.DataFrame(
        columns=[
            "NAME",
            "PARTY_TYPE",
            "SSN",
            "DOB",
            "COUNTY",
            "DIVISION",
            "CASE_YEAR",
            "NO_RECORDS",
            "FILED_BEFORE",
            "FILED_AFTER",
            "RETRIEVED",
            "CASES_FOUND",
        ]
    )
    return write(empty, sheet_names="query", path=path, overwrite=True)


#   #   #   #      GRAPHICAL USER INTERFACE    #   #   #   #


def loadgui():
    """
    Load PySimpleGUI tk graphical interface
    """
    import PySimpleGUI as sg
    import platform
    import threading

    psys = platform.system()
    plat = platform.platform()
    if "Darwin" in (plat, psys) or "macOS" in (plat, psys):  # set MacOS element sizes
        HEADER_FONT, LOGO_FONT, ASCII_FONT, BODY_FONT, WINDOW_RESIZE, WINDOW_SIZE = (
            "Default 22",
            "Courier 20",
            "Courier 14",
            "Default 12",
            True,
            [480, 510],
        )
    elif "Windows" in (plat, psys):  # set Windows element sizes
        HEADER_FONT, LOGO_FONT, ASCII_FONT, BODY_FONT, WINDOW_RESIZE, WINDOW_SIZE = (
            "Default 14",
            "Courier 13",
            "Courier 11",
            "Default 10",
            True,
            [500, 540],
        )
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    else:  # set Linux, etc. element sizes
        HEADER_FONT, LOGO_FONT, ASCII_FONT, BODY_FONT, WINDOW_RESIZE, WINDOW_SIZE = (
            "Default 15",
            "Courier 12",
            "Courier 13",
            "Default 10",
            True,
            [540, 540],
        )
    sg.theme("Black")
    sg.set_options(font=BODY_FONT)
    fetch_layout = [
        [
            sg.Text(
                """Collect case PDFs in bulk from Alacourt.com.""",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """Requires Google Chrome. Use column headers NAME, PARTY_TYPE, SSN,\nDOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel\nspreadsheet to submit a list of queries for Alacorder to scrape. Each\ncolumn corresponds to a field in Alacourt's Party Search form.""",
                pad=(5, 5),
            )
        ],
        [
            sg.Text("Input Path: "),
            sg.InputText(
                tooltip="Existing query template (.xlsx)",
                size=[22, 10],
                key="SQ-INPUTPATH",
                focus=True,
            ),
            sg.FileBrowse(button_text="Select File", button_color=("white", "black")),
            sg.Button(
                button_text="New Query",
                button_color=("white", "black"),
                k="NEWQUERY",
                enable_events=True,
            ),
        ],
        [
            sg.Text("Output Path: "),
            sg.InputText(
                tooltip="PDF download destination folder",
                size=[29, 10],
                key="SQ-OUTPUTPATH",
            ),
            sg.FolderBrowse(
                button_text="Select Folder", button_color=("white", "black")
            ),
        ],
        [
            sg.Text("Max queries: "),
            sg.Input(key="SQ-MAX", default_text="0", size=[5, 1]),
            sg.Text("Skip from top: "),
            sg.Input(key="SQ-SKIP", default_text="0", size=[5, 1]),
        ],
        [sg.Text("Alacourt.com Credentials", font=BODY_FONT)],
        [
            sg.Text("Customer ID:"),
            sg.Input(key="SQ-CUSTOMERID", size=(13, 1)),
            sg.Text("User ID:"),
            sg.Input(key="SQ-USERID", size=(13, 1)),
        ],
        [
            sg.Text("Password:"),
            sg.InputText(key="SQ-PASSWORD", password_char="*", size=(15, 1)),
        ],
        [
            sg.Button(
                "Start Query",
                key="SQ",
                button_color=("white", "black"),
                pad=(10, 10),
                disabled_button_color=("grey", "black"),
                bind_return_key=True,
            )
        ],
    ]
    archive_layout = [
        [
            sg.Text(
                """Create full text archives from a directory\nof PDF cases.""",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """Case text archives require a fraction of the storage capacity and\nprocessing time used to process PDF directories. Before exporting\nyour data to tables, create an archive with supported file extensions\n.parquet, .json, and .csv. Once archived, use your case text archive\nas an input for multitable or single table export.""",
                pad=(5, 5),
            )
        ],
        [
            sg.Text("Input Directory: "),
            sg.InputText(
                tooltip="PDF directory or full text archive (.parquet, .json, .csv)",
                size=[25, 1],
                key="MA-INPUTPATH",
                focus=True,
            ),
            sg.FolderBrowse(
                button_text="Select Folder", button_color=("white", "black")
            ),
        ],
        [
            sg.Text("Output Path: "),
            sg.InputText(
                tooltip="Output archive file path (.parquet, .json, .csv)",
                size=[39, 1],
                key="MA-OUTPUTPATH",
            ),
        ],
        [
            sg.Text("Skip Cases From: "),
            sg.Input(
                tooltip="Skip all input cases found in PDF directory or archive (.parquet, .json, .csv)",
                key="MA-SKIP",
                size=[24, 1],
                pad=(0, 10),
            ),
        ],
        [
            sg.Text("Max cases: "),
            sg.Input(key="MA-COUNT", default_text="0", size=[5, 1]),
            sg.Checkbox("Allow Overwrite", default=True, key="MA-OVERWRITE"),
            sg.Checkbox("Try to Append", key="MA-APPEND", default=False),
        ],
        [
            sg.Button(
                "Make Archive",
                button_color=("white", "black"),
                key="MA",
                enable_events=True,
                bind_return_key=True,
                disabled_button_color=("grey", "black"),
                pad=(10, 10),
            )
        ],
    ]  # "MA"
    append_layout = [
        [
            sg.Text(
                """Append case text archive with the contents\nof a case directory or archive.""",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """Case text archives require a fraction of the storage capacity and\nprocessing time used to process PDF directories. Before exporting\nyour data to tables, create an archive with a supported file\nextension (.parquet, .json, .csv). Once archived, use your case text\narchive as an input for table export.""",
                pad=(5, 5),
            )
        ],
        [
            sg.Text("To Append: "),
            sg.InputText(
                tooltip="PDF Directory or full text archive (.parquet, .json, .csv)",
                size=[30, 10],
                key="AA-INPUTPATH",
                focus=True,
            ),
            sg.FileBrowse(button_text="Select File", button_color=("white", "black")),
        ],
        [
            sg.Text("To Be Appended: "),
            sg.InputText(
                tooltip="Destination full text archive (.parquet, .json, .csv)",
                size=[26, 10],
                key="AA-OUTPUTPATH",
            ),
            sg.FileBrowse(button_text="Select File", button_color=("white", "black")),
        ],
        [
            sg.Button(
                "Append Archives",
                key="AA",
                button_color=("white", "black"),
                pad=(10, 10),
                disabled_button_color=("grey", "black"),
                bind_return_key=True,
            )
        ],
    ]  # "AA"
    sum_layout = [
        [
            sg.Text(
                """Pair cases by AIS number to create a\npaired summary table.""",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """To make a charges summary table, start by creating an AIS / Unique ID\npair template, fill the template with AIS numbers or another\nidentifier to match names in common, then enter the template path and\ncase input path below.""",
                pad=(5, 5),
            )
        ],
        [
            sg.Text("Input Path:  "),
            sg.InputText(
                tooltip="PDF Directory or full text archive (.parquet, .json, .csv)",
                size=[31, 10],
                key="SUM-INPUTPATH",
                focus=True,
            ),
            sg.FileBrowse(button_text="Select File", button_color=("white", "black")),
        ],
        [
            sg.Text("Pairs: "),
            sg.InputText(
                tooltip="Destination full text archive (.parquet, .json, .csv)",
                size=[32, 10],
                key="SUM-PAIRS",
            ),
            sg.Button(
                button_text="Make Template", button_color=("white", "black"), key="MT"
            ),
        ],
        [
            sg.Text("Output Path:  "),
            sg.InputText(
                tooltip="PDF Directory or full text archive (.parquet, .json, .csv)",
                size=[40, 10],
                key="SUM-OUTPUTPATH",
                focus=True,
            ),
        ],
        [
            sg.Radio("Charges", "SUMMARY", key="SUM-CH", default=True),
            sg.Radio("Convictions", "SUMMARY", key="SUM-CONV", default=False),
            sg.Radio("Voting Rights", "SUMMARY", key="SUM-VRR", default=False),
        ],
        [
            sg.Button(
                "Create Summary",
                key="SUM",
                button_color=("white", "black"),
                pad=(10, 10),
                disabled_button_color=("grey", "black"),
                bind_return_key=True,
            )
        ],
    ]  # "SUM"
    table_layout = [
        [
            sg.Text(
                """Export data tables from a case archive\nor PDF directory.""",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """Alacorder processes case detail PDFs and case text archives into data\ntables suitable for research purposes. Enter PDF directory or case text\narchive path and output file path (.xlsx, .xls, .csv, .json) to begin. CSV\nand JSON support single table selection only.""",
                pad=(5, 5),
            )
        ],
        [
            sg.Text("Input Path: "),
            sg.InputText(
                tooltip="PDF directory or full text archive (.parquet, .json, .csv)",
                size=[28, 10],
                key="TB-INPUTPATH",
                focus=True,
            ),
            sg.FolderBrowse(
                button_text="Select Folder", button_color=("white", "black")
            ),
        ],
        [
            sg.Text("Output Path: "),
            sg.InputText(
                tooltip="Multitable export (.xlsx, .xls) or single-table export (.xlsx, .xls, .json, .csv)",
                size=[39, 10],
                key="TB-OUTPUTPATH",
            ),
        ],
        [
            sg.Radio("All Tables (.xlsx, .xls)", "TABLE", key="TB-ALL", default=True),
            sg.Radio("Cases", "TABLE", key="TB-CASES", default=False),
            sg.Radio("Charges", "TABLE", key="TB-CHARGES", default=False),
            sg.Radio("Fees", "TABLE", key="TB-FEES", default=False),
        ],
        [
            sg.Radio("Case Action Summary", "TABLE", key="TB-CAS", default=False),
            sg.Radio("Witnesses", "TABLE", key="TB-WITNESSES", default=False),
            sg.Radio("Images", "TABLE", key="TB-IMAGES", default=False),
        ],
        [
            sg.Radio("Attorneys", "TABLE", key="TB-ATTORNEYS", default=False),
            sg.Radio("Settings", "TABLE", key="TB-SETTINGS", default=False),
            sg.Radio("Disposition", "TABLE", key="TB-DISPOSITION", default=False),
            sg.Radio("Filing", "TABLE", key="TB-FILING", default=False),
        ],
        [
            sg.Text("Max cases: "),
            sg.Input(key="TB-COUNT", default_text="0", size=[5, 1]),
            sg.Checkbox("Allow Overwrite", key="TB-OVERWRITE", default=True),
        ],
        [
            sg.Button(
                "Export Table",
                key="TB",
                button_color=("white", "black"),
                pad=(10, 10),
                disabled_button_color=("grey", "black"),
                bind_return_key=True,
            )
        ],
    ]  # "TB"
    about_layout = [
        [
            sg.Text(
                f""" ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌\n ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││\n ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘\n {version}""",
                font=ASCII_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                "Alacorder retrieves and processes\nAlacourt case detail PDFs into\ndata tables and archives.",
                font=HEADER_FONT,
                pad=(5, 5),
            )
        ],
        [
            sg.Text(
                """View documentation, source code, and latest updates at\ngithub.com/sbrobson959/alacorder.\n\n© 2023 Sam Robson""",
                font=BODY_FONT,
            )
        ],
    ]  # "ABOUT"
    tabs = sg.TabGroup(
        expand_x=True,
        expand_y=False,
        size=[0, 0],
        font="Courier",
        layout=[
            [sg.Tab("fetch", layout=fetch_layout, pad=(2, 2))],
            [sg.Tab("archive", layout=archive_layout, pad=(2, 2))],
            [sg.Tab("table", layout=table_layout, pad=(2, 2))],
            [sg.Tab("append", layout=append_layout, pad=(2, 2))],
            [sg.Tab("pair", layout=sum_layout, pad=(2, 2))],
            [sg.Tab("about", layout=about_layout, pad=(2, 2))],
        ],
    )
    layout = [
        [sg.Text(fshort_name, font=LOGO_FONT, pad=(5, 5))],
        [tabs],
        [
            sg.ProgressBar(
                100,
                size=[5, 10],
                expand_y=False,
                orientation="h",
                expand_x=True,
                key="PROGRESS",
                bar_color="black",
            )
        ],
        [
            sg.Multiline(
                expand_x=True,
                expand_y=True,
                background_color="black",
                reroute_stdout=True,
                pad=(5, 5),
                font="Courier 11",
                write_only=True,
                autoscroll=True,
                no_scrollbar=True,
                size=[None, 4],
                border_width=0,
            )
        ],
    ]
    window = sg.Window(
        title=name,
        layout=layout,
        grab_anywhere=True,
        resizable=WINDOW_RESIZE,
        size=WINDOW_SIZE,
    )
    while True:
        event, values = window.read()
        if event in ("Exit", "Quit", sg.WIN_CLOSED):
            window.close()
            break
        elif "TOTAL" in event and "PROGRESS" in event:
            window["PROGRESS"].update(max=values[event], current_count=0)
        elif "PROGRESS" in event and "TOTAL" not in event:
            window["PROGRESS"].update(current_count=values[event])
        elif "COMPLETE" in event:
            print("Alacorder completed the task.")
            window["AA"].update(disabled=False)
            window["SQ"].update(disabled=False)
            window["MA"].update(disabled=False)
            window["TB"].update(disabled=False)
            window["MA"].update(disabled=False)
            window["SUM"].update(disabled=False)
            window["PROGRESS"].update(current_count=0, max=100)
            sg.popup("Alacorder completed the task.")
            continue
        elif event == "NEWQUERY":
            if window["SQ-INPUTPATH"].get() == "":
                sg.popup(
                    "To create empty query template, enter file output path (extension must be .xlsx) in Input Path, then press the New Query button to try again."
                )
            else:
                if empty_query(window["SQ-INPUTPATH"].get()):
                    sg.popup("Alacorder created query template.")
                else:
                    sg.popup(
                        "Enter valid path with .xlsx extension in Input Path box and try again."
                    )
        elif event == "MT":
            cf = set(
                window["SUM-INPUTPATH"].get(),
                window["SUM-PAIRS"].get(),
                pairs=window["SUM-PAIRS"].get(),
                log=True,
                no_write=False,
                debug=False,
                overwrite=True,
                window=window,
            )
            threading.Thread(target=pairs, args=[cf], daemon=True).start()
            print("Creating AIS / Unique ID pairs template...")
            window["MT"].update(disabled=True)
        elif event == "SUM":
            cf = set(
                window["SUM-INPUTPATH"].get(),
                window["SUM-OUTPUTPATH"].get(),
                pairs=window["SUM-PAIRS"].get(),
                vrr_summary=window["SUM-VRR"].get(),
                charges_summary=window["SUM-CH"].get(),
                convictions_summary=window["SUM-CONV"].get(),
                log=True,
                no_write=False,
                debug=False,
                overwrite=True,
                window=window,
            )
            print("Making voting rights summary table...")
            threading.Thread(target=init, args=[cf], daemon=True).start()
            window["SUM"].update(disabled=True)
        elif event == "POPUP":
            sg.popup(values["POPUP"])
        elif event == "TB":
            table = ""
            table = "all" if window["TB-ALL"].get() else table
            table = "charges" if window["TB-CHARGES"].get() else table
            table = "fees" if window["TB-FEES"].get() else table
            table = "case-action-summary" if window["TB-CAS"].get() else table
            table = "witnesses" if window["TB-WITNESSES"].get() else table
            table = "images" if window["TB-IMAGES"].get() else table
            table = "attorneys" if window["TB-ATTORNEYS"].get() else table
            table = "settings" if window["TB-SETTINGS"].get() else table
            table = "disposition" if window["TB-DISPOSITION"].get() else table
            table = "filing" if window["TB-FILING"].get() else table
            if (
                window["TB-INPUTPATH"].get() == ""
                or window["TB-OUTPUTPATH"].get() == ""
            ):
                sg.popup("Check configuration and try again.")
            else:
                cf = set(
                    window["TB-INPUTPATH"].get(),
                    window["TB-OUTPUTPATH"].get(),
                    count=int(window["TB-COUNT"].get()),
                    table=table,
                    log=True,
                    overwrite=window["TB-OVERWRITE"].get(),
                    no_prompt=True,
                    debug=False,
                    archive=False,
                    window=window,
                )
                # except:
                window["TB"].update(disabled=True)
                threading.Thread(target=init, args=[cf], daemon=True).start()
                continue
        elif event == "MA":
            if (
                window["MA-INPUTPATH"].get() == ""
                or window["MA-OUTPUTPATH"].get() == ""
            ):
                sg.popup("Check configuration and try again.")
                window["MA"].update(disabled=False)
                continue
            try:
                count = int(window["MA-COUNT"].get().strip())
            except:
                count = 0
            try:
                cf = set(
                    window["MA-INPUTPATH"].get(),
                    window["MA-OUTPUTPATH"].get(),
                    count=count,
                    archive=True,
                    log=True,
                    overwrite=window["MA-OVERWRITE"].get(),
                    append=window["MA-APPEND"].get(),
                    no_prompt=True,
                    window=window,
                )
            except:
                sg.popup("Check configuration and try again.")
                window["MA"].update(disabled=False)
                continue
            window["MA"].update(disabled=True)
            threading.Thread(target=archive, args=[cf], daemon=True).start()
            continue
        elif event == "SQ":
            if (
                window["SQ-INPUTPATH"].get() == ""
                or window["SQ-OUTPUTPATH"].get() == ""
            ):
                sg.popup("Check configuration and try again.")
            try:
                pwd = window["SQ-PASSWORD"].get()
                try:
                    sq_max = int(window["SQ-MAX"].get().strip())
                    sq_skip = int(window["SQ-SKIP"].get().strip())
                except:
                    sq_max = 0
                    sq_skip = 0
                window["SQ"].update(disabled=True)
                threading.Thread(
                    target=fetch,
                    args=(
                        window["SQ-INPUTPATH"].get(),
                        window["SQ-OUTPUTPATH"].get(),
                        window["SQ-CUSTOMERID"].get(),
                        window["SQ-USERID"].get(),
                        pwd,
                        sq_max,
                        sq_skip,
                        None,
                        False,
                        False,
                        window,
                    ),
                    daemon=True,
                ).start()
                continue
            except:
                print("Check configuration and try again.")
                window["SQ"].update(disabled=False)
                continue
        elif event == "AA":
            if (
                window["AA-INPUTPATH"].get() == ""
                or window["AA-OUTPUTPATH"].get() == ""
            ):
                sg.popup("Check configuration and try again.")
                continue
            try:
                window["AA"].update(disabled=True)
                threading.Thread(
                    target=append_archive,
                    args=(
                        window["AA-INPUTPATH"].get(),
                        window["AA-OUTPUTPATH"].get(),
                    ),
                    kwargs={"window": window},
                    daemon=True,
                ).start()
                continue
            except:
                print("Check configuration and try again.")
                window["AA"].update(disabled=False)
                continue
        else:
            pass


#   #   #   #       COMMAND LINE INTERFACE     #   #   #   #


@click.group(
    invoke_without_command=autoload_graphical_user_interface,
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option(f"{version}", package_name=f"{name} {long_version}")
@click.pass_context
def main(ctx):
    """
    ALACORDER collects and processes case detail PDFs into data tables suitable for research purposes.
    """
    if autoload_graphical_user_interface and ctx.invoked_subcommand == None:
        loadgui()


@main.command(name="start", help="Launch graphical user interface")
def cli_start():
    loadgui()


@main.command(name="append", help="Append one case text archive to another")
@click.option(
    "--input-path",
    "-in",
    "in_path",
    required=True,
    prompt="Path to archive / PDF directory",
    help="Path to input archive",
    type=click.Path(),
)
@click.option(
    "--output-path",
    "-out",
    "out_path",
    required=True,
    prompt="Path to output archive",
    type=click.Path(),
    help="Path to output archive",
)
@click.option(
    "--no-write",
    "-n",
    default=False,
    is_flag=True,
    help="Do not export to output path",
    hidden=True,
)
def cli_append(in_path, out_path, no_write=False):
    """Append one case text archive to another

    Args:
        in_path (Path|DataFrame): Path to input archive / PDF directory
        out_path (Path): Path to output archive
        no_write (bool, optional): Do not export to output path

    Returns:
        DataFrame: Appended archive
    """
    print("Appending archives...")
    return append_archive(in_path, out_path)


@main.command(name="fetch", help="Fetch cases from Alacourt.com")
@click.option(
    "--input-path",
    "-in",
    "listpath",
    required=True,
    prompt="Path to query table",
    help="Path to query table/spreadsheet (.xls, .xlsx)",
    type=click.Path(),
)
@click.option(
    "--output-path",
    "-out",
    "path",
    required=True,
    prompt="PDF download path",
    type=click.Path(),
    help="Desired PDF output directory",
)
@click.option(
    "--customer-id",
    "-c",
    "cID",
    required=True,
    prompt="Alacourt Customer ID",
    help="Customer ID on Alacourt.com",
)
@click.option(
    "--user-id",
    "-u",
    "uID",
    required=True,
    prompt="Alacourt User ID",
    help="User ID on Alacourt.com",
)
@click.option(
    "--password",
    "-p",
    "pwd",
    required=True,
    prompt="Alacourt Password",
    help="Password on Alacourt.com",
    hide_input=True,
)
@click.option(
    "--max",
    "-max",
    "qmax",
    required=False,
    type=int,
    help="Maximum queries to conduct on Alacourt.com",
    default=0,
)
@click.option(
    "--skip",
    "-skip",
    "qskip",
    required=False,
    type=int,
    help="Skip entries at top of query file",
    default=0,
)
@click.option(
    "--no-mark",
    "-n",
    "no_update",
    is_flag=True,
    default=False,
    help="Do not update query template after completion",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="Print detailed runtime information to console",
)
def cli_fetch(listpath, path, cID, uID, pwd, qmax, qskip, no_update, debug=False):
    """
    Fetch case PDFs from Alacourt.com.
    Args:
        listpath (str): Path to query table/spreadsheet (.xls, .xlsx)
        path (str): Path to PDF output directory
        cID (str): Customer ID on Alacourt.com
        uID (str): User ID on Alacourt.com
        pwd (str): Password on Alacourt.com
        qmax (int): Maximum queries to conduct on Alacourt.com
        qskip (int): Skip entries at top of query file
        no_update (bool): Do not update query template after completion
        debug (bool): Print detailed runtime information to console
    """
    fetch(
        querypath=listpath,
        dirpath=path,
        cID=cID,
        uID=uID,
        pwd=pwd,
        qmax=qmax,
        qskip=qskip,
        no_update=no_update,
        debug=debug,
    )


@main.command(name="table", help="Export data tables from archive or directory")
@click.option(
    "--input-path",
    "-in",
    required=True,
    type=click.Path(),
    prompt="Input Path",
    show_choices=False,
)
@click.option(
    "--output-path", "-out", required=True, type=click.Path(), prompt="Output Path"
)
@click.option("--table", "-t", help="Table export selection")
@click.option(
    "--count",
    "-c",
    default=0,
    help="Total cases to pull from input",
    show_default=False,
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--no-prompt",
    "-s",
    default=False,
    is_flag=True,
    help="Skip user input / confirmation prompts",
)
@click.option(
    "--no-log",
    default=False,
    is_flag=True,
    help="Do not print logs to console",
)
@click.option(
    "--no-write", default=False, is_flag=True, help="Do not export to output path"
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print debug logs to console"
)
@click.version_option(
    package_name="alacorder", prog_name=name, message="%(prog)s beta %(version)s"
)
def cli_table(
    input_path, output_path, count, table, overwrite, no_write, no_log, no_prompt, debug
):
    """
    Write data tables to output path from archive or directory input.

    Args:
        input_path (str): PDF directory or archive input
        output_path (str): Path to table output
        count (int): Total cases to pull from input
        table (str): Table (all, cases, fees, charges, settings, witnesses, attorneys, case_action_summaries, images)
        overwrite (bool): Overwrite existing files at output path
        no_write (bool): Do not export to output path
        no_log(bool): Do not print logs to console
        no_prompt (bool): Skip user input / confirmation prompts
        debug (bool): Print verbose logs to console
    """
    log = not no_log
    if os.path.splitext(output_path)[1] in (".xls", ".xlsx") and not bool(table):
        table = "all"
    elif os.path.splitext(output_path)[1] not in (".xls", ".xlsx") and not bool(table):
        table = click.prompt(
            "Table export choice (cases, fees, charges, disposition, filing, attorneys, witnesses, images, case-action-summary, settings)"
        )
    cf = set(
        input_path,
        output_path,
        count=count,
        table=table,
        overwrite=overwrite,
        no_write=no_write,
        log=log,
        no_prompt=no_prompt,
        debug=debug,
    )
    if cf["DEBUG"]:
        print(cf, cf=cf)
    o = init(cf)
    return o


@main.command(name="archive", help="Create full text archive from case PDFs")
@click.option(
    "--input-path",
    "-in",
    required=True,
    type=click.Path(),
    prompt="PDF directory or archive input",
)
@click.option(
    "--output-path",
    "-out",
    required=True,
    type=click.Path(),
    prompt="Path to archive output",
)
@click.option(
    "--count",
    "-c",
    default=0,
    help="Total cases to pull from input",
    show_default=False,
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--append",
    "-a",
    default=False,
    is_flag=True,
    help="Attempt to append to existing file at output path",
)
@click.option(
    "--no-log",
    default=False,
    is_flag=True,
    help="Do not print logs to console",
)
@click.option(
    "--no-prompt",
    default=False,
    is_flag=True,
    help="Skip user input / confirmation prompts",
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print verbose logs to console"
)
@click.version_option(
    package_name=name.lower(), prog_name=name.upper(), message="%(prog)s %(version)s"
)
def cli_archive(
    input_path, output_path, count, overwrite, append, no_log, no_prompt, debug
):
    """
    Write a full text archive from a directory of case detail PDFs.

    Args:
        input_path (str): PDF directory or archive input
        output_path (str): Path to archive output
        count (int): Total cases to pull from input
        overwrite (bool): Overwrite existing files at output path
        append (bool): Attempt to append to existing file at output path
        no_write (bool): Do not export to output path
        no_prompt (bool): Skip user input / confirmation prompts
        debug (bool): Print verbose logs to console for developers
    """
    log = not no_log
    cf = set(
        input_path,
        output_path,
        archive=True,
        count=count,
        overwrite=overwrite,
        no_write=False,
        log=log,
        no_prompt=no_prompt,
        debug=debug,
    )
    if debug:
        click.echo(cf)
    o = archive(cf, debug=debug)
    return o


@main.command(
    name="pair",
    help="Create blank AIS / unique pairing template",
)
@click.option(
    "--input-path",
    "-in",
    "input_path",
    required=True,
    type=click.Path(),
    prompt="PDF directory or archive input",
)
@click.option(
    "--output-path",
    "-out",
    "output_path",
    required=True,
    type=click.Path(),
    prompt="Path to archive output",
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print verbose logs to console"
)
def cli_pair(input_path, output_path, overwrite, debug):
    conf = cf(
        inputs=input_path,
        outputs=output_path,
        debug=debug,
        overwrite=overwrite,
        log=True,
    )
    p = pairs(conf)
    print("Created pair template at output path.")
    return p


@main.command(
    name="vrr-pairs", help="Create voting rights summary from input cases and pairs"
)
@click.option(
    "--input-path",
    "-in",
    "input_path",
    required=True,
    type=click.Path(),
    prompt="PDF directory or archive input",
)
@click.option(
    "--pairs",
    "-p",
    required=True,
    type=click.Path(),
    prompt="Completed pairs template",
)
@click.option(
    "--output-path",
    "-out",
    "output_path",
    required=True,
    type=click.Path(),
    prompt="Path to table output",
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print verbose logs to console"
)
def cli_vrr(input_path, output_path, pairs, overwrite, debug):
    conf = cf(
        inputs=input_path,
        outputs=output_path,
        pairs=pairs,
        vrr_summary=True,
        debug=debug,
        overwrite=overwrite,
        log=True,
    )
    return vrr(conf)


@main.command(
    name="charge-pairs", help="Create charges summary from input cases and pairs"
)
@click.option(
    "--input-path",
    "-in",
    "input_path",
    required=True,
    type=click.Path(),
    prompt="PDF directory or archive input",
)
@click.option(
    "--pairs",
    "-p",
    required=True,
    type=click.Path(),
    prompt="Completed pairs template",
)
@click.option(
    "--output-path",
    "-out",
    "output_path",
    required=True,
    type=click.Path(),
    prompt="Path to table output",
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print verbose logs to console"
)
def cli_charge_pairs(input_path, output_path, pairs, overwrite, debug):
    conf = cf(
        inputs=input_path,
        outputs=output_path,
        pairs=pairs,
        charges_summary=True,
        debug=debug,
        overwrite=overwrite,
        log=True,
    )
    return charges_summary(conf)


@main.command(
    name="conv-pairs", help="Create convictions summary from input cases and pairs"
)
@click.option(
    "--input-path",
    "-in",
    "input_path",
    required=True,
    type=click.Path(),
    prompt="PDF directory or archive input",
)
@click.option(
    "--pairs",
    "-p",
    required=True,
    type=click.Path(),
    prompt="Completed pairs template",
)
@click.option(
    "--output-path",
    "-out",
    "output_path",
    required=True,
    type=click.Path(),
    prompt="Path to table output",
)
@click.option(
    "--overwrite",
    "-o",
    default=False,
    help="Overwrite existing files at output path",
    is_flag=True,
    show_default=False,
)
@click.option(
    "--debug", "-d", default=False, is_flag=True, help="Print verbose logs to console"
)
def cli_conv_pairs(input_path, output_path, pairs, overwrite, debug):
    conf = cf(
        inputs=input_path,
        outputs=output_path,
        pairs=pairs,
        convictions_summary=True,
        debug=debug,
        overwrite=overwrite,
        log=True,
    )
    return convictions_summary(conf)


def extract_text(path) -> str:
    """
    From path, return full text of PDF as string (PyMuPdf engine required!)
    """
    try:
        doc = fitz.open(path)
    except:
        return ""
    text = ""
    for pg in doc:
        try:
            text += " \n ".join(
                x[4].replace("\n", " ") for x in pg.get_text(option="blocks")
            )
        except:
            pass
    text = re.sub(r"(<image\:.+?>)", "", text).strip()
    return text


if __name__ == "__main__":
    main()

#   #   #   #           GETTER METHODS         #   #   #   #


def get_paths(dirpath):
    """
    From path-like `dirpath`, return list of paths to pdfs in directory
    """
    return glob.glob(dirpath + "**/*.pdf", recursive=True)


def getName(text):
    try:
        return (
            re.sub(
                r"Case Number:",
                "",
                re.search(
                    r"(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*",
                    str(text),
                ).group(1),
            )
            .rstrip("C")
            .strip()
        )
    except:
        return ""


def getAlias(text):
    try:
        return re.sub(
            r":", "", re.search(r"(?:SSN)(.{5,75})(?:Alias)", str(text)).group(1)
        ).strip()
    except:
        return ""


def getDOB(text):
    try:
        return re.sub(
            r"[^\d/]",
            "",
            re.search(r"(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)", str(text)).group(1),
        ).strip()
    except:
        return ""


def getPhone(text):
    try:
        text = str(text)
        text = re.sub(r"[^0-9]", "", re.search(r"(Phone: )(.+)", text).group(2)).strip()
        if len(text) < 7 or text[0:10] == "2050000000":
            return ""
        elif len(text) > 10:
            return text[0:10]
        else:
            return text
    except:
        return ""


def getRace(text):
    try:
        return re.search(r"(B|W|H|A)/(F|M)", str(text)).group(1)
    except:
        return ""


def getSex(text):
    try:
        return re.search(r"(B|W|H|A)/(F|M)", str(text)).group(2)
    except:
        return ""


def getAddress1(text):
    try:
        return re.sub(
            r"Phone.+",
            "",
            re.search(r"(?:Address 1:)(.+)(?:Phone)*?", str(text)).group(1),
        ).strip()
    except:
        return ""


def getAddress2(text):
    try:
        return re.sub(
            r"Defendant Information|JID:.+",
            "",
            re.search(r"(?:Address 2:)(.+)", str(text)).group(1).strip(),
        )
    except:
        return ""


def getCity(text):
    try:
        return re.search(r"(?:City: )(.*)(?:State: )(.*)", str(text)).group(1)
    except:
        return ""


def getState(text):
    try:
        return re.search(r"(?:City: )(.*)(?:State: )(.*)", str(text)).group(2)
    except:
        return ""


def getCountry(text):
    try:
        return re.sub(
            r"Country:",
            "",
            re.sub(
                r"(Enforcement|Party|Country)",
                "",
                re.search(r"Country: (\w*+)", str(text)).group(),
            ).strip(),
        )
    except:
        return ""


def getZipCode(text):
    try:
        return re.sub(
            r"-0000$|[A-Z].+", "", re.search(r"(Zip: )(.+)", str(text)).group(2)
        ).strip()
    except:
        return ""


def getAddress(text):
    try:
        street1 = re.sub(
            r"Phone.+",
            "",
            re.search(r"(?:Address 1:)(.+)(?:Phone)*?", str(text)).group(1),
        ).strip()
    except:
        street1 = ""
    try:
        street2 = getAddress2(text).strip()
    except:
        street2 = ""
    try:
        zipcode = re.sub(
            r"[A-Z].+", "", re.search(r"(Zip: )(.+)", str(text)).group(2)
        ).strip()
    except:
        zipcode = ""
    try:
        city = re.search(r"(?:City: )(.*)(?:State: )(.*)", str(text)).group(1).strip()
    except:
        city = ""
    try:
        state = re.search(r"(?:City: )(.*)(?:State: )(.*)", str(text)).group(2).strip()
    except:
        state = ""
    if len(city) > 3:
        return f"{street1} {street2} {city}, {state} {zipcode}".strip()
    else:
        return f"{street1} {street2} {city} {state} {zipcode}".strip()


def getChargesRows(text):
    m = re.findall(
        r"(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{10,75})", str(text)
    )
    return m


def getFeeSheetRows(text):
    m = re.findall(
        r"(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^A-Za-z\n]*)",
        str(text),
    )
    return m


def getTotalRow(text):
    try:
        mmm = re.search(r"(Total:.+\$[^\n]*)", str(text)).group()
        mm = re.sub(r"[^0-9|\.|\s|\$]", "", str(mmm))
        m = re.findall(r"\d+\.\d{2}", str(mm))
        return m
    except:
        return ["0.00", "0.00", "0.00", "0.00"]


def getTotalAmtDue(text):
    try:
        return float(re.sub(r"[\$\s]", "", getTotalRow(text)[0]))
    except:
        return 0.00


def getTotalAmtPaid(text):
    try:
        return float(re.sub(r"[\$\s]", "", getTotalRow(text)[1]))
    except:
        return 0.00


def getTotalBalance(text):
    try:
        return float(re.sub(r"[\$\s]", "", getTotalRow(text)[2]))
    except:
        return 0.00


def getTotalAmtHold(text):
    try:
        return float(re.sub(r"[\$\s]", "", getTotalRow(text)[3]))
    except:
        return 0.00


def getPaymentToRestore(text):
    try:
        tbal = getTotalBalance(text)
    except:
        return 0.0
    try:
        d999mm = re.search(r"(ACTIVE[^\n]+D999[^\n]+)", str(text)).group()
        d999m = re.findall(r"\$\d+\.\d{2}", str(d999mm))
        d999 = float(re.sub(r"[\$\s]", "", d999m[-1]))
    except:
        d999 = 0.0
    return float(tbal - d999)


def getShortCaseNumber(text):
    try:
        return re.search(r"(\w{2}\-\d{4}-\d{6}\.\d{2})", str(text)).group()
    except:
        return ""


def getCounty(text):
    try:
        return re.search(r"Case Number: (\d\d-\w+) County:", str(text)).group(1)
    except:
        return ""


def getCaseNumber(text):
    try:
        return (
            re.search(r"Case Number: (\d\d-\w+) County:", str(text)).group(1)[0:2]
            + "-"
            + re.search(r"(\w{2}\-\d{4}-\d{6}\.\d{2})", str(text)).group()
        )
    except:
        return ""


def getCaseYear(text):
    try:
        return re.search(r"\w{2}\-(\d{4})-\d{6}\.\d{2}", str(text)).group(1)
    except:
        return ""


def getLastName(text):
    try:
        return getName(text).split(" ")[0].strip()
    except:
        return ""


def getFirstName(text):
    try:
        return getName(text).split(" ")[-1].strip()
    except:
        return ""


def getMiddleName(text):
    try:
        if len(getName(text).split(" ")) > 2:
            return " ".join(getName(text).split(" ")[1:-2]).strip()
        else:
            return ""
    except:
        return ""


def getRelatedCases(text):
    return re.findall(r"(\w{2}\d{12})", str(text))


def getFilingDate(text):
    try:
        return re.sub(
            r"Filing Date: ",
            "",
            re.search(r"Filing Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(),
        ).strip()
    except:
        return ""


def getCaseInitiationDate(text):
    try:
        return re.sub(
            r"Case Initiation Date: ",
            "",
            re.search(
                r"Case Initiation Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)
            ).group(),
        )
    except:
        return ""


def getArrestDate(text):
    try:
        return re.search(r"Arrest Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(1)
    except:
        return ""


def getOffenseDate(text):
    try:
        return re.search(r"Offense Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(1)
    except:
        return ""


def getIndictmentDate(text):
    try:
        return re.search(r"Indictment Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(1)
    except:
        return ""


def getYouthfulDate(text):
    try:
        return re.search(r"Youthful Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(1)
    except:
        return ""


def getRetrieved(text):
    try:
        return re.search(r"Alacourt\.com (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(1)
    except:
        return ""


def getCourtAction(text):
    try:
        return re.search(
            r"Court Action: (BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)",
            str(text),
        ).group(1)
    except:
        return ""


def getCourtActionDate(text):
    try:
        return re.search(r"Court Action Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)).group(
            1
        )
    except:
        return ""


def getDescription(text):
    try:
        return (
            re.search(r"Charge: ([A-Z\.0-9\-\s]+)", str(text))
            .group(1)
            .rstrip("C")
            .strip()
        )
    except:
        return ""


def getJuryDemand(text):
    try:
        return re.search(r"Jury Demand: ([A-Z]+)", str(text)).group(1).strip()
    except:
        return ""


def getInpatientTreatmentOrdered(text):
    try:
        return (
            re.search(r"Inpatient Treatment Ordered: ([YES|NO]?)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getTrialType(text):
    try:
        return re.sub(
            r"[S|N]$", "", re.search(r"Trial Type: ([A-Z]+)", str(text)).group(1)
        ).strip()
    except:
        return ""


def getJudge(text):
    try:
        return (
            re.search(r"Judge: ([A-Z\-\.\s]+)", str(text)).group(1).rstrip("T").strip()
        )
    except:
        return ""


def getProbationOfficeNumber(text):
    try:
        return re.sub(
            r"(0-000000-00)",
            "",
            re.search(r"Probation Office \#: ([0-9\-]+)", str(text)).group(1).strip(),
        )
    except:
        return ""


def getDefendantStatus(text):
    try:
        return (
            re.search(r"Defendant Status: ([A-Z\s]+)", str(text))
            .group(1)
            .rstrip("J")
            .strip()
        )
    except:
        return ""


def getArrestingAgencyType(text):
    try:
        return re.sub(
            r"\n",
            "",
            re.search(r"([^0-9]+) Arresting Agency Type:", str(text)).group(1),
        ).strip()
    except:
        return ""


def getArrestingOfficer(text):
    try:
        return (
            re.search(r"Arresting Officer: ([A-Z\s]+)", str(text))
            .group(1)
            .rstrip("S")
            .rstrip("P")
            .strip()
        )
    except:
        return ""


def getProbationOfficeName(text):
    try:
        return (
            re.search(r"Probation Office Name: ([A-Z0-9]+)", str(text)).group(1).strip()
        )
    except:
        return ""


def getTrafficCitationNumber(text):
    try:
        return (
            re.search(r"Traffic Citation \#: ([A-Z0-9]+)", str(text)).group(1).strip()
        )
    except:
        return ""


def getPreviousDUIConvictions(text):
    try:
        return int(
            re.search(r"Previous DUI Convictions: (\d{3})", str(text)).group(1).strip()
        )
    except:
        return ""


def getCaseInitiationType(text):
    try:
        return (
            re.search(r"Case Initiation Type: ([A-Z\s]+)", str(text))
            .group(1)
            .rstrip("J")
            .strip()
        )
    except:
        return ""


def getDomesticViolence(text):
    try:
        return re.search(r"Domestic Violence: ([YES|NO])", str(text)).group(1).strip()
    except:
        return ""


def getAgencyORI(text):
    try:
        return (
            re.search(r"Agency ORI: ([A-Z\s]+)", str(text)).group(1).rstrip("C").strip()
        )
    except:
        return ""


def getDriverLicenseNo(text):
    try:
        m = re.search(r"Driver License N°: ([A-Z0-9]+)", str(text)).group(1).strip()
        if m == "AL":
            return ""
        else:
            return m
    except:
        return ""


def getSSN(text):
    try:
        return (
            re.search(r"SSN: ([X\d]{3}\-[X\d]{2}-[X\d]{4})", str(text)).group(1).strip()
        )
    except:
        return ""


def getStateID(text):
    try:
        m = re.search(r"([A-Z0-9]{11}?) State ID:", str(text)).group(1).strip()
        if m == "AL000000000":
            return ""
        else:
            return m
    except:
        return ""


def getWeight(text):
    try:
        return int(re.search(r"Weight: (\d+)", str(text)).group(1).strip())
    except:
        return ""


def getHeight(text):
    try:
        return re.search(r"Height : (\d'\d{2})", str(text)).group(1).strip() + '"'
    except:
        return ""


def getEyes(text):
    try:
        return re.search(r"Eyes/Hair: (\w{3})/(\w{3})", str(text)).group(1).strip()
    except:
        return ""


def getHair(text):
    try:
        return re.search(r"Eyes/Hair: (\w{3})/(\w{3})", str(text)).group(2).strip()
    except:
        return ""


def getCountry(text):
    try:
        return re.sub(
            r"(Enforcement|Party|Country:)",
            "",
            re.search(r"Country: (\w*+)", str(text)).group(1).strip(),
        )
    except:
        return ""


def getWarrantIssuanceDate(text):
    try:
        return (
            re.search(r"(\d\d?/\d\d?/\d\d\d\d) Warrant Issuance Date:", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getWarrantActionDate(text):
    try:
        return (
            re.search(r"Warrant Action Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getWarrantIssuanceStatus(text):
    try:
        return re.search(r"Warrant Issuance Status: (\w)", str(text)).group(1).strip()
    except:
        return ""


def getWarrantActionStatus(text):
    try:
        return re.search(r"Warrant Action Status: (\w)", str(text)).group(1).strip()
    except:
        return ""


def getWarrantLocationStatus(text):
    try:
        return re.search(r"Warrant Location Status: (\w)", str(text)).group(1).strip()
    except:
        return ""


def getNumberOfWarrants(text):
    try:
        return (
            re.search(r"Number Of Warrants: (\d{3}\s\d{3})", str(text)).group(1).strip()
        )
    except:
        return ""


def getBondType(text):
    try:
        return re.search(r"Bond Type: (\w)", str(text)).group(1).strip()
    except:
        return ""


def getBondTypeDesc(text):
    try:
        return re.search(r"Bond Type Desc: ([A-Z\s]+)", str(text)).group(1).strip()
    except:
        return ""


def getBondAmt(text):
    try:
        return float(
            re.sub(
                r"[^0-9\.\s]",
                "",
                re.search(r"([\d\.]+) Bond Amount:", str(text)).group(1).strip(),
            )
        )
    except:
        return ""


def getSuretyCode(text):
    try:
        return re.search(r"Surety Code: ([A-Z0-9]{4})", str(text)).group(1).strip()
    except:
        return ""


def getBondReleaseDate(text):
    try:
        return (
            re.search(r"Release Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getFailedToAppearDate(text):
    try:
        return (
            re.search(r"Failed to Appear Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getBondsmanProcessIssuance(text):
    try:
        return (
            re.search(
                r"Bondsman Process Issuance: ([^\n]*?) Bondsman Process Return:",
                str(text),
            )
            .group(1)
            .strip()
        )
    except:
        return ""


def getBondsmanProcessReturn(text):
    try:
        return (
            re.search(r"Bondsman Process Return: (.*?) Number of Subponeas", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getAppealDate(text):
    try:
        return re.sub(
            r"[\n\s]",
            "",
            re.search(r"([\n\s/\d]*?) Appeal Court:", str(text)).group(1).strip(),
        )
    except:
        return ""


def getAppealCourt(text):
    try:
        return re.search(r"([A-Z\-\s]+) Appeal Case Number", str(text)).group(1).strip()
    except:
        return ""


def getOriginOfAppeal(text):
    try:
        return (
            re.search(r"Orgin Of Appeal: ([A-Z\-\s]+)", str(text))
            .group(1)
            .rstrip("L")
            .strip()
        )
    except:
        return ""


def getAppealToDesc(text):
    try:
        return (
            re.search(r"Appeal To Desc: ([A-Z\-\s]+)", str(text))
            .group(1)
            .rstrip("D")
            .rstrip("T")
            .strip()
        )
    except:
        return ""


def getAppealStatus(text):
    try:
        return (
            re.search(r"Appeal Status: ([A-Z\-\s]+)", str(text))
            .group(1)
            .rstrip("A")
            .strip()
        )
    except:
        return ""


def getAppealTo(text):
    try:
        return re.search(r"Appeal To: (\w?) Appeal", str(text)).group(1).strip()
    except:
        return ""


def getLowerCourtAppealDate(text):
    try:
        return re.sub(
            r"[\n\s:\-]",
            "",
            re.search(
                r"LowerCourt Appeal Date: (\d\d?/\d\d?/\d\d\d\d)", str(text)
            ).group(1),
        ).strip()
    except:
        return ""


def getDispositionDateOfAppeal(text):
    try:
        return re.sub(
            r"[\n\s:\-]",
            "",
            re.search(
                r"Disposition Date Of Appeal: (\d\d?/\d\d?/\d\d\d\d)", str(text)
            ).group(1),
        ).strip()
    except:
        return ""


def getDispositionTypeOfAppeal(text):
    try:
        return re.sub(
            r"[\n\s:\-]",
            "",
            re.search(r"Disposition Type Of Appeal: [^A-Za-z]+", str(text)).group(1),
        ).strip()
    except:
        return ""


def getNumberOfSubpoenas(text):
    try:
        return int(
            re.sub(
                r"[\n\s:\-]",
                "",
                re.search(r"Number of Subponeas: (\d{3})", str(text)).group(1),
            ).strip()
        )
    except:
        return ""


def getAdminUpdatedBy(text):
    try:
        return re.search(r"Updated By: (\w{3})", str(text)).group(1).strip()
    except:
        return ""


def getTransferToAdminDocDate(text):
    try:
        return (
            re.search(r"Transfer to Admin Doc Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getTransferDesc(text):
    try:
        return (
            re.search(r"Transfer Desc: ([A-Z\s]{0,15} \d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getTBNV1(text):
    try:
        return (
            re.search(r"Date Trial Began but No Verdict \(TBNV1\): ([^\n]+)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getTBNV2(text):
    try:
        return (
            re.search(r"Date Trial Began but No Verdict \(TBNV2\): ([^\n]+)", str(text))
            .group(1)
            .strip()
        )
    except:
        return ""


def getSentencingRequirementsCompleted(text):
    try:
        return re.sub(
            r"[\n:]|Requrements Completed",
            "",
            ", ".join(re.findall(r"(?:Requrements Completed: )([YES|NO]?)", str(text))),
        )
    except:
        return ""


def getSentencingRequrementsCompleted(
    text,
):  # [sic] On-Line Services doesn't know how to spell requirements lol
    try:
        return re.sub(
            r"[\n:]|Requrements Completed",
            "",
            ", ".join(re.findall(r"(?:Requrements Completed: )([YES|NO]?)", str(text))),
        )
    except:
        return ""


def getSentenceDate(text):
    try:
        return (
            re.search(r"(Sentence Date: )(\d\d?/\d\d?/\d\d\d\d)", str(text))
            .group(2)
            .strip()
        )
    except:
        return ""


def getProbationPeriod(text):
    try:
        return "".join(
            re.search(r"Probation Period: ([^\.]+)", str(text)).group(1).strip()
        ).strip()
    except:
        return ""


def getLicenseSuspPeriod(text):
    try:
        return "".join(
            re.sub(
                r"(License Susp Period:)",
                "",
                re.search(r"License Susp Period: ([^\.]+)", str(text)).group(1).strip(),
            )
        )
    except:
        return ""


def getJailCreditPeriod(text):
    try:
        return "".join(
            re.search(r"Jail Credit Period: ([^\.]+)", str(text)).group(1).strip()
        )
    except:
        return ""


def getSentenceProvisions(text):
    try:
        return re.search(r"Sentence Provisions: ([Y|N]?)", str(text)).group(1).strip()
    except:
        return ""


def getSentenceStartDate(text):
    try:
        return re.sub(
            r"(Sentence Start Date:)",
            "",
            ", ".join(
                re.findall(r"Sentence Start Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            ),
        ).strip()
    except:
        return ""


def getSentenceEndDate(text):
    try:
        return re.sub(
            r"(Sentence End Date:)",
            "",
            ", ".join(
                re.findall(r"Sentence End Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            ),
        ).strip()
    except:
        return ""


def getProbationBeginDate(text):
    try:
        return re.sub(
            r"(Probation Begin Date:)",
            "",
            ", ".join(
                re.findall(r"Probation Begin Date: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            ),
        ).strip()
    except:
        return ""


def getSentenceUpdatedBy(text):
    try:
        return re.sub(
            r"(Updated By:)",
            "",
            ", ".join(re.findall(r"Updated By: (\w{3}?)", str(text))),
        ).strip()
    except:
        return ""


def getSentenceLastUpdate(text):
    try:
        return re.sub(
            r"(Last Update:)",
            "",
            ", ".join(re.findall(r"Last Update: (\d\d?/\d\d?/\d\d\d\d)", str(text))),
        ).strip()
    except:
        return ""


def getProbationRevoke(text):
    try:
        return re.sub(
            r"(Probation Revoke:)",
            "",
            ", ".join(
                re.findall(r"Probation Revoke: (\d\d?/\d\d?/\d\d\d\d)", str(text))
            ),
        ).strip()
    except:
        return ""


def getAttorneys(text):
    att = re.search(
        r"(Type of Counsel Name Phone Email Attorney Code)(.+)(Warrant Issuance)",
        str(text),
        re.DOTALL,
    )
    if att:
        att = att.group(2)
        return re.sub(r"Warrant.+", "", att, re.DOTALL).strip()
    else:
        return ""


def getCaseActionSummary(text):
    cas = re.search(
        r"(Case Action Summary)([^\\]*)(Images\s+?Pages)", str(text), re.DOTALL
    )
    if cas:
        cas = cas.group(2)
        return re.sub(
            r"© Alacourt\.com|Date: Description Doc# Title|Operator", "", cas, re.DOTALL
        ).strip()
    else:
        return ""


def getImages(text):
    imgs = re.findall(
        r"(Images\s+?Pages)([^\\n]*)(END OF THE REPORT)", str(text), re.DOTALL
    )
    if len(imgs) > 1:
        imgs = "; ".join(imgs).strip()
    elif len(imgs) == 1:
        return imgs[0].strip()
    else:
        return ""


def getWitnesses(text):
    wit = re.search(r"(Witness.+?Case Action Summary)", str(text), re.DOTALL)
    if wit:
        wit = re.sub(
            r"Witness # Date Served Service Type Attorney Issued Type   SJIS Witness List   Date Issued   Subpoena",
            "",
            wit,
            re.DOTALL,
        )
        wit = re.sub(
            r"Date: Time Code Comments   Case Action Summary", "", wit, re.DOTALL
        )
        wit = re.sub(r"© Alacourt.com \d\d?/\d\d?/\d\d\d\d", "", wit, re.DOTALL)
        wit = re.sub(
            r"Witness List    4 Requesting Party Name Witness # Date Served Service Type Attorney Issued Type   Date Issued   Subpoena",
            "",
            wit,
            re.DOTALL,
        )
        return wit.strip()
    else:
        return ""


def getSettings(text):
    settings = re.search(r"(Settings.+Court Action)", str(text), re.DOTALL)
    if settings:
        out = settings.group(2)
        out = re.sub(
            r"Settings   Date: Que: Time: Description:   Settings", "", out, re.DOTALL
        )
        out = re.sub(
            r"Settings   Settings Date: Que: Time: Description:", "", out, re.DOTALL
        )
        out = re.sub(
            r"Disposition Charges   # Code Court Action Category Cite Court Action",
            "",
            out,
            re.DOTALL,
        )
        return out.strip()
    else:
        return ""
