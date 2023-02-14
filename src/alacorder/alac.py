# alac 71
# sam robson

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
import PyPDF2
from io import StringIO


pd.set_option("mode.chained_assignment",None)
pd.set_option("display.notebook_repr_html",True)
pd.set_option("display.width",None)

def getPDFText(path: str) -> str:
    text = ""
    pdf = PyPDF2.PdfReader(path)
    for pg in pdf.pages:
        text += pg.extract_text()
    return text

def getCaseNumber(text: str):
    try:
        county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
        case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip() 
        return county + "-" + case_num
    except (IndexError, AttributeError):
        return ""

def getName(text: str):
    name = ""
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    return name

def getDOB(text: str):
    dob = ""
    if bool(re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL)):
        dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
    return dob

def getFeeTotals(text: str):
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
    return [totalrow,tdue,tpaid,tdue,thold]

def getAddress(text: str):
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
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    race = racesex.group(1).strip()
    sex = racesex.group(2).strip()
    return race

def getSex(text: str):
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    sex = racesex.group(2).strip()
    return sex

def getName(text: str):
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    try:
        alias = re.search(r'(SSN)(.{5,75})(Alias)', text, re.MULTILINE).group(2).replace(":","").replace("Alias 1","").strip()
    except (IndexError, AttributeError):
        alias = ""
    if alias == "":
        return name
    else:
        return name + " / " + alias

