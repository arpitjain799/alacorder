 
# alac 73
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
import click
import PyPDF2
from io import StringIO

pd.set_option("mode.chained_assignment",None)
pd.set_option("display.notebook_repr_html",True)
pd.set_option("display.width",None)
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 250)

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
        return case_num
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


def getTotalAmtDue(text: str):
    try:
        trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
        totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
        if len(totalrow.split("$")[-1])>5:
            totalrow = totalrow.split(" . ")[0]
        tdue = totalrow.split("$")[1].strip().replace("$","").replace(",","").replace(" ","").astype(float)
    except IndexError:
        tbal = np.nan
    return tbal

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
        return name + "\r" + alias

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

def getFeeSheet(text: str):
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
        adminfeerows = fees.map(lambda x: x.strip()[7].strip())
        

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
    return getFeeSheet(text)[4]
def getFeeCodesOwed(text: str):
    return getFeeSheet(text)[3]
def getTotals(text: str):
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
    try:
        trowraw = re.findall(r'(Total.*\$.*)', str(text), re.MULTILINE)[0]
        totalrow = re.sub(r'[^0-9|\.|\s|\$]', "", trowraw)
        if len(totalrow.split("$")[-1])>5:
            totalrow = totalrow.split(" . ")[0]
        tbal = totalrow.split("$")[3].strip().replace("$","").replace(",","").replace(" ","")
        tbal = float(tbal)
    except:
        tbal = np.nan
    return tbal

def getBalanceByCode(text: str, code: str):
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
    return matches.sum()

def getAmtDueByCode(text: str, code: str):
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
    return due 
def getAmtPaidByCode(text: str, code: str):
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
    return paid

def getCharges(text: str):
    cnum = getCaseNumber(text)
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
    charges['Charges'] = charges['Charges'].map(lambda x: re.sub(r'(©.+)','',x,re.MULTILINE))
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

def getConvictions(text) -> str:
    return getCharges(text)[0]
def getDispositionCharges(text) -> str:
    return getCharges(text)[1]
def getFilingCharges(text) -> str:
    return getCharges(text)[2]
def getCERVConvictions(text) -> str:
    return getCharges(text)[3]
def getPardonConvictions(text) -> str:
    return getCharges(text)[4]
def getPermanentConvictions(text) -> str:
    return getCharges(text)[5]
def getConvictionCount(text) -> int:
    return getCharges(text)[6]
def getChargeCount(text) -> int:
    return getCharges(text)[7]
def getCERVChargeCount(text) -> int:
    return getCharges(text)[8]
def getPardonDQCount(text) -> int:
    return getCharges(text)[9]
def getPermanentDQChargeCount(text) -> int:
    return getCharges(text)[10]
def getCERVConvictionCount(text) -> int:
    return getCharges(text)[11]
def getPardonDQConvictionCount(text) -> int:
    return getCharges(text)[12]
def getPermanentDQConvictionCount(text) -> int:
    return getCharges(text)[13]
def getChargeCodes(text) -> [str]:
    return getCharges(text)[14]
def getConvictionCodes(text) -> [str]:
    return getCharges(text)[15]
def getChargesString(text) -> str:
    return getCharges(text)[16]



def config(input_path, table_path=None, archive_path=None, text_path=None, tables="", print_log=True, verbose=False, warn=False, max_cases=0, force_overwrite=True, GUI_mode=False, drop_cols=True): 

    tab_ext = ""
    arc_ext = ""
    in_ext = ""
    appendArchive = False
    stringInput = True
    pathMode = False
    old_archive = None
    old_table = None

    if warn == False:
        warnings.filterwarnings("ignore")

