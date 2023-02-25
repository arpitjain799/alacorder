# alac 75 (in beta)
# alacorder
# sam robson 

import os
import sys
import glob
import re
import math
import numpy as np
import pandas as pd
import time
import warnings
import click
import inspect
import PyPDF2

pd.set_option("mode.chained_assignment",None)
pd.set_option("display.notebook_repr_html",True)
pd.set_option("display.width",None)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 100)

###########
## WRITE ##
###########

def write(conf, outputs, archive=False):
    """
    Writes outputs to path in conf
    """
    path_in = conf['INPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    launch = conf['LAUNCH']
    compress = conf['COMPRESS']
    path_out = conf['OUTPUT_PATH'] if conf['MAKE'] != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf['MAKE'] == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    if dedupe == True:
        outputs = outputs.drop_duplicates()

    if out_ext == ".xls":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table",engine="openpyxl")
        except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            try:
                with pd.ExcelWriter(path_out,engine="xlwt") as writer:
                    outputs.to_excel(writer, sheet_name="output-table")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                try:
                    os.remove(path_out)
                except:
                    pass
                outputs.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                if warn or print_log:
                    click.echo(f"Fallback export to {os.path.splitext(path_out)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
    if out_ext == ".xlsx":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table", engine="openpyxl")
        except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
            try:
                with pd.ExcelWriter(path_out[0:-1]) as writer:
                    outputs.to_excel(writer, sheet_name="output-table", engine="xlsxwriter")
            except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                try:
                    os.remove(path_out)
                except:
                    pass
                outputs.to_json(os.path.splitext(path_out)[0] + ".json.zip", orient='table',compression="zip")
                if warn or print_log:
                    click.echo(f"Fallback export to {os.path.splitext(path_out)}.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
    elif out_ext == ".pkl":
        if compress:
            outputs.to_pickle(path_out+".xz",compression="xz")
        else:
            outputs.to_pickle(path_out)
    elif out_ext == ".xz":
        outputs.to_pickle(path_out,compression="xz")
    elif out_ext == ".json":
        if compress:
            outputs.to_json(path_out,orient='table',compression="zip")
        else:
            outputs.to_json(path_out,orient='table')
    elif out_ext == ".csv":
        if compress:
            outputs.to_csv(path_out,escapechar='\\',compression="zip")
        else:
            outputs.to_csv(path_out,escapechar='\\')
    elif out_ext == ".txt":
        outputs.to_string(path_out)
    elif out_ext == ".dta":
        outputs.to_stata(path_out)
    elif out_ext == ".parquet":
        if compress:
            outputs.to_parquet(path_out,compression="brotli")
        else:
            outputs.to_parquet(path_out)
    else:
        pass
    return outputs
def archive(conf):
    """
    Write full text archive to file.pkl.xz
    """
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    arc_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    compress = conf['COMPRESS']
    table = conf['TABLE']
    debug = conf['DEBUG']
    start_time = time.time()
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    if warn == False:
        warnings.filterwarnings("ignore")
    if warn or print_log or debug:
        click.echo(click.style("* ",blink=True) + "Writing full text archive from cases...")

    if not from_archive:
        allpagestext = pd.Series(queue).map(lambda x: getPDFText(x))
    else:
        allpagestext = pd.Series(queue)

    outputs = pd.DataFrame({
        'Path': queue if from_archive else np.nan,
        'AllPagesText': allpagestext,
        'Timestamp': start_time,
    })

    outputs.fillna('',inplace=True)

    if dedupe == True:
        outputs = outputs.drop_duplicates()

    if not no_write and out_ext == ".xz":
        outputs.to_pickle(path_out,compression="xz")
    if not no_write and out_ext == ".parquet":
        if compress:
            outputs.to_parquet(path_out+".parquet",compression="brotli")
        else:
            outputs.to_parquet(path_out+".parquet",compression="brotli")
    if not no_write and out_ext == ".json":
        if compress:
            outputs.to_json(path_out,orient='table',compression="zip")
        else:
            outputs.to_json(path_out,orient='table')
    complete(conf, outputs)
    return outputs
def init(conf):
    """
    Route config to function corresponding to MAKE, TABLE in conf
    """
    a = []
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    if conf.MAKE == "multiexport":
        a = cases(conf)
    if conf.MAKE == "archive":
        a = archive(conf)
    if conf['TABLE'] == "cases":
        a = caseinfo(conf)
    if conf['TABLE'] == "fees":
        a = fees(conf)
    if conf['TABLE'] == "charges":
        a = charges(conf)
    if conf['TABLE'] == "disposition":
        a = charges(conf)
    if conf['TABLE'] == "filing":
        a = charges(conf)
    return a
def table(conf):
    """
    Route config to parse...() function corresponding to table attr
    """
    a = []
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    if conf.MAKE == "multiexport":
        a = cases(conf)
    if conf['TABLE'] == "cases":
        a = caseinfo(conf)
    if conf['TABLE'] == "fees":
        a = fees(conf)
    if conf['TABLE'] == "charges":
        a = charges(conf)
    if conf['TABLE'] == "disposition":
        a = charges(conf)
    if conf['TABLE'] == "filing":
        a = charges(conf)
    return a
def fees(conf):
    """
    Return fee sheets with case number as DataFrame from batch
    fees = pd.DataFrame({'CaseNumber': '',
        'Code': '', 'Payor': '', 'AmtDue': '',
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''})
    """
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    from_archive = True if conf['IS_FULL_TEXT'] else False
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")
    fees = pd.DataFrame()
    # fees = pd.DataFrame({'CaseNumber': '',
    #  'Code': '', 'Payor': '', 'AmtDue': '',
    # 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
    if not conf['NO_BATCH']:
        batches = batcher(conf)
    else:
        batches = np.array_split(queue, 1)

    batchcount = len(batches)
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = c.map(lambda x: getPDFText(x))

            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            #try:
            b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(str(b.loc[x].AllPagesText)))
            feesheet = b['FeeOutputs'].map(lambda x: x[6])
            #except (AttributeError,IndexError):
            #   pass

            feesheet = feesheet.dropna() 
            fees =fees.dropna()
            feesheet = feesheet.tolist() #  -> [df, df, df]
            feesheet = pd.concat(feesheet,axis=0,ignore_index=True) 
            fees = fees.append(feesheet, ignore_index=True)
            fees.fillna('',inplace=True)
            fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))
    if not no_write:
        write(conf, fees)
    complete(conf)
    return fees