def getCaseInfo(text: str):
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
 
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.{5,100})(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.{5,100})(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
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

def getDOB(text: str):
    try:
        dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
    except (IndexError, AttributeError):
        dob = ""
    return dob

def getFeeSheet(text: str, cnum: str):
    actives = re.findall(r'(ACTIVE.*\$.*)', str(text))
    if len(actives) == 0:
        return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    else:
        rind = range(0, len(actives)+1)
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
        adminfeerows = fees.map(lambda x: x.strip()[7].strip())
        

        feesheet = pd.DataFrame({
            'CaseNumber': cnum,
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
            'CaseNumber': cnum,
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

def getCharges(text: str, cnum: str):

    rc = re.findall(r'(\d{3}\s{1}.{1,100}?.{3}-.{3}-.{3}.{10,75})', text, re.MULTILINE)
    unclean = pd.DataFrame({'Raw':rc})
    unclean['FailTimeTest'] = unclean['Raw'].map(lambda x: bool(re.search(r'([0-9]{1}\:[0-9]{2})', x)))
    unclean['FailNumTest'] = unclean['Raw'].map(lambda x: False if bool(re.search(r'([0-9]{3}\s{1}.{4}\s{1})',x)) else True)
    unclean['Fail'] = unclean.index.map(lambda x: unclean['FailTimeTest'][x] == True or unclean['FailNumTest'][x]== True)
    passed = pd.Series(unclean[unclean['Fail']==False]['Raw'].dropna().explode().tolist())
    passed = passed.explode()
    passed = passed.dropna()
    passed = pd.Series(passed.tolist())
    passed = passed.map(lambda x: re.sub(r'(\s+[0-1]{1}$)', '',x))
    passed = passed.map(lambda x: re.sub(r'([©|\w]{1}[a-z]+)', ' ',x))
    passed = passed.explode()
    c = passed.dropna().tolist()
    cind = range(0, len(c))
    charges = pd.DataFrame({ 'Charges': c,'parentheses':'','decimals':''},index=cind)
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
    charges['CourtAction'] = charges['Charges'].map(lambda x: re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x).group() if bool(re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x)) else "")
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
    noDatesEither = noNumCode.str.replace("\d{2}/\d{2}/\d{4}",'',regex=True)
    noWeirdColons = noDatesEither.str.replace("\:.+","",regex=True)
    descSplit = noWeirdColons.str.split(".{3}-.{3}-.{3}",regex=True)
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

#### CONFIGURATION METHOD - CALL ALAC.CONFIG() TO FEED CONF TO WRITE METHODS
def config(input_path, tables_path=None, archive_path=None, text_path=None, tables="", print_log=True, verbose=True, warn=False, max_cases=0, force_overwrite=True, GUI_mode=False, drop_cols=True): 

    tab_ext = ""
    arc_ext = ""
    in_ext = ""
    appendArchive = False
    stringInput = True
    pathMode = False
    old_archive = None

    if warn == False:
        warnings.filterwarnings("ignore")

## CONFIG - INPUT

    ## FILE INPUT (.PDF, .TXT, .PKL.XZ)
    if os.path.isfile(input_path): 
        in_head = os.path.split(input_path)[0]
        in_tail = os.path.split(input_path)[1]
        in_ext = os.path.splitext(input_path)[1]
        if in_ext == ".xz": # if archive 
            try:
                queue = pd.read_pickle(input_path,compression="xz")['AllPagesText']
                pathMode = False
            except KeyError:
                raise Exception("Could not identify Series \'AllPagesText\' in input archive!")
        elif in_ext == ".pdf": # if pdf get text
            queue = pd.Series([getPDFText(input_path)])
            pathMode = False
        elif in_ext == ".txt": # if txt get text
            pathMode = False
            with open(input_path,'r') as textfile:
                queue = pd.Series([textfile.read()])
        else:
            raise Exception("Invalid input!")

    ## DIRECTORY INPUT
    elif os.path.isdir(input_path):
        queue = pd.Series(glob.glob(input_path + '**/*.pdf', recursive=True))
        pathMode = True
        if queue.shape[0] == 0:
            raise Exception("No PDFs found in input directory!")

    ## DATAFRAME INPUT
    elif type(input_path) == pd.DataFrame:
        stringInput = False
        pathMode = False
        try:
            queue = input_path['AllPagesText']
        except KeyError:
            raise Exception("Could not identify Series \'AllPagesText\' in input path!")

    ## SERIES INPUT
    elif type(input_path) == pd.Series:
        stringInput = False
        try:
            if os.path.exists(input_path.tolist()[0]):
                pathMode = True
                queue = input_path
            elif "ALABAMA SJIS CASE DETAIL" in input_path.tolist()[0]:
                pathMode = False
                queue = input_path
            else:
                raise Exception("Could not parse input object!")
        except (AttributeError, KeyError, IndexError):
            raise Exception("Could not parse input object!")

    ## TEXT INPUT
    else:
        if "ALABAMA SJIS CASE DETAIL" in input_path:
            queue = [input_path]
            pathMode = False
        else:
            raise Exception("Warning: Input not supported! Alacorder may fail.")


    content_length = queue.shape[0]
    if queue.shape[0] > max_cases and max_cases > 0: # cap input at max
        queue = queue.sample(frac=1) # shuffle rows
        queue = queue[0:max_cases] # get max_cases 
    if max_cases > queue.shape[0] or max_cases == 0: # cap max at input len
        max_cases = queue.shape[0]

## CONFIG - ARCHIVE OUT
    if archive_path != None:
        arc_head = os.path.split(archive_path)[0]
        if os.path.exists(arc_head) == False:
            raise Exception("Invalid input!")
        arc_tail = os.path.split(archive_path)[1]
        arc_ext = os.path.splitext(arc_tail)[1]
        if arc_ext == ".xz": # if archive 
            if os.path.isfile(archive_path):
                try: # if exists at path, append
                    old_archive = pd.read_pickle(archive_path,compression="xz")
                    appendArchive = True
                except KeyError: # 
                    raise Exception("Invalid archive output path!")
            else:
                old_archive = None
                appendArchive = False
        else:
            raise Exception("Invalid file extension! Archives must export to .pkl.xz")

## CONFIG - TABLE OUT
    if tables_path != None:
        tab_head = os.path.split(tables_path)[0]
        if os.path.exists(tab_head) is False:
            raise Exception(f"Invalid table output path!")
        tab_tail = os.path.split(tables_path)[1]
        tab_ext = os.path.splitext(tab_tail)[1]
        if os.path.isfile(tables_path):
            if force_overwrite:
                if warn:
                    print("WARNING: FORCE OVERWRITE MODE IS ENABLED. EXISTING FILE AT TABLE OUTPUT PATH WILL BE OVERWRITTEN.")
                pass
            else:
                raise Exception("Existing file at output path! Provide valid table export path or use \'force_overwrite\' flag to replace existing file with task outputs.")
        elif os.path.exists(tab_head) == False or (tab_ext == ".xz" or tab_ext == ".pkl" or tab_ext == ".json" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".dta") == False:
            raise Exception("Table output invalid!")
        elif tables == "" and tab_ext != ".xls" and tab_ext != ".xlsx" and tab_ext != ".pkl" and tab_ext != ".xz":
            print(f"(DEFAULTING TO CASES TABLE) Must specify table export (cases, fees, charges) on table export to file extension {tab_ext}. Specify table or export to .xls or .xlsx to continue.")
        elif tab_ext == ".xz" or tab_ext == ".json" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".pkl" or tab_ext == ".dta":
            pass
        else:
            raise Exception("Invalid table output file extension! Must write to .xls, .xlsx, .pkl.xz, .csv, .json, or .dta.")

    if tables_path != None and archive_path != None and tables_path == archive_path:
        raise Exception("Cannot write tables and archive to same file!")

## CONFIG - LOG INPUT 
    if print_log and verbose:
        if tables_path == None and archive_path == None:
            if GUI_mode == False:
                print(f"No output path provided. alac.parse...() functions will {'print to console and' if print_log else ''} return object.")
            if GUI_mode == True:
                raise Exception(f"No output path provided! Use alac libraries without guided interface to return object to python.")
        if content_length > max_cases:
            print(f"\n>>    {max_cases} of {content_length} total {'paths' if pathMode else 'cases'} loaded from input: {input_path}")
        if content_length <= max_cases:
            print(f">>    INPUT:  {max_cases} {'paths' if pathMode else 'cases'} loaded from input: {input_path if pathMode else ''}")
        if tables_path != None:
            print(f">>    TABLES:  {'cases, charges, fees' if tables == '' else tables} to {tables_path}")
        if archive_path != None:
            print(f">>    ARCHIVE:  {'cases, charges, fees' if tables == '' else tables} to {'existing archive at: ' if appendArchive else ''}{archive_path}\n\n")

## CONFIG OBJECT
    return pd.Series({
        'input_path': input_path,
        'table_out': tables_path,
        'table_ext': tab_ext,
        'table': tables,
        'archive_out': archive_path,
        'archive_ext': arc_ext,
        'appendArchive': appendArchive, 
        'old_archive': old_archive,
        'warn': warn, 
        'log': print_log,
        'verbose': verbose, 
        'queue': queue, 
        'count': max_cases, 
        'path_mode': pathMode,
        'drop_cols': drop_cols
        })


def writeArchive(conf): 
    path_in = conf['input_path']
    path_out = conf['archive_out']
    out_ext = conf['archive_ext']
    max_cases = conf['count']
    queue = conf['queue']
    print_log = conf['log']
    warn = conf['warn']
    path_mode = conf['path_mode']
    max_cases = conf['count']
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")

    if path_mode:
        allpagestext = pd.Series(queue).map(lambda x: getPDFText(x))
    else:
        allpagestext = queue

    outputs = pd.DataFrame({
        'Path': queue if path_mode else np.nan,
        'AllPagesText': allpagestext,
        'Timestamp': start_time
        })

    outputs.fillna('',inplace=True)

    if bool(path_out):
        if out_ext == ".xls":
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table")
        if out_ext == ".xlsx":
            try:
                with pd.ExcelWriter(path_out) as writer:
                    outputs.to_excel(writer, sheet_name="output-table", engine="xlsxwriter")
            except ValueError:
                try:
                    with pd.ExcelWriter(path_out[0:-1]) as writer:
                        outputs.to_excel(writer, sheet_name="output-table")
                except ValueError:
                    outputs.to_csv(path_out,escapechar='\\')
                    print("Exported to CSV due to XLSX engine failure")
        if out_ext == ".pkl":
            outputs.to_pickle(path_out+".xz",compression="xz")
        if out_ext == ".xz":
            outputs.to_pickle(path_out,compression="xz")
        if out_ext == ".json":
            outputs.to_json(path_out)
        if out_ext == ".csv":
            outputs.to_csv(path_out,escapechar='\\')
        if out_ext == ".txt":
            outputs.to_string(path_out)
        if out_ext == ".dta":
            outputs.to_stata(path_out)
    else:
        if print_log:
            log_console(conf, f"(Batch {i+1}/{math.ceil(max_cases /1000)})", outputs)
    log_complete(conf, start_time)
    return outputs

def parseFees(conf):
    path_in = conf['input_path']
    path_out = conf['table_out']
    out_ext = conf['table_ext']
    max_cases = conf['count']
    queue = conf['queue']
    print_log = conf['log']
    warn = conf['warn']
    from_archive = False if conf['path_mode'] else True
    start_time = time.time()
    if warn == False:
        warnings.filterwarnings("ignore")
    outputs = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])

    if max_cases > 1000:
        batches = np.array_split(queue, math.ceil(max_cases / 1000))
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    else:
        batches = np.array_split(queue, 3)
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    for i, c in enumerate(batches):
        exptime = time.time()
        b = pd.DataFrame()

        if from_archive == True:
            b['AllPagesText'] = queue
        else:
            b['AllPagesText'] = pd.Series(queue).map(lambda x: getPDFText(x))

        b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
        b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
        b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText, b.loc[x].CaseNumber))



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
        # write 
        if out_ext == ".xls":
            with pd.ExcelWriter(path_out) as writer:
                fees.to_excel(writer, sheet_name="fees")
        if out_ext == ".xlsx":
            try:
                with pd.ExcelWriter(path_out) as writer:
                    fees.to_excel(writer, sheet_name="fees", engine="xlsxwriter")
            except ValueError:
                try:
                    with pd.ExcelWriter(path_out[0:-1]) as writer:
                        fees.to_excel(writer, sheet_name="fees")
                except ValueError:
                    outputs.to_csv(path_out,escapechar='\\')
                    print("Exported to CSV due to XLSX engine failure")
        elif out_ext == ".pkl":
            fees.to_pickle(path_out+".xz",compression="xz")
        elif out_ext == ".xz":
            fees.to_pickle(path_out,compression="xz")
        elif out_ext == ".json":
            fees.to_json(path_out)
        elif out_ext == ".csv":
            fees.to_csv(path_out,escapechar='\\')
        elif out_ext == ".md":
            fees.to_markdown(path_out)
        elif out_ext == ".txt":
            fees.to_string(path_out)
        elif out_ext == ".dta":
            fees.to_stata(path_out)
        else:
            if print_log:
                log_console(conf, fees, f"\n(Batch {i+1}/{math.ceil(max_cases/1000)})")
        
    if print_log == True:
        log_complete(conf, start_time)
    return fees