## CONFIG - INPUT

    ## OBJECT INPUT

    if archive_path == None and os.path.splitext(table_path)[1] == ".xz":
        archive_path = table_path
        table_path = None
        if log:
            click.echo(f"WARNING: alac.config() received archive file format for parameter table_path: Setting archive_path to {archive_path}. Reconfigure to export tables.")


    if isinstance(input_path, pd.core.series.Series) or isinstance(input_path, pd.core.frame.DataFrame):
        obj_in = input_path
        input_path = ""
        if "AllPagesText" in obj_in.columns:
            pathMode = False
            queue = obj_in['AllPagesText']
        else:
            raise Exception("Object input only supports archives! Must use \'AllPagesText\' series to continue.")

    ## EXISTING FILE INPUT

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

    try:
        content_length = queue.shape[0]
    except UnboundLocalError:
        content_length = 1
        queue = []
    if content_length > max_cases and max_cases > 0: # cap input at max
        queue = queue.sample(frac=1) # shuffle rows
        queue = queue[0:max_cases] # get max_cases 
    if max_cases > content_length or max_cases == 0: # cap max at input len
        max_cases = content_length

## CONFIG - ARCHIVE OUT
    if archive_path != None:
        arc_head = os.path.split(archive_path)[0]
        if os.path.exists(arc_head) == False:
            raise Exception("Invalid input!")
        arc_tail = os.path.split(archive_path)[1]
        arc_ext = os.path.splitext(arc_tail)[1]
        if arc_ext == ".xz": # if archive 
            try: # if exists at path, append
                old_archive = pd.read_pickle(archive_path,compression="xz")
                appendArchive = True
            except: 
                pass
        else:
            raise Exception("Invalid file extension! Archives must export to .pkl.xz")

## CONFIG - TABLE OUT
    if table_path != None:
        tab_head = os.path.split(table_path)[0]
        if os.path.exists(tab_head) is False:
            raise Exception(f"Invalid table output path!")
        tab_tail = os.path.split(table_path)[1]
        tab_ext = os.path.splitext(tab_tail)[1]
        if os.path.isfile(table_path):
            if force_overwrite:
                if warn:
                    click.echo("WARNING: FORCE OVERWRITE MODE IS ENABLED. EXISTING FILE AT TABLE OUTPUT PATH WILL BE OVERWRITTEN.")
                pass
            else:
                raise Exception("Existing file at output path! Provide valid table export path or use \'force_overwrite\' flag to replace existing file with task outputs.")
        elif os.path.exists(tab_head) == False or (tab_ext == ".xz" or tab_ext == ".pkl" or tab_ext == ".json" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".dta") == False:
            raise Exception("Table output invalid!")
        elif tables == "" and tab_ext != ".xls" and tab_ext != ".xlsx" and tab_ext != ".pkl" and tab_ext != ".xz":
            click.echo(f"(DEFAULTING TO CASES TABLE) Must specify table export (cases, fees, charges) on table export to file extension {tab_ext}. Specify table or export to .xls or .xlsx to continue.")
        elif tab_ext == ".xz" or tab_ext == ".json" or tab_ext == ".xls" or tab_ext == ".xlsx" or tab_ext == ".csv" or tab_ext == ".txt" or tab_ext == ".pkl" or tab_ext == ".dta":
            pass
        else:
            raise Exception("Invalid table output file extension! Must write to .xls, .xlsx, .csv, .json, or .dta.")

## CONFIG - LOG INPUT 
    if print_log == True and verbose == True:
        if table_path == None and archive_path == None:
            if GUI_mode == False:
                click.echo(f"\nNo output path provided. alac.parse...() functions will {'print to console and' if print_log else ''} return object.")
            if GUI_mode == True:
                raise Exception(f"No output path provided! Use alac libraries without guided interface to return object to python.")
        if content_length > max_cases:
            click.echo(f"\n>>    INPUT:  {max_cases} of {content_length} total {'paths' if pathMode else 'cases'} loaded from input: {input_path}")
        if content_length <= max_cases:
            click.echo(f"\n>>    INPUT:  {max_cases} {'paths' if pathMode else 'cases'} loaded from input: {input_path if pathMode else ''}")
        if table_path != None:
            click.echo(f">>    TABLES:  {'cases, charges, fees' if tables == '' else tables} to {table_path}")
        if archive_path != None:
            click.echo(f">>    ARCHIVE:  {'cases, charges, fees' if tables == '' else tables} to {'existing archive at: ' if appendArchive else ''}{archive_path}\n\n")