def charges(conf):
    """
    Return charges with case number as DataFrame from batch
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''})
    """
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    dedupe = conf['DEDUPE']
    from_archive = True if conf['IS_FULL_TEXT'] else False

    if warn == False:
        warnings.filterwarnings("ignore")

    if not conf['NO_BATCH']:
        batches = batcher(conf)
    else:
        batches = np.array_split(queue, 1)

    start_time = time.time()
    charges = pd.DataFrame()
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = pd.Series(c).map(lambda x: getPDFText(x))

            ## b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
            b['CaseNumber'] = b['AllPagesText'].map(lambda x: getCaseNumber(x))
            b['ChargesOutputs'] = b.index.map(lambda x: getCharges(str(b.loc[x].AllPagesText)))


            chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
            chargetabs = chargetabs.dropna()
            chargetabs = chargetabs.tolist()
            charges = charges.append(chargetabs)
            charges.fillna('',inplace=True)

            if dedupe == True:
                charges = charges.drop_duplicates()

        if table == "filing":
            is_disp = charges['Disposition']
            is_filing = is_disp.map(lambda x: False if x == True else True)
            charges = charges[is_filing]
            charges.drop(columns=['CourtAction','CourtActionDate'],inplace=True)

        if table == "disposition":
            is_disp = charges.Disposition.map(lambda x: True if x == True else False)
            charges = charges[is_disp]
        if not no_write:
            write(conf, charges)

    complete(conf)
    return charges