def parseCharges(conf):
    path_in = conf['input_path']
    path_out = conf['table_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    queue = conf['queue']
    warn = conf['warn']
    table = conf['table']
    from_archive = False if conf['path_mode'] else True

    if warn == False:
        warnings.filterwarnings("ignore")

    if max_cases > 1000:
        batches = np.array_split(queue, math.ceil(max_cases / 1000))
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    else:
        batches = np.array_split(queue, 3)
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    start_time = time.time()
    outputs = pd.DataFrame()
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
    for i, c in enumerate(batches):
        exptime = time.time()
        b = pd.DataFrame()

        if from_archive == True:
            b['AllPagesText'] = queue
        else:
            b['AllPagesText'] = pd.Series(queue).map(lambda x: getPDFText(x))

        b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
        b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
        b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText, b.loc[x].CaseNumber))

        
        chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
        chargetabs = chargetabs.dropna()

        charges = charges.dropna()
        chargetabs = chargetabs.tolist()
        chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
        charges = charges.append(chargetabs,ignore_index=True)
        charges.fillna('',inplace=True)

        if table == "filing":
            is_disp = charges['Disposition']
            is_filing = is_disp.map(lambda x: False if x == True else True)
            charges = charges[is_disp]

        if table == "disposition":
            is_disp = charges['Disposition']
            charges = charges[is_disp]

        # charges = charges[['CaseNumber', 'Num', 'Code', 'Description', 'Cite', 'CourtAction', 'CourtActionDate', 'Category', 'TypeDescription', 'Disposition', 'Permanent', 'Pardon', 'CERV','Conviction']]

        # write 
        if out_ext == ".xls":
            try:
                with pd.ExcelWriter(path_out) as writer:
                    charges.to_excel(writer, sheet_name="charges", engine="xlsxwriter")
            except ValueError:
                try:
                    with pd.ExcelWriter(path_out) as writer:
                        charges.to_excel(writer, sheet_name="charges")
                except ValueError:
                    charges.to_csv(path_out,escapechar='\\')
                    log_console(conf, charges, f"\n(Batch {i+1}) ERROR: Exported to CSV due to XLS engine failure")
        if out_ext == ".xlsx":
            try:
                with pd.ExcelWriter(path_out) as writer:
                    charges.to_excel(writer, sheet_name="charges", engine="xlsxwriter")
            except ValueError:
                try:
                    with pd.ExcelWriter(path_out) as writer:
                        charges.to_excel(writer, sheet_name="charges")
                except ValueError:
                    charges.to_csv(path_out,escapechar='\\')
                    log_console(conf, charges.to_string(), f"(Batch {i+1}) ERROR: Exported to CSV due to XLSX engine failure!")
        elif out_ext == ".pkl":
            charges.to_pickle(path_out+".xz",compression="xz")
        elif out_ext == ".xz":
            charges.to_pickle(path_out,compression="xz")
        elif out_ext == ".json":
            charges.to_json(path_out)
        elif out_ext == ".csv":
            charges.to_csv(path_out,escapechar='\\')
        elif out_ext == ".md":
            charges.to_markdown(path_out)
        elif out_ext == ".txt":
            charges.to_string(path_out)
        elif out_ext == ".dta":
            charges.to_stata(path_out)
        else:
            if print_log:
                log_console(conf, f"(Batch {i+1}) ", charges.to_string())

    if print_log == True:
        log_complete(conf, start_time)
    return charges