## CONFIG OBJECT
    return pd.Series({
        'input_path': input_path,
        'table_out': table_path,
        'table_ext': tab_ext,
        'table': tables,
        'archive_out': archive_path,
        'archive_ext': arc_ext,
        'appendArchive': appendArchive, 
        'old_archive': old_archive,
        'old_table': old_table,
        'warn': warn, 
        'log': print_log,
        'verbose': verbose, 
        'queue': queue,
        'count': max_cases, 
        'path_mode': pathMode,
        'drop_cols': drop_cols
        })
    
def splitext(path: str):
    head = os.path.split(path)[0]
    tail = os.path.split(path)[1]
    ext = os.path.splitext(path)[1] 
    return pd.Series({
        'head': head,
        'tail': tail,
        'ext': ext
    })

def checkPath(path: str, log=True):
    PathType = ""
    if os.path.isdir(path):
        count = len(glob.glob(path + '**/*.pdf', recursive=True))
        if count == 0:
            PathType = "bad"
            warnings.warn("No PDFs found in input path!")
        if count > 0:
            PathType = "pdf_directory"
            if log:
                click.echo(f"\nAlacorder found {count} PDFs in input directory.")
            return PathType
    else:
        head = os.path.split(path)[0]
        tail = os.path.split(path)[1]
        ext = os.path.splitext(path)[1]

        if not os.path.isdir(head):
            PathType = "bad"
            warnings.warn("ERROR: Invalid output path!")
            return PathType

        if os.path.isfile(path):
            if ext == ".txt":
                PathType = "text"
                if log:
                    click.echo(f"WARNING: text file input experimental!")
            if ext == ".pdf":
                PathType = "pdf"
            if ext == ".xz":
                test = pd.read_pickle(path,compression="xz")
                if "AllPagesText" in test.columns:
                    PathType = "existing_archive"
                    if log:
                        click.echo(f"Found existing archive with {test.shape[0]} cases. APPEND MODE is enabled.")
                    return PathType
                else:
                    PathType = "overwrite_archive"
                    if log:
                        click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
                    return PathType
            elif ext == ".xls" or ext == ".xlsx":
                if log:
                    click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
                PathType = "overwrite_all_tables"
                return PathType
            elif ext == ".csv" or ext == ".json" or ext == ".dta":
                if log:
                    click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
                PathType = "overwrite_table"
                return PathType
            else:
                PathType = "bad"
                if log:
                    click.echo("Output file extension not supported!")
                if log:
                    click.echo("WARNING: Existing file at archive output cannot be parsed and will be overwritten!")
                return PathType
        else:
            if ext == ".xls" or ext == ".xlsx":
                PathType = "all_tables"
                return PathType
            elif ext == ".xz":
                PathType = "archive"
                return PathType
            elif ext == ".csv" or ext == ".json" or ext == ".dta" or ext == ".txt":
                PathType = "table"
                return PathType
            else:
                PathType = "bad"
                warnings.warn("Output file extension not supported!")
                return PathType
    return PathType

def write(conf, outputs, archive=False):
    max_cases = conf['count']
    old_archive = conf['old_archive']
    if isinstance(old_archive, pd.core.frame.DataFrame):
        try:
            outputs = old_archive.append(outputs)
        except (AttributeError, TypeError):
          outputs = pd.Series([old_archive, outputs])
    if archive:
        path_out = conf['archive_out']
    else:
        path_out = conf['table_out']
    print_log = conf['log']
    warn = conf['warn']
    try:
        out_ext = os.path.splitext(path_out)[1]
    except TypeError:
        out_ext = ""

    if out_ext == ".xls":
        try:
            with pd.ExcelWriter(path_out) as writer:
                outputs.to_excel(writer, sheet_name="output-table")
        except ValueError:
            try:
                with pd.ExcelWriter(path_out,engine="xlwt") as writer:
                    outputs.to_excel(writer, sheet_name="output-table")
            except ValueError:
                outputs.to_csv(path_out,escapechar='\\')
                if warn or print_log:
                    click.echo("Exported to CSV due to XLSX engine failure")
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
                if warn or print_log:
                    click.echo("Exported to CSV due to XLSX engine failure")
    elif out_ext == ".pkl":
        outputs.to_pickle(path_out+".xz",compression="xz")
    elif out_ext == ".xz":
        outputs.to_pickle(path_out,compression="xz")
    elif out_ext == ".json":
        outputs.to_json(path_out)
    elif out_ext == ".csv":
        outputs.to_csv(path_out,escapechar='\\')
    elif out_ext == ".txt":
        outputs.to_string(path_out)
    elif out_ext == ".dta":
        outputs.to_stata(path_out)
    else:
        if warn:
            click.echo("Warning: Failed to export!")
    click.launch(path_out)
    return outputs 