def cases(conf):
    """
    Return [cases, fees, charges] tables as List of DataFrames from batch
    See API docs for table specific outputs
    """
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    compress = conf['COMPRESS']
    overwrite = conf['OVERWRITE']
    path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT'] else False
    start_time = time.time()
    arc_ext = conf['OUTPUT_EXT']
    cases = pd.DataFrame()
    fees = pd.DataFrame()
    charges = pd.DataFrame()
    if not conf['NO_BATCH']:
        batches = batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    if warn == False:
        warnings.filterwarnings("ignore")
    temp_no_write_arc = False
    temp_no_write_tab = False
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            b = pd.DataFrame()
            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = pd.Series(c).map(lambda x: getPDFText(x))
            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
            b['ChargesOutputs'] = b.index.map(lambda x: getCharges(str(b.loc[x].AllPagesText)))
            b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
            b['Dispositioncharges'] = b['ChargesOutputs'].map(lambda x: x[1])
            b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
            b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
            b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
            b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
            b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
            b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
            b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
            b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
            b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
            b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
            b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
            b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
            b['ChargeCodes'] = b['ChargesOutputs'].map(lambda x: x[14])
            b['ConvictionCodes'] = b['ChargesOutputs'].map(lambda x: x[15])
            b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(str(b.loc[x].AllPagesText)))
            b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
            b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: getPaymentToRestore(x))
            # b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
            b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
            b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
            b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])
            logdebug(conf, b['FeeSheet'])

            feesheet = b['FeeOutputs'].map(lambda x: x[6])
            feesheet = feesheet.dropna()
            feesheet = feesheet.tolist() # -> [df, df, df]

            #try:
            feesheet = pd.concat(feesheet,axis=0,ignore_index=True) #  -> batch df
            #except:
            #   pass
            #try:
            fees = fees.append(feesheet)
            #except:
            #   pass
            logdebug(conf, fees)
            chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
            chargetabs = chargetabs.dropna()
            # charges = charges.dropna()
            chargetabs = chargetabs.tolist()


            chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)

            charges = charges.append(chargetabs,ignore_index=True)


            feesheet['AmtDue'] = feesheet['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            feesheet['AmtPaid'] = feesheet['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
            feesheet['Balance'] = feesheet['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
            feesheet['AmtHold'] = feesheet['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))

            b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
            b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['PaymentToRestore'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))

            if bool(archive_out) and len(arc_ext) > 2 and i > 0 and not no_write:
                if os.path.getsize(archive_out) > 1000:
                    temp_no_write_arc = True
            if bool(path_out) and i > 0 and not no_write:
                if os.path.getsize(path_out) > 1000:
                    temp_no_write_tab = True
            if i == len(batches) - 1:
                temp_no_write_arc = False
                temp_no_write_tab = False

            if (i % 5 == 0 or i == len(batches) - 1) and not no_write and temp_no_write_arc == False:
                if bool(archive_out) and len(arc_ext) > 2:
                    timestamp = start_time
                    q = pd.Series(queue) if conf.IS_FULL_TEXT == False else pd.NaT
                    ar = pd.DataFrame({
                        'Path': q,
                        'AllPagesText': b['AllPagesText'],
                        'Timestamp': timestamp
                    },index=range(0,conf.COUNT))
                    try:
                        arch = pd.concat([arch, ar],ignore_index=True,axis=0)
                    except:
                        pass
                    arch.fillna('',inplace=True)
                    arch.dropna(inplace=True)
                    arch.to_pickle(archive_out,compression="xz")

            b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','ChargesTable','FeeSheet'],inplace=True)

            b.fillna('',inplace=True)
            # newcases = [cases, b]
            cases = cases.append(b, ignore_index=True)

            if dedupe == True:
                cases = cases.drop_duplicates()
                fees = fees.drop_duplicates()
                charges = charges.drop_duplicates()

            if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
                if out_ext == ".xls":
                    try:
                        with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                    except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                        click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
                        with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                elif out_ext == ".xlsx":
                    try:
                        with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                    except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                        try:
                            if warn:
                                click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
                            with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                                cases.to_excel(writer, sheet_name="cases")
                                fees.to_excel(writer, sheet_name="fees")
                                charges.to_excel(writer, sheet_name="charges")
                        except (ImportError, FileNotFoundError, IndexError, ValueError, ModuleNotFoundError):
                            try:
                                cases.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                                fees.to_json(os.path.splitext(path_out)[0] + "-fees.json.zip",orient='table')
                                charges.to_json(os.path.splitext(path_out)[0] + "-charges.json.zip",orient='table')
                                echo(conf,"Fallback export to " + os.path.splitext(path_out)[0] + "-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
                            except (ImportError, FileNotFoundError, IndexError, ValueError):
                                click.echo("Failed to export!")

                elif out_ext == ".json":
                    if compress:
                        cases.to_json(path_out,orient='table',compression="zip")
                    else:
                        cases.to_json(path_out,orient='table')
                elif out_ext == ".csv":
                    if compress:
                        cases.to_csv(path_out,escapechar='\\',compression="zip")
                    else:
                        cases.to_csv(path_out,escapechar='\\')
                elif out_ext == ".md":
                    cases.to_markdown(path_out)
                elif out_ext == ".txt":
                    cases.to_string(path_out)
                elif out_ext == ".dta":
                    cases.to_stata(path_out)
                elif out_ext == ".parquet":
                    if compress:
                        cases.to_parquet(path_out, compression="brotli")
                    else:
                        cases.to_parquet(path_out)
                else:
                    pd.Series([cases, fees, charges]).to_string(path_out)
                try:
                    if dedupe == True and outputs.shape[0] < queue.shape[0]:
                        click.echo(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
                except:
                    pass

        complete(conf)
        return [cases, fees, charges]
def caseinfo(conf):
    """
    Return [cases, fees, charges] tables as List of DataFrames from batch
    See API docs for table specific outputs
    """
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    count = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    compress = conf['COMPRESS']
    overwrite = conf['OVERWRITE']
    path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT'] else False
    start_time = time.time()
    arc_ext = conf['OUTPUT_EXT']
    cases = pd.DataFrame()
    if not conf['NO_BATCH']:
        batches = batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    if warn == False:
        warnings.filterwarnings("ignore")
    temp_no_write_arc = False
    temp_no_write_tab = False
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            b = pd.DataFrame()
            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = pd.Series(c).map(lambda x: getPDFText(x))
            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
            b['ChargesOutputs'] = b.index.map(lambda x: getCharges(str(b.loc[x].AllPagesText)))
            b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
            b['Dispositioncharges'] = b['ChargesOutputs'].map(lambda x: x[1])
            b['FilingCharges'] = b['ChargesOutputs'].map(lambda x: x[2])
            b['CERVConvictions'] = b['ChargesOutputs'].map(lambda x: x[3])
            b['PardonConvictions'] = b['ChargesOutputs'].map(lambda x: x[4])
            b['PermanentConvictions'] = b['ChargesOutputs'].map(lambda x: x[5])
            b['ConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[6])
            b['ChargeCount'] = b['ChargesOutputs'].map(lambda x: x[7])
            b['CERVChargeCount'] = b['ChargesOutputs'].map(lambda x: x[8])
            b['PardonChargeCount'] = b['ChargesOutputs'].map(lambda x: x[9])
            b['PermanentChargeCount'] = b['ChargesOutputs'].map(lambda x: x[10])
            b['CERVConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[11])
            b['PardonConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[12])
            b['PermanentConvictionCount'] = b['ChargesOutputs'].map(lambda x: x[13])
            b['ChargeCodes'] = b['ChargesOutputs'].map(lambda x: x[14])
            b['ConvictionCodes'] = b['ChargesOutputs'].map(lambda x: x[15])
            b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(str(b.loc[x].AllPagesText)))
            b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
            b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: getPaymentToRestore(x))
            # b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
            b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
            b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
            b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])


            b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['PaymentToRestore'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))

            if bool(archive_out) and len(arc_ext) > 2 and i > 0 and not no_write:
                if os.path.getsize(archive_out) > 1000:
                    temp_no_write_arc = True
            if bool(path_out) and i > 0 and not no_write:
                if os.path.getsize(path_out) > 1000:
                    temp_no_write_tab = True
            if i == len(batches) - 1:
                temp_no_write_arc = False
                temp_no_write_tab = False

            if (i % 5 == 0 or i == len(batches) - 1) and not no_write and temp_no_write_arc == False:
                if bool(archive_out) and len(arc_ext) > 2:
                    timestamp = start_time
                    q = pd.Series(queue) if conf.IS_FULL_TEXT == False else pd.NaT
                    ar = pd.DataFrame({
                        'Path': q,
                        'AllPagesText': b['AllPagesText'],
                        'Timestamp': timestamp
                    },index=range(0,conf.COUNT))
                    try:
                        arch = pd.concat([arch, ar],ignore_index=True,axis=0)
                    except:
                        pass
                    arch.fillna('',inplace=True)
                    arch.dropna(inplace=True)
                    arch.to_pickle(archive_out,compression="xz")

            b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','FeeSheet'],inplace=True)

            if dedupe == True:
                cases = cases.drop_duplicates()

            b.fillna('',inplace=True)
            cases = cases.append(b, ignore_index=True)

            if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
                if out_ext == ".xls":
                    try:
                        with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                    except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                        click.echo(f"openpyxl engine failed! Trying xlsxwriter...")
                        with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                elif out_ext == ".xlsx":
                    try:
                        with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                    except (ImportError, IndexError, ValueError, ModuleNotFoundError, FileNotFoundError):
                        try:
                            if warn:
                                click.secho(f"openpyxl engine failed! Trying xlsxwriter...")
                            with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                                cases.to_excel(writer, sheet_name="cases")
                        except (ImportError, FileNotFoundError, IndexError, ValueError, ModuleNotFoundError):
                            try:
                                cases.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                                echo(conf,"Fallback export to " + os.path.splitext(path_out)[0] + "-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")
                            except (ImportError, FileNotFoundError, IndexError, ValueError):
                                click.secho("Failed to export!")

                elif out_ext == ".json":
                    if compress:
                        cases.to_json(path_out,orient='table',compression="zip")
                    else:
                        cases.to_json(path_out,orient='table')
                elif out_ext == ".csv":
                    if compress:
                        cases.to_csv(path_out,escapechar='\\',compression="zip")
                    else:
                        cases.to_csv(path_out,escapechar='\\')
                elif out_ext == ".md":
                    cases.to_markdown(path_out)
                elif out_ext == ".txt":
                    cases.to_string(path_out)
                elif out_ext == ".dta":
                    cases.to_stata(path_out)
                elif out_ext == ".parquet":
                    if compress:
                        cases.to_parquet(path_out, compression="brotli")
                    else:
                        cases.to_parquet(path_out)
                else:
                    cases.to_string(path_out)
                try:
                    if dedupe == True and outputs.shape[0] < queue.shape[0]:
                        click.secho(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
                except:
                    pass

        complete(conf)
        return cases
def map(conf, *args):
    """
    Custom Parsing
    From config object and custom getter functions defined like below:

    def getter(text: str):
        out = re.search(...)
        ...
        return str(out)

    Creates DataFrame with column for each getter column output and row for each case in queue

    """
    path_in = conf['INPUT_PATH']
    path_out = conf['OUTPUT_PATH']
    out_ext = conf['OUTPUT_EXT']
    max_cases = conf['COUNT']
    queue = conf['QUEUE']
    print_log = conf['LOG']
    warn = conf['WARN']
    no_write = conf['NO_WRITE']
    dedupe = conf['DEDUPE']
    table = conf['TABLE']
    dedupe = conf['DEDUPE']
    path_out = conf['OUTPUT_PATH'] if config.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if config.MAKE == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    if warn == False:
        warnings.filterwarnings("ignore")

    batches = config.batcher(conf)
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    start_time = time.time()
    alloutputs = []
    uselist = False
    func = pd.Series(args).map(lambda x: 1 if inspect.isfunction(x) else 0)
    funcs = func.index.map(lambda x: args[x] if func[x]>0 else np.nan)
    no_funcs = func.index.map(lambda x: args[x] if func[x]==0 else np.nan)
    no_funcs = no_funcs.dropna()
    countfunc = func.sum()
    column_getters = pd.DataFrame(columns=['Name','Method','Arguments'],index=(range(0,countfunc)))
    df_out = pd.DataFrame()
    local_get = []
    for i, x in enumerate(funcs):
        if inspect.isfunction(x):
            column_getters.Name[i] = x.__name__
            column_getters.Method[i] = x
    for i, x in enumerate(args):
        if inspect.isfunction(x) == False:
            column_getters.Arguments.iloc[i-1] = x
    if print_log:
        click.echo(column_getters)
    def ExceptionWrapperArgs(mfunc, x, *args):
        unpacked_args = args
        a = mfunc(x, unpacked_args)
        return a

    def ExceptionWrapper(mfunc, x):
        a = str(mfunc(x))
        return a
    temp_no_write_tab = False
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if bool(path_out) and i > 0 and not no_write:
                if os.path.getsize(path_out) > 500:
                    temp_no_write_tab = True
            if i == len(batches) - 1:
                temp_no_write_tab = False
            if from_archive == True:
                allpagestext = c
            else:
                allpagestext = pd.Series(c).map(lambda x: getPDFText(x))
            df_out['CaseNumber'] = allpagestext.map(lambda x: getCaseNumber(x))
            for i, getter in enumerate(column_getters.Method.tolist()):
                arg = column_getters.Arguments[i]
                try:
                    name = getter.__name__.strip()[3:]
                    col = pd.DataFrame({
                    name: allpagestext.map(lambda x: getter(x, arg))
                        })
                except (AttributeError,TypeError):
                    try:
                        name = getter.__name__.strip()[3:]
                        col = pd.DataFrame({
                        name: allpagestext.map(lambda x: getter(x))
                                })
                    except (AttributeError,TypeError):
                        name = getter.__name__.strip()[2:-1]
                        col = pd.DataFrame({
                        name: allpagestext.map(lambda x: ExceptionWrapper(x,arg))
                                })
                n_out = [df_out, col]
                df_out = pd.concat([df_out,col.reindex(df_out.index)],axis=1)
                df_out = df_out.dropna(axis=1)
                df_out = df_out.convert_dtypes()
                if dedupe == True:
                    df_out = df_out.drop_duplicates()

            if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
                write(conf, df_out) # rem alac
    if not no_write:
        write(conf, df_out) # rem alac
    complete(conf, start_time, df_out)
    return df_out


############
## CONFIG ##
############

def setinputs(path):
    found = 0
    is_full_text = False
    good = False
    pickle = None
    queue = pd.Series()

    if os.path.isdir(path): # if PDF directory -> good
        queue = pd.Series(glob.glob(path + '**/*.pdf', recursive=True))
        if queue.shape[0] > 0:
            found = len(queue)
            good = True
    elif os.path.isfile(path) and (os.path.splitext(path)[1] == ".xz" or os.path.splitext(path)[1] == ".pkl"): # if archive -> good
        good = True
        try:
            pickle = pd.read_pickle(path,compression="xz")
            queue = pickle['AllPagesText']
            is_full_text = True
            found = len(queue)
        except:
            try:
                pickle = pd.read_pickle(path)
                queue = pickle['AllPagesText']
                is_full_text = True
                found = len(queue)
            except:
                good = False
    else:
        good = False

    if good:
        echo = click.style(f"\nFound {found} cases in input.",italic=True,fg='bright_yellow')
    else:
        echo = click.style(f"""Alacorder failed to configure input! Try again with a valid PDF directory or full text archive path, or run 'python -m alacorder --help' in command line for more details.""",fg='red',bold=True)
        if not debug:
            raise Exception("Alacorder failed and quit.")

    out = pd.Series({
        'INPUT_PATH': path,
        'IS_FULL_TEXT': is_full_text,
        'QUEUE': queue,
        'FOUND': found,
        'GOOD': good,
        'PICKLE': pickle,
        'ECHO': echo
    })
    return out
def setoutputs(path):
    good = False
    make = None
    pickle = None
    exists = os.path.isfile(path)
    ext = os.path.splitext(path)[1]
    if os.path.splitext(path)[1] == ".zip": # if vague due to compression, assume archive
        ext = os.path.splitext(path)[1] + os.path.splitext(os.path.splitext(path)[0])[1]
        make = "archive"
        good = True
    if os.path.splitext(path)[1] == ".xz": # if output is existing archive
        make = "archive"
        good = True
    elif os.path.splitext(path)[1] == ".xlsx" or os.path.splitext(path)[1] == ".xls": # if output is multiexport
        make = "multiexport"
        good = True
    elif os.path.splitext(path)[1] == ".csv" or os.path.splitext(path)[1] == ".dta" or os.path.splitext(path)[1] == ".json" or os.path.splitext(path)[1] == ".txt" or os.path.splitext(path)[1] == ".pkl":
        make = "singletable"
        good = True
    if good:
        echo = click.style(f"""Output path successfully configured for {"table" if (make == "multiexport" or make == "singletable") else "archive"} export.\n""",italic=True,fg='bright_yellow')
    else:
        echo = click.style(f"Alacorder failed to configure output! Try again with a valid path to a file with a supported extension, or run 'python -m alacorder --help' in command line for help.",fg='red',bold=True)

    out = pd.Series({
        'OUTPUT_PATH': path,
        'OUTPUT_EXT': ext,
        'MAKE': make,
        'GOOD': good,
        'EXISTING_FILE': exists,
        'ECHO': echo
    })
    return out
def set(inputs,outputs,count=0,table='',overwrite=False,launch=False,log=True,dedupe=False,warn=False,no_write=False,no_prompt=False,skip_echo=False,debug=False,no_batch=False, compress=False):

    if isinstance(inputs, str):
        inputs = setinputs(inputs)
    if isinstance(outputs, str):
        outputs = setoutputs(outputs)

    status_code = []
    echo = ""
    will_archive = False
    will_overwrite = False
    good = True

    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')

    ## DEDUPE
    content_len = inputs.QUEUE.shape[0]
    if dedupe == True:
        content_len
        queue = inputs.QUEUE.drop_duplicates()
        dif = content_len - queue.shape[0]
        if debug:
            click.secho(f"Removed {dif} duplicate cases from queue.",fg='bright_yellow',bold=True)
            click.secho(queue)
    else:
        queue = inputs.QUEUE

    ## COUNT
    content_len = inputs['FOUND']
    if content_len > count and count != 0:
        ind = count - 1
        queue = inputs.QUEUE[0:ind]
    elif count > content_len and content_len > 0:
        count = inputs.QUEUE.shape[0]
    else:
        queue = inputs.QUEUE

    echo += echo_conf(inputs.INPUT_PATH,outputs.MAKE,outputs.OUTPUT_PATH,overwrite,no_write,dedupe,launch,warn,no_prompt,compress)

    out = pd.Series({
        'GOOD': good,
        'ECHO': echo,
        'STATUS_CODES': status_code,

        'QUEUE': queue,
        'COUNT': count,
        'IS_FULL_TEXT': bool(inputs.IS_FULL_TEXT),
        'MAKE': outputs.MAKE,
        'TABLE': table,

        'INPUT_PATH': inputs.INPUT_PATH,
        'OUTPUT_PATH': outputs.OUTPUT_PATH,
        'OUTPUT_EXT': outputs.OUTPUT_EXT,

        'OVERWRITE': will_overwrite,
        'FOUND': inputs.FOUND,

        'DEDUPE': dedupe, # not ready (well none of its ready but especially that)
        'LOG': log,
        'WARN': warn,
        'LAUNCH': launch,
        'DEBUG': debug,
        'NO_PROMPT': no_prompt,
        'NO_WRITE': no_write,
        'NO_BATCH': no_batch,
        'COMPRESS': compress
    })

    return out
def batcher(conf):
    q = conf['QUEUE']
    if conf.IS_FULL_TEXT == False:
        if conf.FOUND < 1000:
            batchsize = 250
        elif conf.FOUND > 10000:
            batchsize = 2500
        else:
            batchsize = 1000
        batches = np.array_split(q, math.floor(conf.FOUND/batchsize))
    else:
        batches = np.array_split(q, 1)
    return batches
# same as calling set(setinputs(path), setoutputs(path), **kwargs)
def setpaths(input_path, output_path, count=0, table='', overwrite=False, launch=False, log=True, dedupe=False, warn=False,no_write=False, no_prompt=False, skip_echo=False, debug=False, no_batch=False, compress=False):
    if not debug:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    a = setinputs(input_path)
    if log:
        click.secho(a.ECHO)
    b = setoutputs(output_path)
    if b.MAKE == "archive":
        compress = True
    if log:
        click.secho(b.ECHO)
    c = set(a,b, count=count, table=table, overwrite=overwrite, launch=launch, log=log, dedupe=dedupe, warn=warn, no_write=no_write, no_prompt=no_prompt, debug=debug, no_batch=no_batch, compress=compress)
    if log:
        click.secho(c.ECHO)
    return c

#############
## GETTERS ##
#############

def getPDFText(path: str) -> str:
    """Returns PyPDF2 extract_text() outputs for all pages from path"""
    text = ""
    pdf = PyPDF2.PdfReader(path)
    for pg in pdf.pages:
        text += pg.extract_text()
    return text
def getCaseNumber(text: str):
    """Returns full case number with county number prefix from case text"""
    try:
        county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
        case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip()
        return case_num
    except (IndexError, AttributeError):
        return ""
def getName(text: str):
    """Returns name from case text"""
    name = ""
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    return name
def getDOB(text: str):
    """Returns DOB from case text"""
    dob = ""
    if bool(re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL)):
        dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
    return dob
def getTotalAmtDue(text: str):
    """Returns total amt due from case text"""
    try:
        trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
        totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
        if len(totalrow.split("$")[-1])>5:
            totalrow = totalrow.split(" . ")[0]
        tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","")
    except IndexError:
        tdue = ""
    return tdue
def getAddress(text: str):
    """Returns address from case text"""
    try:
        street_addr = re.search(r'(Address 1\:)(.+)(?:Phone)*?', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        street_addr = ""
    try:
        zip_code = re.search(r'(Zip\: )(.+)', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        zip_code = ""
    try:
        city = re.search(r'(City\: )(.*)(State\: )(.*)', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        city = ""
    try:
        state = re.search(r'(?:City\: ).*(?:State\: ).*', str(text), re.MULTILINE).group(4).strip()
    except (IndexError, AttributeError):
        state = ""
    address = street_addr + " " + city + ", " + state + " " + zip_code
    if len(address) < 5:
        address = ""
    address = address.replace("00000-0000","").replace("%","").strip()
    address = re.sub(r'([A-Z]{1}[a-z]+)','',address)
    return address
def getRace(text: str):
    """Return race from case text"""
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    race = racesex.group(1).strip()
    sex = racesex.group(2).strip()
    return race
def getSex(text: str):
    """Return sex from case text"""
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    sex = racesex.group(2).strip()
    return sex
def getNameAlias(text: str):
    """Return name from case text"""
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    try:
        alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":","").replace("Alias 1","").strip()
    except (IndexError, AttributeError):
        alias = ""
    if alias == "":
        return name
    else:
        return name + "\r" + alias
def getCaseInfo(text: str): ## FIX: DEPRECATED -> replace with small getters in Cases() and CaseInfo()
    """Returns case information from case text -> cases table"""
    case_num = ""
    name = ""
    alias = ""
    race = ""
    sex = ""
    address = ""
    dob = ""
    phone = ""

    try:
        county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
        case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip()
    except (IndexError, AttributeError):
        pass

    if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.{5,1000})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.{5,1000})(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    try:
        alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":","").replace("Alias 1","").strip()
    except (IndexError, AttributeError):
        pass
    else:
        pass
    try:
        dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
        phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
        phone = re.sub(r'[^0-9]','',phone)
        if len(phone) < 7:
            phone = ""
        if len(phone) > 10 and phone[-3:] == "000":
            phone = phone[0:9]
    except (IndexError, AttributeError):
        dob = ""
        phone = ""
    try:
        racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
        race = racesex.group(1).strip()
        sex = racesex.group(2).strip()
    except (IndexError, AttributeError):
        pass
    try:
        street_addr = re.search(r'(Address 1\:)(.+)(?:Phone)*?', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        street_addr = ""
    try:
        zip_code = re.search(r'(Zip\: )(.+)', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        zip_code = ""
    try:
        city = re.search(r'(City\: )(.*)(State\: )(.*)', str(text), re.MULTILINE).group(2).strip()
    except (IndexError, AttributeError):
        city = ""
    try:
        state = re.search(r'(?:City\: ).*(?:State\: ).*', str(text), re.MULTILINE).group(4).strip()
    except (IndexError, AttributeError):
        state = ""

    address = street_addr + " " + city + ", " + state + " " + zip_code
    if len(address) < 5:
        address = ""
    address = address.replace("00000-0000","").replace("%","").strip()
    address = re.sub(r'([A-Z]{1}[a-z]+)','',address)
    case = [case_num, name, alias, dob, race, sex, address, phone]
    return case
def getPhone(text: str):
    """Return phone number from case text"""
    try:
        phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
        phone = re.sub(r'[^0-9]','',phone)
        if len(phone) < 7:
            phone = ""
        if len(phone) > 10 and phone[-3:] == "000":
            phone = phone[0:9]
    except (IndexError, AttributeError):
        phone = ""
    return phone
def getFeeSheet(text: str):
    """
    Return fee sheet and fee summary outputs from case text
    List: [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]
    feesheet = feesheet[['CaseNumber', 'FeeStatus', 'AdminFee', 'Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
    """
    actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
    if len(actives) == 0:
        return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    else:
        try:
            trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
            totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
            if len(totalrow.split("$")[-1])>5:
                totalrow = totalrow.split(" . ")[0]
            tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
            tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","")
            tpaid = totalrow.split("$")[2].strip().replace("$","").replace(",","").replace(" ","")
            thold = totalrow.split("$")[4].strip().replace("$","").replace(",","").replace(" ","")
        except IndexError:
            totalrow = ""
            tbal = ""
            tdue = ""
            tpaid = ""
            thold = ""
        fees = pd.Series(actives,dtype=str)
        fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
        srows = fees.map(lambda x: x.strip().split(" "))
        drows = fees_noalpha.map(lambda x: x.replace(",","").split("$"))
        coderows = srows.map(lambda x: str(x[5]).strip() if len(x)>5 else "")
        payorrows = srows.map(lambda x: str(x[6]).strip() if len(x)>6 else "")
        amtduerows = drows.map(lambda x: str(x[1]).strip() if len(x)>1 else "")
        amtpaidrows = drows.map(lambda x: str(x[2]).strip() if len(x)>2 else "")
        balancerows = drows.map(lambda x: str(x[-1]).strip() if len(x)>5 else "")
        amtholdrows = drows.map(lambda x: str(x[3]).strip() if len(x)>5 else "")
        amtholdrows = amtholdrows.map(lambda x: x.split(" ")[0].strip() if " " in x else x)
        istotalrow = fees.map(lambda x: False if bool(re.search(r'(ACTIVE)',x)) else True)
        adminfeerows = fees.map(lambda x: x.strip()[7].strip() if 'N' else '')


        feesheet = pd.DataFrame({
            'CaseNumber': getCaseNumber(text),
            'Total': '',
            'FeeStatus': 'ACTIVE',
            'AdminFee': adminfeerows.tolist(),
            'Code': coderows.tolist(),
            'Payor': payorrows.tolist(),
            'AmtDue': amtduerows.tolist(),
            'AmtPaid': amtpaidrows.tolist(),
            'Balance': balancerows.tolist(),
            'AmtHold': amtholdrows.tolist()
        })

        totalrdf = {
            'CaseNumber': getCaseNumber(text),
            'Total': 'TOTAL',
            'FeeStatus': '',
            'AdminFee': '',
            'Code': '',
            'Payor': '',
            'AmtDue': tdue,
            'AmtPaid': tpaid,
            'Balance': tbal,
            'AmtHold': thold
        }

        feesheet = feesheet.dropna()
        feesheet = feesheet.append(totalrdf, ignore_index=True)
        feesheet['Code'] = feesheet['Code'].astype("category")
        feesheet['Payor'] = feesheet['Payor'].astype("category")

        try:
            d999 = feesheet[feesheet['Code']=='D999']['Balance']
        except (TypeError, IndexError):
            d999 = ""

        owe_codes = " ".join(feesheet['Code'][feesheet.Balance.str.len() > 0])
        codes = " ".join(feesheet['Code'])
        allrows = actives
        allrows.append(totalrow)
        allrowstr = "\n".join(allrows)

        feesheet = feesheet[['CaseNumber', 'FeeStatus', 'AdminFee', 'Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]

        return [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]
def getFeeCodes(text: str):
    """Return fee codes from case text"""
    return FeeSheet(text)[4]
def getFeeCodesOwed(text: str):
    """Return fee codes with positive balance owed from case text"""
    return FeeSheet(text)[3]
def getTotals(text: str):
    """Return totals from case text -> List: [totalrow,tdue,tpaid,tdue,thold]"""
    try:
        trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
        totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
        if len(totalrow.split("$")[-1])>5:
            totalrow = totalrow.split(" . ")[0]
        tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
        tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","")
        tpaid = totalrow.split("$")[2].strip().replace("$","").replace(",","").replace(" ","")
        thold = totalrow.split("$")[4].strip().replace("$","").replace(",","").replace(" ","")
        tbal = pd.to_numeric(tbal, 'coerce')
        tdue = pd.to_numeric(tdue, 'coerce')
        tpaid = pd.to_numeric(tpaid, 'coerce')
        thold = pd.to_numeric(thold, 'coerce')

    except IndexError:
        totalrow = 0
        tbal = 0
        tdue = 0
        tpaid = 0
        thold = 0
    return [totalrow,tdue,tpaid,tdue,thold]
def getTotalBalance(text: str):
    """Return total balance from case text"""
    try:
        trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
        totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
        if len(totalrow.split("$")[-1])>5:
            totalrow = totalrow.split(" . ")[0]
        tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
    except:
        tbal = ""
    return str(tbal)
def getPaymentToRestore(text: str):
    """
    Return (total balance - total d999) from case text -> str
    Does not mask misc balances!
    """
    totalrow = "".join(re.findall(r'(Total.*\$.+\$.+\$.+)', str(text), re.MULTILINE)) if bool(re.search(r'(Total.*\$.*)', str(text), re.MULTILINE)) else "0"
    try:
        tbalance = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","").strip()
        try:
            tbal = pd.Series([tbalance]).astype(float)
        except ValueError:
            tbal = 0.0
    except (IndexError, TypeError):
        tbal = 0.0
    try:
        d999raw = re.search(r'(ACTIVE.*?D999\$.*)', str(text), re.MULTILINE).group() if bool(re.search(r'(ACTIVE.*?D999\$.*)', str(text), re.MULTILINE)) else "0"
        d999 = pd.Series([d999raw]).astype(float)
    except (IndexError, TypeError):
        d999 = 0.0
    t_out = pd.Series(tbal - d999).astype(float).values[0]
    return str(t_out)
def getBalanceByCode(text: str, code: str):
    """
    Return balance by code from case text -> str
    """
    actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
    fees = pd.Series(actives,dtype=str)
    fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
    srows = fees.map(lambda x: x.strip().split(" "))
    drows = fees_noalpha.map(lambda x: x.replace(",","").split("$"))
    coderows = srows.map(lambda x: str(x[5]).strip() if len(x)>5 else "")
    balancerows = drows.map(lambda x: str(x[-1]).strip() if len(x)>5 else "")
    codemap = pd.DataFrame({
        'Code': coderows,
        'Balance': balancerows
    })
    matches = codemap[codemap.Code==code].Balance
    return str(matches.sum())
def getAmtDueByCode(text: str, code: str):
    """
    Return total amt due from case text -> str
    """
    actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
    fees = pd.Series(actives,dtype=str)
    fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
    srows = fees.map(lambda x: x.strip().split(" "))
    drows = fees_noalpha.map(lambda x: x.replace(",","").split("$"))
    coderows = srows.map(lambda x: str(x[5]).strip() if len(x)>5 else "")
    payorrows = srows.map(lambda x: str(x[6]).strip() if len(x)>6 else "")
    amtduerows = drows.map(lambda x: str(x[1]).strip() if len(x)>1 else "")

    codemap = pd.DataFrame({
        'Code': coderows,
        'Payor': payorrows,
        'AmtDue': amtduerows
    })

    codemap.AmtDue = codemap.AmtDue.map(lambda x: pd.to_numeric(x,'coerce'))

    due = codemap.AmtDue[codemap.Code == code]
    return str(due)
def getAmtPaidByCode(text: str, code: str):
    """
    Return total amt paid from case text -> str
    """
    actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
    fees = pd.Series(actives,dtype=str)
    fees_noalpha = fees.map(lambda x: re.sub(r'[^0-9|\.|\s|\$]', "", x))
    srows = fees.map(lambda x: x.strip().split(" "))
    drows = fees_noalpha.map(lambda x: x.replace(",","").split("$"))
    coderows = srows.map(lambda x: str(x[5]).strip() if len(x)>5 else "")
    payorrows = srows.map(lambda x: str(x[6]).strip() if len(x)>6 else "")
    amtpaidrows = drows.map(lambda x: str(x[2]).strip() if len(x)>2 else "")

    codemap = pd.DataFrame({
        'Code': coderows,
        'Payor': payorrows,
        'AmtPaid': amtpaidrows
    })

    codemap.AmtPaid = codemap.AmtPaid.map(lambda x: pd.to_numeric(x,'coerce'))

    paid = codemap.AmtPaid[codemap.Code == code]
    return str(paid)
def getCharges(text: str):
    """
    Returns charges summary from case text -> List: [convictions, dcharges, fcharges, cerv_convictions, pardon_convictions, perm_convictions, conviction_ct, charge_ct, cerv_ct, pardon_ct, perm_ct, conv_cerv_ct, conv_pardon_ct, conv_perm_ct, charge_codes, conv_codes, allcharge, charges]
    """
    cnum = getCaseNumber(text)
    rc = re.findall(r'(\d{3}\s{1}.{1,1000}?.{3}-.{3}-.{3}.{10,75})', text, re.MULTILINE)
    unclean = pd.DataFrame({'Raw':rc})
    unclean['FailTimeTest'] = unclean['Raw'].map(lambda x: bool(re.search(r'([0-9]{1}\:{1}[0-9]{2})', x)))
    unclean['FailNumTest'] = unclean['Raw'].map(lambda x: False if bool(re.search(r'([0-9]{3}\s{1}.{4}\s{1})',x)) else True)
    unclean['Fail'] = unclean.index.map(lambda x: unclean['FailTimeTest'][x] == True or unclean['FailNumTest'][x]== True)
    passed = pd.Series(unclean[unclean['Fail']==False]['Raw'].dropna().explode().tolist())
    passed = passed.explode()
    passed = passed.dropna()
    passed = pd.Series(passed.tolist())
    passed = passed.map(lambda x: re.sub(r'(\s+[0-1]{1}$)', '',x))
    passed = passed.map(lambda x: re.sub(r'([©|\w]{1}[a-z]+)', ' ',x))
    passed = passed.map(lambda x: re.sub(r'(0\.0[0\s]\s+$)', ' ',x))
    passed = passed.explode()
    c = passed.dropna().tolist()
    cind = range(0, len(c))
    charges = pd.DataFrame({ 'Charges': c,'parentheses':'','decimals':''},index=cind)
    charges['Charges'] = charges['Charges'].map(lambda x: re.sub(r'(\$|\:|©.+)','',x,re.MULTILINE))
    charges['CaseNumber'] = charges.index.map(lambda x: cnum)
    split_charges = charges['Charges'].map(lambda x: x.split(" "))
    charges['Num'] = split_charges.map(lambda x: x[0].strip())
    charges['Code'] = split_charges.map(lambda x: x[1].strip()[0:4])
    charges['Felony'] = charges['Charges'].map(lambda x: bool(re.search(r'FELONY',x)))
    charges['Conviction'] = charges['Charges'].map(lambda x: bool(re.search(r'GUILTY|CONVICTED',x)))
    charges['VRRexception'] = charges['Charges'].map(lambda x: bool(re.search(r'(A ATT|ATTEMPT|S SOLICIT|CONSP)',x)))
    charges['CERVCode'] = charges['Code'].map(lambda x: bool(re.search(r'(OSUA|EGUA|MAN1|MAN2|MANS|ASS1|ASS2|KID1|KID2|HUT1|HUT2|BUR1|BUR2|TOP1|TOP2|TPCS|TPCD|TPC1|TET2|TOD2|ROB1|ROB2|ROB3|FOR1|FOR2|FR2D|MIOB|TRAK|TRAG|VDRU|VDRY|TRAO|TRFT|TRMA|TROP|CHAB|WABC|ACHA|ACAL)', x)))
    charges['PardonCode'] = charges['Code'].map(lambda x: bool(re.search(r'(RAP1|RAP2|SOD1|SOD2|STSA|SXA1|SXA2|ECHI|SX12|CSSC|FTCS|MURD|MRDI|MURR|FMUR|PMIO|POBM|MIPR|POMA|INCE)', x)))
    charges['PermanentCode'] = charges['Code'].map(lambda x: bool(re.search(r'(CM\d\d|CMUR)', x)))
    charges['CERV'] = charges.index.map(lambda x: charges['CERVCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
    charges['Pardon'] = charges.index.map(lambda x: charges['PardonCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
    charges['Permanent'] = charges.index.map(lambda x: charges['PermanentCode'][x] == True and charges['VRRexception'][x] == False and charges['Felony'][x] == True)
    charges['Disposition'] = charges['Charges'].map(lambda x: bool(re.search(r'\d{2}/\d{2}/\d{4}', x)))
    charges['CourtActionDate'] = charges['Charges'].map(lambda x: re.search(r'(\d{2}/\d{2}/\d{4})', x).group() if bool(re.search(r'(\d{2}/\d{2}/\d{4})', x)) else "")
    charges['CourtAction'] = charges['Charges'].map(lambda x: re.search(r'(BOUND|GUILTY PLEA|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x).group() if bool(re.search(r'(BOUND|GUILTY PLEA|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x)) else "")
    try:
        charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([^a-z]{1,2}?.{1}-[^\s]{3}-[^\s]{3})', x).group())
    except (AttributeError, IndexError):
        pass
        try:
            charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([0-9]{1,2}.{1}-.{3}-.{3})',x).group()) # TEST
        except (AttributeError, IndexError):
            charges['Cite'] = ""
    charges['Cite'] = charges['Cite'].astype(str)
    try:
        charges['decimals'] = charges['Charges'].map(lambda x: re.search(r'(\.[0-9])', x).group())
        charges['Cite'] = charges['Cite'] + charges['decimals']
    except (AttributeError, IndexError):
        charges['Cite'] = charges['Cite']
    try:
        charges['parentheses'] = charges['Charges'].map(lambda x: re.search(r'(\([A-Z]\))', x).group())
        charges['Cite'] = charges['Cite'] + charges['parentheses']
        charges['Cite'] = charges['Cite'].map(lambda x: x[1:-1] if bool(x[0]=="R" or x[0]=="Y" or x[0]=="C") else x)
    except (AttributeError, IndexError):
        pass
    charges['TypeDescription'] = charges['Charges'].map(lambda x: re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x).group() if bool(re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x)) else "")
    charges['Category'] = charges['Charges'].map(lambda x: re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x).group() if bool(re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x)) else "")
    charges['Charges'] = charges['Charges'].map(lambda x: x.replace("SentencesSentence","").replace("Sentence","").strip())
    charges.drop(columns=['PardonCode','PermanentCode','CERVCode','VRRexception','parentheses','decimals'], inplace=True)
    ch_Series = charges['Charges']
    noNumCode = ch_Series.str.slice(8)
    noNumCode = noNumCode.str.strip()
    noDatesEither = noNumCode.str.replace("\d{2}/\d{2}/\d{4}",'', regex=True)
    noWeirdColons = noDatesEither.str.replace("\:.+","", regex=True)
    descSplit = noWeirdColons.str.split(".{3}-.{3}-.{3}", regex=True)
    descOne = descSplit.map(lambda x: x[0])
    descTwo = descSplit.map(lambda x: x[1])

    descs = pd.DataFrame({
        'One': descOne,
        'Two': descTwo
    })

    descs['TestOne'] = descs['One'].str.replace("TRAFFIC","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("FELONY","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("PROPERTY","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("MISDEMEANOR","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("PERSONAL","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("FELONY","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("DRUG","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("GUILTY PLEA","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("DISMISSED","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("NOL PROSS","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("CONVICTED","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.replace("WAIVED TO GJ","").astype(str)
    descs['TestOne'] = descs['TestOne'].str.strip()

    descs['TestTwo'] = descs['Two'].str.replace("TRAFFIC","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("FELONY","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("PROPERTY","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("MISDEMEANOR","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("PERSONAL","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("FELONY","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.replace("DRUG","").astype(str)
    descs['TestTwo'] = descs['TestTwo'].str.strip()

    descs['Winner'] = descs['TestOne'].str.len() - descs['TestTwo'].str.len()

    descs['DoneWon'] = descs['One'].astype(str)
    descs['DoneWon'][descs['Winner']<0] = descs['Two'][descs['Winner']<0]
    descs['DoneWon'] = descs['DoneWon'].str.replace("(©.*)","",regex=True)
    descs['DoneWon'] = descs['DoneWon'].str.replace(":","")
    descs['DoneWon'] = descs['DoneWon'].str.strip()

    charges['Description'] = descs['DoneWon']

    charges['Category'] = charges['Category'].astype("category")
    charges['TypeDescription'] = charges['TypeDescription'].astype("category")
    charges['Code'] = charges['Code'].astype("category")
    charges['CourtAction'] = charges['CourtAction'].astype("category")

    # counts
    conviction_ct = charges[charges.Conviction == True].shape[0]
    charge_ct = charges.shape[0]
    cerv_ct = charges[charges.CERV == True].shape[0]
    pardon_ct = charges[charges.Pardon == True].shape[0]
    perm_ct = charges[charges.Permanent == True].shape[0]
    conv_cerv_ct = charges[charges.CERV == True][charges.Conviction == True].shape[0]
    conv_pardon_ct = charges[charges.Pardon == True][charges.Conviction == True].shape[0]
    conv_perm_ct = charges[charges.Permanent == True][charges.Conviction == True].shape[0]

    # summary strings
    convictions = "; ".join(charges[charges.Conviction == True]['Charges'].tolist())
    conv_codes = " ".join(charges[charges.Conviction == True]['Code'].tolist())
    charge_codes = " ".join(charges[charges.Disposition == True]['Code'].tolist())
    dcharges = "; ".join(charges[charges.Disposition == True]['Charges'].tolist())
    fcharges = "; ".join(charges[charges.Disposition == False]['Charges'].tolist())
    cerv_convictions = "; ".join(charges[charges.CERV == True][charges.Conviction == True]['Charges'].tolist())
    pardon_convictions = "; ".join(charges[charges.Pardon == True][charges.Conviction == True]['Charges'].tolist())
    perm_convictions = "; ".join(charges[charges.Permanent == True][charges.Conviction == True]['Charges'].tolist())

    allcharge = "; ".join(charges['Charges'])
    if charges.shape[0] == 0:
        charges = np.nan

    return [convictions, dcharges, fcharges, cerv_convictions, pardon_convictions, perm_convictions, conviction_ct, charge_ct, cerv_ct, pardon_ct, perm_ct, conv_cerv_ct, conv_pardon_ct, conv_perm_ct, charge_codes, conv_codes, allcharge, charges]
def getConvictions(text):
    """
    Return convictions as string from case text
    """
    return getCharges(text)[0]
def getDispositionCharges(text):
    """
    Return disposition charges as string from case text
    """
    return getCharges(text)[1]
def getFilingCharges(text):
    """
    Return filing charges as string from case text
    """
    return getCharges(text)[2]
def getCERVConvictions(text):
    """
    Return CERV convictions as string from case text
    """
    return getCharges(text)[3]
def getPardonDQConvictions(text):
    """
    Return pardon-to-vote charges as string from case text
    """
    return getCharges(text)[4]
def getPermanentDQConvictions(text):
    """
    Return permanent no vote charges as string from case text
    """
    return getCharges(text)[5]
def getConvictionCount(text):
    """
    Return convictions count from case text
    """
    return getCharges(text)[6]
def getChargeCount(text):
    """
    Return charges count from case text
    """
    return getCharges(text)[7]
def getCERVChargeCount(text):
    """
    Return CERV charges count from case text
    """
    return getCharges(text)[8]
def getPardonDQCount(text):
    """
    Return pardon-to-vote charges count from case text
    """
    return getCharges(text)[9]
def getPermanentDQChargeCount(text):
    """
    Return permanent no vote charges count from case text
    """
    return getCharges(text)[10]
def getCERVConvictionCount(text):
    """
    Return CERV convictions count from case text
    """
    return getCharges(text)[11]
def getPardonDQConvictionCount(text):
    """
    Return pardon-to-vote convictions count from case text
    """
    return getCharges(text)[12]
def getPermanentDQConvictionCount(text):
    """
    Return permanent no vote convictions count from case text
    """
    return getCharges(text)[13]
def getChargeCodes(text):
    """
    Return charge codes as string from case text
    """
    return getCharges(text)[14]
def getConvictionCodes(text):
    """
    Return convictions codes as string from case text
    """
    return getCharges(text)[15]
def getChargesString(text):
    """
    Return charges as string from case text
    """
    return getCharges(text)[16]

############
##  LOGS  ##
############

def echo_conf(input_path,make,output_path,overwrite,no_write,dedupe,launch,warn,no_prompt, compress):
    d = click.style(f"""\n* Successfully configured!\n""",fg='green', bold=True)
    e = click.style(f"""INPUT: {input_path}\n{'TABLE' if make == "multiexport" or make == "singletable" else 'ARCHIVE'}: {output_path}\n""",fg='white',bold=True)
    f = click.style(f"""{"OVERWRITE is enabled. Alacorder will overwrite existing files at output path! " if overwrite else ''}{"NO-WRITE is enabled. Alacorder will NOT export outputs. " if no_write else ''}{"REMOVE DUPLICATES is enabled. At time of export, all duplicate cases will be removed from output. " if dedupe else ''}{"LAUNCH is enabled. Upon completion, Alacorder will attempt to launch exported file in default viewing application. " if launch and make != "archive" else ''}{"WARN is enabled. All warnings from pandas and other modules will print to console. " if warn else ''}{"NO_PROMPT is enabled. All user confirmation prompts will be suppressed as if set to default by user." if no_prompt else ''}{"COMPRESS is enabled. Alacorder will try to compress output file." if compress == True and make != "archive" else ''}""".strip(), italic=True, fg='white')
    return d + e + f
def complete(conf, *outputs):
    if not conf.DEBUG:
        sys.tracebacklimit = 0
        warnings.filterwarnings('ignore')
    if conf.LOG and len(outputs)>0:
        click.secho(outputs)
    if conf.LOG:
        click.secho("\n\n* Task completed!\n\n",bold=True,fg='green')
def logdebug(conf, *msg):
    if conf['DEBUG'] == True:
        click.secho(msg)
def echo(conf, *msg):
    if conf['LOG']==True:
        click.secho(msg)
def echo_red(text, echo=True):
    if echo:
        click.echo(click.style(text,fg='bright_red',bold=True),nl=True)
        return click.style(text,fg='bright_red',bold=True)
    else:
        return click.style(text,fg='bright_red',bold=True)
def echo_yellow(text, echo=True):
    if echo:
        click.echo(click.style(text,fg='bright_yellow',bold=True),nl=True)
        return click.style(text,fg='bright_yellow',bold=True)
    else:
        return click.style(text,fg='bright_yellow',bold=True)
def echo_green(text, echo=True):
    if echo:
        click.echo(click.style(text,fg='bright_green',bold=True),nl=True)
        return click.style(text,fg='bright_green',bold=True)
    else:
        return click.style(text,fg='bright_green',bold=True)