def parseTables(conf):
    path_in = conf['input_path']
    path_out = conf['table_out']
    archive_out = conf['archive_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    warn = conf['warn']
    queue = conf['queue']
    from_archive = False if conf['path_mode'] else True
    start_time = time.time()
    arc_ext = conf['archive_ext']
    
    cases = pd.DataFrame()
    fees = pd.DataFrame({'CaseNumber': '', 'FeeStatus': '','AdminFee': '', 'Code': '', 'Payor': '', 'AmtDue': '', 'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])
    charges = pd.DataFrame({'CaseNumber': '', 'Num': '', 'Code': '', 'Felony': '', 'Conviction': '', 'CERV': '', 'Pardon': '', 'Permanent': '', 'Disposition': '', 'CourtActionDate': '', 'CourtAction': '', 'Cite': '', 'TypeDescription': '', 'Category': '', 'Description': ''},index=[0]) 
    arch = pd.DataFrame({'Path':'','AllPagesText':'','Timestamp':''},index=[0])

    if not from_archive:
        if max_cases > 1000:
            batches = np.array_split(queue, math.ceil(max_cases / 1000))
            batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
        else:
            batches = np.array_split(queue, 3)
            batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    else:
        batches = np.array_split(queue, 2)
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    if warn == False:
        warnings.filterwarnings("ignore")

    for i, c in enumerate(batches):

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
        b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
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
        b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText, b.loc[x].CaseNumber))
        b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
        b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
        b['TotalD999'] = b['FeeOutputs'].map(lambda x: x[2])
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

        if print_log == True:
            print(fees)

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

        if print_log == True:
            log_console(conf, f"(Batch {i+1}) ", charges)
        
        fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))

        b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
        b['TotalD999'] = b['TotalD999'].map(lambda x: pd.to_numeric(x,'ignore'))
        b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'ignore'))
        b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'ignore'))
        b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'ignore'))

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

       #  b = [['CaseNumber','Name','Alias','DOB','Race','Sex','Address','Phone','TotalAmtDue','TotalBalance','DispositionCharges','Conviction','FeeCodes','FeeCodesOwed','CERVConvictions','CERVConvictionCount','PardonConvictions','PardonConvictionCount','PermanentConvictions','PermanentConvictionCount']]
        b.drop(columns=['AllPagesText','CaseInfoOutputs','ChargesOutputs','FeeOutputs','TotalD999','ChargesTable','FeeSheet'],inplace=True)
        
        b.fillna('',inplace=True)
        charges.fillna('',inplace=True)
        fees.fillna('',inplace=True)
        newcases = [cases, b]

        cases = cases.append(newcases, ignore_index=True)

        charges = charges[['CaseNumber', 'Num', 'Code', 'Description', 'Cite', 'CourtAction', 'CourtActionDate', 'Category', 'TypeDescription', 'Disposition', 'Permanent', 'Pardon', 'CERV','Conviction']]

        fees = fees[['CaseNumber', 'FeeStatus', 'AdminFee','Total', 'Code', 'Payor', 'AmtDue', 'AmtPaid', 'Balance', 'AmtHold']]

        # write 
        if out_ext == ".xls":
            try:
                with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                    cases.to_excel(writer, sheet_name="cases")
                    fees.to_excel(writer, sheet_name="fees")
                    charges.to_excel(writer, sheet_name="charges")
            except ImportError:
                with pd.ExcelWriter(path_out) as writer:
                    cases.to_excel(writer, sheet_name="cases")
                    fees.to_excel(writer, sheet_name="fees")
                    charges.to_excel(writer, sheet_name="charges")
        elif out_ext == ".xlsx":
            try:
                with pd.ExcelWriter(path_out,engine="xlsxwriter") as writer:
                    cases.to_excel(writer, sheet_name="cases")
                    fees.to_excel(writer, sheet_name="fees")
                    charges.to_excel(writer, sheet_name="charges")
            except ImportError:
                try:
                    with pd.ExcelWriter(path_out.slice[0:-1]) as writer:
                        cases.to_excel(writer, sheet_name="cases")
                        fees.to_excel(writer, sheet_name="fees")
                        charges.to_excel(writer, sheet_name="charges")
                except (ImportError, FileNotFoundError):
                    try:
                        cases.to_csv(path_out + ".csv",escapechar='\\')
                        fees.to_csv(path_out + ".csv",escapechar='\\')
                        charges.to_csv(path_out + ".csv",escapechar='\\')
                        log_console(conf, f"(Batch {i+1}) - WARNING: Exported to CSV due to XLSX engine failure")
                    except (ImportError, FileNotFoundError):
                        pass
        elif out_ext == ".pkl":
            b.to_pickle(path_out+".xz",compression="xz")
        elif out_ext == ".xz":
            b.to_pickle(path_out,compression="xz")
        elif out_ext == ".json":
            b.to_json(path_out)
        elif out_ext == ".csv":
            b.to_csv(path_out,escapechar='\\')
        elif out_ext == ".md":
            b.to_markdown(path_out)
        elif out_ext == ".txt":
            b.to_string(path_out)
        elif out_ext == ".dta":
            b.to_stata(path_out)
        else:
            log_console(conf, f"(Batch {i+1}) ", b, charges, fees)
        if print_log == True:
            log_complete(conf, start_time)
    return [cases, fees, charges]

