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
import alacorder as alac
from alacorder import get
from alacorder import write
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass
def Table(conf, table=""):
    """
    Route config to parse...() function corresponding to table attr 
    """
    a = []
    if table == "all" or table == "all_cases" or table == "":
        a = Cases(conf)
    if table == "cases":
        a = CaseInfo(conf)
    if table == "fees":
        a = Fees(conf)
    if table == "charges":
        a = Charges(conf)
    if table == "disposition":
        a = Charges(conf)
    if table == "filing":
        a = Charges(conf)
    return a

def Fees(conf):
    """
    Return fee sheets with case number as DataFrame from batch
    fees = pd.DataFrame({'CaseNumber': '', 
        'Code': '', 'Payor': '', 'AmtDue': '', 
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''})
    """
    path_in = conf['input_path']
    path_out = conf['table_out']
    out_ext = conf['table_ext']
    max_cases = conf['count']
    queue = conf['queue']
    print_log = conf['log']
    warn = conf['warn']
    no_write = conf['no_write']
    dedupe = conf['dedupe']
    from_archive = False if conf['path_mode'] else True
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")
    outputs = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 
        'Code': '', 'Payor': '', 'AmtDue': '', 
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])

    batches = pd.Series(np.array_split(queue, (math.ceil(max_cases / 100)+1)))
    batchcount = batches.shape[0]
    batchsize = batches[0].shape[0]
    with click.progressbar(batches) as bar:
        for i, c in enumerate(bar):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                b['AllPagesText'] = c
            else:
                b['AllPagesText'] = c.map(lambda x: get.PDFText(x))

            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(b.loc[x].AllPagesText))

            feesheet = b['FeeOutputs'].map(lambda x: x[6]) 
            feesheet = feesheet.dropna() # drop empty 
            fees =fees.dropna()
            feesheet = feesheet.tolist() # convert to list -> [df, df, df]
            feesheet = pd.concat(feesheet,axis=0,ignore_index=True) # add all dfs in batch -> df
            fees = fees.append(feesheet, ignore_index=True) 
            fees = fees[['CaseNumber', 'Total', 'FeeStatus', 'AdminFee', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
            fees.fillna('',inplace=True)
            fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
            fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))
    if not no_write:
        write.now(conf, fees)
    log_complete(conf, start_time, fees)
    return fees
