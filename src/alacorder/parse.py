
# parse 74
# Sam Robson

import os
import sys
import glob
import re
import math
import numexpr
import xarray
import bottleneck
import numpy as np
import xlrd
import openpyxl
import datetime
import pandas as pd
import time
import warnings
import click
import inspect
from alacorder import get 
from alacorder import write 
from alacorder import config 
from alacorder import logs
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass
def table(conf, table=""):
    """
    Route config to parse...() function corresponding to table attr 
    """
    a = []
    if conf.MAKE == "multiexport":
        a = cases(conf)
    if table == "cases":
        a = caseinfo(conf)
    if table == "fees":
        a = fees(conf)
    if table == "charges":
        a = charges(conf)
    if table == "disposition":
        a = charges(conf)
    if table == "filing":
        a = charges(conf)
    return a

def fees(conf):
    """
    Return fee sheets with case number as DataFrame from batch
    fees = pd.DataFrame({'CaseNumber': '', 
        'Code': '', 'Payor': '', 'AmtDue': '', 
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''})
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
    from_archive = True if conf['IS_FULL_TEXT'] else False
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")
    outputs = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 
        'Code': '', 'Payor': '', 'AmtDue': '', 
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
    if not conf['NO_BATCH']:
        batches = config.batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    batchcount = len(batches)
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = c.map(lambda x: get.PDFText(x))

            b['caseinfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['caseinfoOutputs'].map(lambda x: x[0])
            try:
                b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(str(b.loc[x].AllPagesText)))
                feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
            except (AttributeError,IndexError):
                pass

            feesheet = feesheet.dropna() # drop empty 
            fees =fees.dropna()
            feesheet = feesheet.tolist() # convert to list -> [df, df, df]
            try:
                feesheet = pd.concat(feesheet,axis=0,ignore_index=True) # add all dfs in batch -> df
            except ValueError:
                pass
            fees = fees.append(feesheet, ignore_index=True) 
            fees = fees[['CaseNumber', 'FeeStatus', 'AdminFee', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
            fees.fillna('',inplace=True)
            fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))
    if not no_write:
        write.now(conf, fees)
    logs.complete(conf, start_time, fees)
    return fees
def charges(conf):
    """
    Return charges with case number as DataFrame from batch
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''}) 
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
    from_archive = True if conf['IS_FULL_TEXT'] else False

    if warn == False:
        warnings.filterwarnings("ignore")

    if not conf['NO_BATCH']:
        batches = config.batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    start_time = time.time()
    outputs = pd.DataFrame()
    charges = pd.DataFrame()
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))

            b['caseinfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['caseinfoOutputs'].map(lambda x: x[0])
            b['chargesOutputs'] = b.index.map(lambda x: get.Charges(str(b.loc[x].AllPagesText)))

            
            chargetabs = b['chargesOutputs'].map(lambda x: x[17])
            chargetabs = chargetabs.dropna()
            chargetabs = chargetabs.tolist()
            chargetabs = pd.concat(chargetabs)
            charges = charges.append(chargetabs)
            charges.fillna('',inplace=True)

            if table == "filing":
                is_disp = charges['Disposition']
                is_filing = is_disp.map(lambda x: False if x == True else True)
                charges = charges[is_filing]
                charges.drop(columns=['CourtAction','CourtActionDate'],inplace=True)

            if table == "disposition":
                is_disp = charges.Disposition.map(lambda x: True if x == True else False)
                charges = charges[is_disp]
        if not no_write:
            write.now(conf, charges)

    logs.complete(conf, start_time, charges)
    return charges
def cases(conf):
    """
    Return [cases, fees, charges] tables as List of DataFrames from batch
    See API docs for table specific outputs
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
    path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
    appendtable = conf['APPEND']
    old_table = conf['OLD_ARCHIVE']
    from_archive = True if conf['IS_FULL_TEXT'] else False
    start_time = time.time()
    arc_ext = conf['OUTPUT_EXT']
    cases = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 'FeeStatus': '','AdminFee': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
    arch = pd.DataFrame({'Path':'','AllPagesText':'','Timestamp':''},index=[0])
    if not conf['NO_BATCH']:
        batches = config.batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
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
                b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))
            b['caseinfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['caseinfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['caseinfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['caseinfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['caseinfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['caseinfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['caseinfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['caseinfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['caseinfoOutputs'].map(lambda x: x[7])
            b['chargesOutputs'] = b.index.map(lambda x: get.Charges(str(b.loc[x].AllPagesText)))
            b['Convictions'] = b['chargesOutputs'].map(lambda x: x[0])
            b['Dispositioncharges'] = b['chargesOutputs'].map(lambda x: x[1])
            b['Filingcharges'] = b['chargesOutputs'].map(lambda x: x[2])
            b['CERVConvictions'] = b['chargesOutputs'].map(lambda x: x[3])
            b['PardonConvictions'] = b['chargesOutputs'].map(lambda x: x[4])
            b['PermanentConvictions'] = b['chargesOutputs'].map(lambda x: x[5])
            b['ConvictionCount'] = b['chargesOutputs'].map(lambda x: x[6])
            b['ChargeCount'] = b['chargesOutputs'].map(lambda x: x[7])
            b['CERVChargeCount'] = b['chargesOutputs'].map(lambda x: x[8])
            b['PardonChargeCount'] = b['chargesOutputs'].map(lambda x: x[9])
            b['PermanentChargeCount'] = b['chargesOutputs'].map(lambda x: x[10])
            b['CERVConvictionCount'] = b['chargesOutputs'].map(lambda x: x[11])
            b['PardonConvictionCount'] = b['chargesOutputs'].map(lambda x: x[12])
            b['PermanentConvictionCount'] = b['chargesOutputs'].map(lambda x: x[13])
            b['ChargeCodes'] = b['chargesOutputs'].map(lambda x: x[14])
            b['ConvictionCodes'] = b['chargesOutputs'].map(lambda x: x[15])
            b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(str(b.loc[x].AllPagesText)))
            b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
            b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
            b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
            b['FeeCodesOwed'] = b['FeeOutputs'].map(lambda x: x[3])
            b['FeeCodes'] = b['FeeOutputs'].map(lambda x: x[4])
            b['FeeSheet'] = b['FeeOutputs'].map(lambda x: x[5])


            feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
            feesheet = feesheet.dropna() 
            fees = fees.dropna()
            feesheet = feesheet.tolist() # -> [df, df, df]
            
            try:
                feesheet = pd.concat(feesheet,axis=0,ignore_index=True) #  -> batch df
            except ValueError:
                pass
            try:
                fees = fees.append(feesheet, ignore_index=True) # -> all fees df
            except ValueError:
                pass

            chargetabs = b['chargesOutputs'].map(lambda x: x[17])
            chargetabs = chargetabs.dropna()
            charges = charges.dropna()
            chargetabs = chargetabs.tolist()
            
            try:
                chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
            except ValueError:
                pass
            try:
                charges = charges.append(chargetabs,ignore_index=True)
            except ValueError:
                pass
            
            fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))

            b['chargestable'] = b['chargesOutputs'].map(lambda x: x[-1])
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
                    ar = pd.DataFrame({
                        'Path': pd.Series(queue),
                        'AllPagesText': b['AllPagesText'],
                        'Timestamp': timestamp
                        },index=range(0,pd.Series(queue).shape[0]))
                    arch = pd.concat([arch, ar],ignore_index=True)
                    arch.fillna('',inplace=True)
                    arch.dropna(inplace=True)
                    arch.to_pickle(archive_out,compression="xz")

            b.drop(columns=['AllPagesText','caseinfoOutputs','chargesOutputs','FeeOutputs','chargestable','FeeSheet'],inplace=True)

            if dedupe == True:
                outputs.drop_duplicates(keep='first',inplace=True)
            
            b.fillna('',inplace=True)
            charges.fillna('',inplace=True)
            fees.fillna('',inplace=True)
            cases.fillna('',inplace=True)
            newcases = [cases, b]
            cases = cases.append(newcases, ignore_index=True)
            # charges = charges[['CaseNumber', 'Num', 'Code', 'Description', 'Cite', 'CourtAction', 'CourtActionDate', 'Category', 'TypeDescription', 'Disposition', 'Permanent', 'Pardon', 'CERV','Conviction']]
            # fees = fees[['CaseNumber', 'FeeStatus', 'AdminFee','Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
            
            # write     
            if appendtable:
                if type(old_table) == list:
                    appcase = [cases, old_table[0]]
                    appcharge = [charges, old_table[1]]
                    appfees = [fees, old_table[2]]
                    cases = pd.concat(appcase)
                    fees = pd.concat(appfees)
                    charges = pd.concat(appcharge)
                else:
                    if len(old_table.columns) == 29 or len(old_table.columns) == 30:
                        appcase = [cases, old_table]
                        cases = pd.concat(appcase)
                    elif len(old_table.columns) == 10 or len(old_table.columns) == 11:
                        appcharge = [charges, old_table]
                    elif len(old_table.columns) == 14 or len(old_table.columns) == 15:
                        appfees = [fees, old_table]
                    else:
                        appcase = [cases, old_table]
                        cases = pd.concat(appcase)


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
                                try:
                                    if not appendtable:
                                        os.remove(path_out)
                                except:
                                    pass
                                cases.to_json(os.path.splitext(path_out)[0] + "-cases.json.zip", orient='table')
                                fees.to_json(os.path.splitext(path_out)[0] + "-fees.json.zip",orient='table')
                                charges.to_json(os.path.splitext(path_out)[0] + "-charges.json.zip",orient='table')
                                click.echo(f"Fallback export to {os.path.splitext(path_out)[0]}-cases.json.zip due to Excel engine failure, usually caused by exceeding max row limit for .xls/.xlsx files!")

                                # ADD LOG
                            except (ImportError, FileNotFoundError, IndexError, ValueError):
                                click.echo("Failed to export!")
                            
                elif out_ext == ".json":
                    cases.to_json(path_out,orient='table')
                elif out_ext == ".csv":
                    cases.to_csv(path_out,escapechar='\\')
                elif out_ext == ".md":
                    cases.to_markdown(path_out)
                elif out_ext == ".txt":
                    cases.to_string(path_out)
                elif out_ext == ".dta":
                    cases.to_stata(path_out)
                else:
                    pd.Series([cases, fees, charges]).to_string(path_out)
                try:
                    if dedupe == True and outputs.shape[0] < queue.shape[0]:
                        click.echo(f"Identified and removed {outputs.shape[0]-queue.shape[0]} from queue.")
                except:
                    pass

        logs.complete(conf, start_time, pd.Series([cases, fees, charges]).to_string())
        return [cases, fees, charges]

def caseinfo(conf):
    """
    Return case information with case number as DataFrame from batch
    List: ['CaseNumber','Name','Alias','DOB','Race','Sex','Address','Phone','Totals','TotalAmtDue','TotalAmtPaid','TotalBalance','TotalAmtHold','PaymentToRestore','ConvictionCodes','ChargeCodes','FeeCodes','FeeCodesOwed','Dispositioncharges','Filingcharges','CERVConvictions','PardonDQConvictions','PermanentDQConviction','TotalAmtDue','TotalAmtPaid','TotalBalance','TotalAmtHold','PaymentToRestore','ConvictionCodes','ChargeCodes','FeeCodes','FeeCodesOwed','Dispositioncharges','Filingcharges','CERVConvictions','PardonDQConvictions','PermanentDQConvictions']
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
    path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT'] else False

    cases = pd.DataFrame()

    if not conf['NO_BATCH']:
        batches = config.batcher(conf)
    else:
        batches = np.array_split(queue, 1)
    batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    
    

    if warn == False:
        warnings.filterwarnings("ignore")
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            b = pd.DataFrame()
            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = pd.Series(c).map(lambda x: get.PDFText(x))

            b['caseinfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['caseinfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['caseinfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['caseinfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['caseinfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['caseinfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['caseinfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['caseinfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['caseinfoOutputs'].map(lambda x: x[7])
            b['Totals'] = b['AllPagesText'].map(lambda x: get.Totals(x))
            b['TotalAmtDue'] = b['Totals'].map(lambda x: x[1])
            b['TotalAmtPaid'] = b['Totals'].map(lambda x: x[2])
            b['TotalBalance'] = b['Totals'].map(lambda x: x[3])
            b['TotalAmtHold'] = b['Totals'].map(lambda x: x[4])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
            b['PaymentToRestore'][b['CERVConvictionCount'] == 0] = pd.NaT
            b['ConvictionCodes'] = b['AllPagesText'].map(lambda x: get.ConvictionCodes(x))
            b['ChargeCodes'] = b['AllPagesText'].map(lambda x: get.ChargeCodes(x))
            b['FeeCodes'] = b['AllPagesText'].map(lambda x: get.FeeCodes(x))
            b['FeeCodesOwed'] = b['AllPagesText'].map(lambda x: get.FeeCodesOwed(x))
            b['Dispositioncharges'] = b['AllPagesText'].map(lambda x: get.Dispositioncharges(x))
            b['Filingcharges'] = b['AllPagesText'].map(lambda x: get.Filingcharges(x))
            b['CERVConvictions'] = b['AllPagesText'].map(lambda x: get.CERVConvictions(x))
            b['PardonDQConvictions'] = b['AllPagesText'].map(lambda x: get.PardonDQConvictions(x))
            b['PermanentDQConvictions'] = b['AllPagesText'].map(lambda x: get.PermanentDQConvictions(x))
            b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
            b.drop(columns=['AllPagesText','caseinfoOutputs','Totals'],inplace=True)
            b.fillna('',inplace=True)
            newcases = [cases, b]
            cases = cases.append(newcases, ignore_index=True)
            # write 
        if not no_write:
            write.now(conf, cases)
        logs.complete(conf, start_time, cases)
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
    path_out = conf['OUTPUT_PATH'] if conf.MAKE != "archive" else ''
    archive_out = conf['OUTPUT_PATH'] if conf.MAKE == "archive" else ''
    from_archive = True if conf['IS_FULL_TEXT']==True else False

    if warn == False:
        warnings.filterwarnings("ignore")
    if not conf['NO_BATCH']:
        batches = config.batcher(conf)
    else:
        batches = np.array_split(queue, 1)
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
                allpagestext = pd.Series(c).map(lambda x: get.PDFText(x))
            df_out['CaseNumber'] = allpagestext.map(lambda x: get.CaseNumber(x))
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

            if no_write == False and temp_no_write_tab == False and (i % 5 == 0 or i == len(batches) - 1):
                write.now(conf, df_out) # rem alac
    if not no_write:
        write.now(conf, df_out) # rem alac
    logs.complete(conf, start_time, df_out)
    return df_out