def parseTables(config, tables=""): # aim to remove
    a = []
    if tables == "all" or tables == "all_cases" or tables == "":
        a = parseCases(config)
    if tables == "cases":
        a = parseCaseInfo(config)
    if tables == "fees":
        a = parseFees(config)
    if tables == "charges":
        a = parseCharges(config)
    if tables == "disposition":
        a = parseCharges(config)
    if tables == "filing":
        a = parseCharges(config)
    return a

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
    old_archive = conf['old_archive']

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

    if isinstance(old_archive, pd.core.frame.DataFrame):
        try:
            outputs = old_archive.append(outputs)
        except:
            outputs = [old_archive, outputs]

    outputs.fillna('',inplace=True)
    write(conf, outputs, archive=True)
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
    fees = pd.DataFrame({'CaseNumber': '', 
        'Code': '', 'Payor': '', 'AmtDue': '', 
        'AmtPaid': '', 'Balance': '', 'AmtHold': ''},index=[0])

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
        b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText))

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
        write(conf, fees)
        
    if print_log == True:
        log_complete(conf, start_time)
    return fees

def getPaymentToRestore(text: str):
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
    return t_out

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
    charges = pd.DataFrame()
    for i, c in enumerate(batches):
        exptime = time.time()
        b = pd.DataFrame()

        if from_archive == True:
            b['AllPagesText'] = queue
        else:
            b['AllPagesText'] = pd.Series(queue).map(lambda x: getPDFText(x))

        b['CaseInfoOutputs'] = b['AllPagesText'].map(lambda x: getCaseInfo(x))
        b['CaseNumber'] = b['CaseInfoOutputs'].map(lambda x: x[0])
        b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText))

        
        chargetabs = b['ChargesOutputs'].map(lambda x: x[17])
        chargetabs = chargetabs.dropna()
        chargetabs = chargetabs.tolist()
        chargetabs = pd.concat(chargetabs,axis=0,ignore_index=True)
        charges = charges.append(chargetabs,ignore_index=True)
        charges.fillna('',inplace=True)

        if table == "filing":
            is_disp = charges['Disposition']
            is_filing = is_disp.map(lambda x: False if x == True else True)
            charges = charges[is_filing]

        if table == "disposition":
            is_disp = charges.Disposition.map(lambda x: True if x == True else False)
            charges = charges[is_disp]


        write(conf, charges)

    if print_log == True:
        log_complete(conf, start_time)

    return charges

def parseCases(conf):
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
        b['ChargesOutputs'] = b.index.map(lambda x: getCharges(b.loc[x].AllPagesText))
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
        b['FeeOutputs'] = b.index.map(lambda x: getFeeSheet(b.loc[x].AllPagesText))
        b['TotalAmtDue'] = b['FeeOutputs'].map(lambda x: x[0])
        b['TotalBalance'] = b['FeeOutputs'].map(lambda x: x[1])
        b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: getPaymentToRestore(x))
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

        if print_log == True:
            log_console(conf, f"(Batch {i+1}) ", charges)
        
        fees['AmtDue'] = fees['AmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['AmtPaid'] = fees['AmtPaid'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['Balance'] = fees['Balance'].map(lambda x: pd.to_numeric(x,'coerce'))
        fees['AmtHold'] = fees['AmtHold'].map(lambda x: pd.to_numeric(x,'coerce'))

        b['ChargesTable'] = b['ChargesOutputs'].map(lambda x: x[-1])
        b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
        b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
        b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))
        b['PaymentToRestore'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))


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
                    with pd.ExcelWriter(path_out) as writer:
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