def parse(conf, method, status=''):
    path_in = conf['input_path']
    path_out = conf['table_out']
    max_cases = conf['count']
    out_ext = conf['table_ext']
    print_log = conf['log']
    warn = conf['warn']
    queue = conf['queue']
    from_archive = False if conf['path_mode'] else True
    if warn == False:
        warnings.filterwarnings("ignore")
    if not from_archive:
        if max_cases > 1000:
            batches = np.array_split(queue, math.ceil(max_cases / 1000))
            batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
        else:
            batches = np.array_split(queue, 3)
            batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))
    else:
        batches = np.array_split(queue, 2)
        batchsize = max(pd.Series(batches).map(lambda x: x.shape[0]))

    start_time = time.time()
    alloutputs = pd.Series()
    uselist = False
    for i, c in enumerate(batches):
        exptime = time.time()
        b = pd.DataFrame()

        if from_archive == True:
            allpagestext = c
        else:
            allpagestext = pd.Series(c).map(lambda x: getPDFText(x))

        customoutputs = allpagestext.map(lambda x: method(x))
        alloutputs = alloutputs.append(customoutputs)
        
        if out_ext == ".xls":
            with pd.ExcelWriter(path_out) as writer:
                alloutputs.to_excel(writer, sheet_name="output-table")
        if out_ext == ".xlsx":
            try:
                with pd.ExcelWriter(path_out) as writer:
                    alloutputs.to_excel(writer, sheet_name="output-table", engine="xlsxwriter")
            except ValueError:
                try:
                    with pd.ExcelWriter(path_out[0:-1]) as writer:
                        alloutputs.to_excel(writer, sheet_name="output-table")
                except ValueError:
                    alloutputs.to_csv(path_out,escapechar='\\')
                    log_console(conf, f"(Batch {i+1}) - WARNING: Exported to CSV due to XLSX engine failure")
        elif out_ext == ".pkl":
            alloutputs.to_pickle(path_out+".xz",compression="xz")
        elif out_ext == ".xz":
            alloutputs.to_pickle(path_out,compression="xz")
        elif out_ext == ".json":
            alloutputs.to_json(path_out)
        elif out_ext == ".csv":
            alloutputs.to_csv(path_out,escapechar='\\')
        elif out_ext == ".md":
            alloutputs.to_markdown(path_out)
        elif out_ext == ".txt":
            alloutputs.to_string(path_out)
        elif out_ext == ".dta":
            alloutputs.to_stata(path_out)
        else:
            log_console(conf, alloutputs)

    if print_log == True:
        log_complete(conf, start_time)
    return alloutputs

def log_complete(conf, start_time):
    path_in = conf['input_path']
    path_out = conf['table_out']
    arc_out = conf['archive_out']
    print_log = conf['log']
    max_cases = conf['count']
    verbose = conf['verbose']
    completion_time = time.time()
    elapsed = completion_time - start_time
    cases_per_sec = max_cases/elapsed

    if print_log:
        print(f'''

>>  ALACORDER PROGRESS:

    >>    INPUT: {path_in} 
    >>    OUTPUT: {path_out} 
    >>    ARCHIVE: {arc_out}

    >>    Processing {max_cases} cases...
    >>    Last batch completed in {elapsed:.2f} seconds ({cases_per_sec:.2f}cases/sec)
        
        ''') 

def log_console(conf, *msg):
    path_in = conf['input_path']
    path_out = conf['table_out']
    arc_out = conf['archive_out']
    print_log = conf['log']
    max_cases = conf['count']
    verbose = conf['verbose']

    if print_log:
        print(msg)