def Charges(conf):
    """
    Return charges with case number as DataFrame from batch
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''}) 
    """
    path_in = conf['input_path']
    path_out = conf['table_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    queue = conf['queue']
    warn = conf['warn']
    table = conf['table']
    no_write = conf['no_write']
    dedupe = conf['dedupe']
    from_archive = False if conf['path_mode'] else True

    if warn == False:
        warnings.filterwarnings("ignore")

    batches = pd.Series(np.array_split(queue, (math.ceil(max_cases / 1000)+1))) # batches of 1000, write every 500
    batchsize = max(batches.map(lambda x: x.shape[0]))

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

            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['ChargesOutputs'] = b.index.map(lambda x: get.Charges(b.loc[x].AllPagesText))

            
            chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
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

    log_complete(conf, start_time, charges)
    return charges
def Cases(conf):
    """
    ~~the whole shebang~~
    Return [cases, fees, charges] tables as List of DataFrames from batch
    See API docs for table specific outputs
    """
    path_in = conf['input_path']
    path_out = conf['table_out']
    archive_out = conf['archive_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    warn = conf['warn']
    queue = conf['queue']
    appendTable = conf['appendTable']
    old_table = conf['old_table']
    no_write = conf['no_write']
    dedupe = conf['dedupe']
    from_archive = False if conf['path_mode'] else True
    start_time = time.time()
    arc_ext = conf['archive_ext']
    cases = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 'FeeStatus': '','AdminFee': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
    arch = pd.DataFrame({'Path':'','AllPagesText':'','Timestamp':''},index=[0])
    batches = np.array_split(queue, (math.ceil(max_cases / 1000) + 1))
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
            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
            b['ChargesOutputs'] = b.index.map(lambda x: get.Charges(b.loc[x].AllPagesText))
            b['Convictions'] = b['ChargesOutputs'].map(lambda x: x[0])
            b['DispositionCharges'] = b['ChargesOutputs'].map(lambda x: x[1])
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
            b['FeeOutputs'] = b.index.map(lambda x: get.FeeSheet(b.loc[x].AllPagesText))
            b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
            b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
            b['PaymentToRestore'][b.CERVConvictionCount == 0] = pd.NaT
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

            chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
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
                    ar = pd.DataFrame({
                        'Path': pd.Series(queue),
                        'AllPagesText': b['AllPagesText'],
                        'Timestamp': timestamp
                        },index=range(0,pd.Series(queue).shape[0]))
                    arch = pd.concat([arch, ar],ignore_index=True)
                    arch.fillna('',inplace=True)
                    arch.dropna(inplace=True)
                    arch.to_pickle(archive_out,compression="xz")

            b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','ChargesTable','FeeSheet'],inplace=True)

            if dedupe == True:
                outputs.drop_duplicates(keep='first',inplace=True)
            
            b.fillna('',inplace=True)
            charges.fillna('',inplace=True)
            fees.fillna('',inplace=True)
            cases.fillna('',inplace=True)
            newcases = [cases, b]
            cases = cases.append(newcases, ignore_index=True)
            charges = charges[['CaseNumber', 'Num', 'Code', 'Description', 'Cite', 'CourtAction', 'CourtActionDate', 'Category', 'TypeDescription', 'Disposition', 'Permanent', 'Pardon', 'CERV','Conviction']]
            fees = fees[['CaseNumber', 'FeeStatus', 'AdminFee','Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]
            
            # write     
            if appendTable:
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
                        with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                    except (ImportError, IndexError, ValueError):
                        with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                elif out_ext == ".xlsx":
                    try:
                        with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                            cases.to_excel(writer, sheet_name="cases")
                            fees.to_excel(writer, sheet_name="fees")
                            charges.to_excel(writer, sheet_name="charges")
                    except (ImportError, IndexError, ValueError):
                        try:
                            with pd.ExcelWriter(path_out,engine="openpyxl") as writer:
                                cases.to_excel(writer, sheet_name="cases")
                                fees.to_excel(writer, sheet_name="fees")
                                charges.to_excel(writer, sheet_name="charges")
                        except (ImportError, FileNotFoundError, IndexError, ValueError):
                            try:
                                try:
                                    if not appendTable:
                                        os.remove(path_out)
                                except:
                                    pass
                                cases.to_csv(path_out + "-cases.csv",escapechar='\\')
                                fees.to_csv(path_out + "-fees.csv",escapechar='\\')
                                charges.to_csv(path_out + "-charges.csv",escapechar='\\')
                                log_console(conf, f"(Batch {i+1}) - WARNING: Exported to CSV due to XLSX engine failure")
                            except (ImportError, FileNotFoundError, IndexError, ValueError):
                                click.echo("Failed to export to CSV...")
                                pass
                elif out_ext == ".json":
                    cases.to_json(path_out)
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

        log_complete(conf, start_time, pd.Series([cases, fees, charges]).to_string())
        return [cases, fees, charges]

def CaseInfo(conf):
    """
    Return case information with case number as DataFrame from batch
    List: ['CaseNumber','Name','Alias','DOB','Race','Sex','Address','Phone','Totals','TotalAmtDue','TotalAmtPaid','TotalBalance','TotalAmtHold','PaymentToRestore','ConvictionCodes','ChargeCodes','FeeCodes','FeeCodesOwed','DispositionCharges','FilingCharges','CERVConvictions','PardonDQConvictions','PermanentDQConviction','TotalAmtDue','TotalAmtPaid','TotalBalance','TotalAmtHold','PaymentToRestore','ConvictionCodes','ChargeCodes','FeeCodes','FeeCodesOwed','DispositionCharges','FilingCharges','CERVConvictions','PardonDQConvictions','PermanentDQConvictions']
    """
    path_in = conf['input_path']
    path_out = conf['table_out']
    archive_out = conf['archive_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    warn = conf['warn']
    queue = conf['queue']
    appendTable = conf['appendTable']
    from_archive = False if conf['path_mode'] else True
    start_time = time.time()
    arc_ext = conf['archive_ext']
    no_write = conf['no_write']

    cases = pd.DataFrame()

    batches = pd.Series(np.array_split(queue, math.ceil(max_cases / 1000)))
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

            b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: get.CaseInfo(x))
            b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
            b['Name'] = b['CaseInfoOutputs'].map(lambda x: x[1])
            b['Alias'] = b['CaseInfoOutputs'].map(lambda x: x[2])
            b['DOB'] = b['CaseInfoOutputs'].map(lambda x: x[3])
            b['Race'] = b['CaseInfoOutputs'].map(lambda x: x[4])
            b['Sex'] = b['CaseInfoOutputs'].map(lambda x: x[5])
            b['Address'] = b['CaseInfoOutputs'].map(lambda x: x[6])
            b['Phone'] = b['CaseInfoOutputs'].map(lambda x: x[7])
            b['Totals'] = b['AllPagesText'].map(lambda x: get.Totals(x))
            b['TotalAmtDue'] = b['Totals'].map(lambda x: x[1])
            b['TotalAmtPaid'] = b['Totals'].map(lambda x: x[2])
            b['TotalBalance'] = b['Totals'].map(lambda x: x[3])
            b['TotalAmtHold'] = b['Totals'].map(lambda x: x[4])
            b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: get.PaymentToRestore(x))
            b['PaymentToRestore'][b.CERVConvictionCount == 0] = pd.NaT
            b['ConvictionCodes'] = b['AllPagesText'].map(lambda x: get.ConvictionCodes(x))
            b['ChargeCodes'] = b['AllPagesText'].map(lambda x: get.ChargeCodes(x))
            b['FeeCodes'] = b['AllPagesText'].map(lambda x: get.FeeCodes(x))
            b['FeeCodesOwed'] = b['AllPagesText'].map(lambda x: get.FeeCodesOwed(x))
            b['DispositionCharges'] = b['AllPagesText'].map(lambda x: get.DispositionCharges(x))
            b['FilingCharges'] = b['AllPagesText'].map(lambda x: get.FilingCharges(x))
            b['CERVConvictions'] = b['AllPagesText'].map(lambda x: get.CERVConvictions(x))
            b['PardonDQConvictions'] = b['AllPagesText'].map(lambda x: get.PardonDQConvictions(x))
            b['PermanentDQConvictions'] = b['AllPagesText'].map(lambda x: get.PermanentDQConvictions(x))
            b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
            b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
            b.drop(columns=['AllPagesText','CaseInfoOutputs','Totals'],inplace=True)
            b.fillna('',inplace=True)
            newcases = [cases, b]
            cases = cases.append(newcases, ignore_index=True)
            # write 
        if not no_write:
            write.now(conf, cases)
        log_complete(conf, start_time, cases)
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
    path_in = conf['input_path']
    path_out = conf['table_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    warn = conf['warn']
    queue = conf['queue']
    no_write = conf['no_write']
    from_archive = False if conf['path_mode'] else True
    if warn == False:
        warnings.filterwarnings("ignore")
    batches = pd.Series(np.array_split(queue, math.ceil(max_cases / 1000)))
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
    log_complete(conf, start_time, df_out)
    return df_out

## LOG
def log_complete(conf, start_time, output=None):
    path_in = conf['input_path']
    path_out = conf['table_out']
    arc_out = conf['archive_out']
    print_log = conf['log']
    max_cases = conf['count']
    launch = conf['launch']
    tablog = conf['tablog']
    completion_time = time.time()
    elapsed = completion_time - start_time
    cases_per_sec = max_cases/elapsed
    if tablog:
        click.secho(output)
    if launch:
        time.sleep(5)
        click.launch(path_out)
    if tablog or print_log:
        click.clear()
        click.echo(f'''\nTASK COMPLETED: Successfully processed {max_cases} cases. Last batch completed in {elapsed:.2f} seconds ({cases_per_sec:.2f} cases/sec)''')
def log_console(conf, *msg):
    path_in = conf['input_path']
    path_out = conf['table_out']
    arc_out = conf['archive_out']
    tablog = conf['tablog']
    max_cases = conf['count']
    click.clear()
    if tablog:
        click.echo(msg)