def parseCaseInfo(conf):
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
        b['Totals'] = b['AllPagesText'].map(lambda x: getTotals(x))
        b['TotalAmtDue'] = b['Totals'].map(lambda x: x[1])
        b['TotalAmtPaid'] = b['Totals'].map(lambda x: x[2])
        b['TotalBalance'] = b['Totals'].map(lambda x: x[3])
        b['TotalAmtHold'] = b['Totals'].map(lambda x: x[4])
        b['PaymentToRestore'] = b['AllPagesText'].map(lambda x: getPaymentToRestore(x))
        b['ConvictionCodes'] = b['AllPagesText'].map(lambda x: getConvictionCodes(x))
        b['ChargeCodes'] = b['AllPagesText'].map(lambda x: getChargeCodes(x))
        b['FeeCodes'] = b['AllPagesText'].map(lambda x: getFeeCodes(x))
        b['FeeCodesOwed'] = b['AllPagesText'].map(lambda x: getFeeCodesOwed(x))
        b['DispositionCharges'] = b['AllPagesText'].map(lambda x: getDispositionCharges(x))
        b['FilingCharges'] = b['AllPagesText'].map(lambda x: getFilingCharges(x))
        b['CERVConvictions'] = b['AllPagesText'].map(lambda x: getCERVConvictions(x))
        b['PardonDQConvictions'] = b['AllPagesText'].map(lambda x: getPardonConvictions(x))
        b['PermanentDQConvictions'] = b['AllPagesText'].map(lambda x: getPermanentConvictions(x))

        if print_log == True:
            log_console(conf, b, f"\n(Batch {i+1})\n")
        
        b['Phone'] =  b['Phone'].map(lambda x: pd.to_numeric(x,'coerce'))
        b['TotalAmtDue'] = b['TotalAmtDue'].map(lambda x: pd.to_numeric(x,'coerce'))
        b['TotalBalance'] = b['TotalBalance'].map(lambda x: pd.to_numeric(x,'coerce'))

        b.drop(columns=['AllPagesText','CaseInfoOutputs','Totals'],inplace=True)
        
        b.fillna('',inplace=True)
        newcases = [cases, b]

        cases = cases.append(newcases, ignore_index=True)

        # write 
        write(conf, cases)
    return cases

def parse(conf, method, *args):
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
    alloutputs = []
    uselist = False

    def ExceptionWrapper(mfunc, x, *args):
        a = mfunc(x, *args)
        return a

    with click.progressbar(batches) as bar:
        for i, c in enumerate(batches):
            exptime = time.time()
            b = pd.DataFrame()

            if from_archive == True:
                allpagestext = c
            else:
                allpagestext = pd.Series(c).map(lambda x: getPDFText(x))

            customoutputs = allpagestext.map(lambda x: ExceptionWrapper(method, x, *args))
            alloutputs += customoutputs.tolist()

            write(conf, pd.Series(alloutputs))

    allout = pd.Series(alloutputs).infer_objects()
    try:
        allout = allout.map(lambda x: x.values[0])
    except AttributeError:
        pass

    if print_log == True:
        log_complete(conf, start_time)
    return allout

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
        click.clear()
        click.echo(f'''

    >>  TASK COMPLETED!

        {">>     INPUT: "+path_in if bool(path_in) else ""}
        {">>     OUTPUT: "+path_out if bool(path_out) else ""}
        {">>     ARCHIVE: "+arc_out if bool(arc_out) else ""}

    >>    Successfully processed {max_cases} cases.
    >>    Last batch completed in {elapsed:.2f} seconds ({cases_per_sec:.2f} cases/sec)
        
        ''')

def log_console(conf, *msg):
    path_in = conf['input_path']
    path_out = conf['table_out']
    arc_out = conf['archive_out']
    print_log = conf['log']
    max_cases = conf['count']
    verbose = conf['verbose']
    click.clear()
    if print_log:
        click.echo(msg)
        click.echo(f'''

    >>  ALACORDER IN PROGRESS:

        {">>     INPUT: "+path_in if bool(path_in) else ""}
        {">>     OUTPUT: "+path_out if bool(path_out) else ""}
        {">>     ARCHIVE: "+arc_out if bool(arc_out) else ""}

        ''')


