
# get 74
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
import alacorder as alac
import warnings
import click
import inspect
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass

def PDFText(path: str) -> str:
    """Returns PyPDF2 extract_text() outputs for all pages from path"""
    text = ""
    pdf = PyPDF2.PdfReader(path)
    for pg in pdf.pages:
        text += pg.extract_text()
    return text
def CaseNumber(text: str):
    """Returns full case number with county number prefix from case text"""
    try:
        county: str = re.search(r'(?:County\: )(\d{2})(?:Case)', str(text)).group(1).strip()
        case_num: str = county + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}.\d{2})', str(text)).group(1).strip() 
        return case_num
    except (IndexError, AttributeError):
        return ""
def Name(text: str):
    """Returns name from case text"""
    name = ""
    if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
        name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
    else:
        if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
            name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
    return name
def DOB(text: str):
    """Returns DOB from case text"""
    dob = ""
    if bool(re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL)):
        dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
    return dob

def TotalAmtDue(text: str):
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
def Address(text: str):
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
def Race(text: str):
    """Return race from case text"""
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    race = racesex.group(1).strip()
    sex = racesex.group(2).strip()
    return race
def Sex(text: str):
    """Return sex from case text"""
    racesex = re.search(r'(B|W|H|A)\/(F|M)(?:Alias|XXX)', str(text))
    sex = racesex.group(2).strip()
    return sex
def NameAlias(text: str):
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

def CaseInfo(text: str): ## FIX: DEPRECATED -> replace with small getters in parseCases() and parseCaseInfo()
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
def Phone(text: str):
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

def FeeSheet(text: str):
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
        adminfeerows = fees.map(lambda x: x.strip()[7].strip())
        

        feesheet = pd.DataFrame({
            'CaseNumber': CaseNumber(text),
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
            'CaseNumber': CaseNumber(text),
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
def FeeCodes(text: str):
    """Return fee codes from case text"""
    return FeeSheet(text)[4]
def FeeCodesOwed(text: str):
    """Return fee codes with positive balance owed from case text"""
    return FeeSheet(text)[3]
def Totals(text: str):
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
def TotalBalance(text: str):
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
def PaymentToRestore(text: str):
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
def BalanceByCode(text: str, code: str):
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
def AmtDueByCode(text: str, code: str):
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
def AmtPaidByCode(text: str, code: str):
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
def Charges(text: str):
    """
    Returns charges summary from case text -> List: [convictions, dcharges, fcharges, cerv_convictions, pardon_convictions, perm_convictions, conviction_ct, charge_ct, cerv_ct, pardon_ct, perm_ct, conv_cerv_ct, conv_pardon_ct, conv_perm_ct, charge_codes, conv_codes, allcharge, charges]
    """
    cnum = CaseNumber(text)
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
def Convictions(text):
    """
    Return convictions as string from case text
    """
    return Charges(text)[0]
def DispositionCharges(text):
    """
    Return disposition charges as string from case text
    """
    return Charges(text)[1]
def FilingCharges(text):
    """
    Return filing charges as string from case text
    """
    return Charges(text)[2]
def CERVConvictions(text):
    """
    Return CERV convictions as string from case text
    """
    return Charges(text)[3]
def PardonDQConvictions(text):
    """
    Return pardon-to-vote charges as string from case text
    """
    return Charges(text)[4]
def PermanentDQConvictions(text):
    """
    Return permanent no vote charges as string from case text
    """
    return Charges(text)[5]
def ConvictionCount(text):
    """
    Return convictions count from case text
    """
    return Charges(text)[6]
def ChargeCount(text):
    """
    Return charges count from case text
    """
    return Charges(text)[7]
def CERVChargeCount(text):
    """
    Return CERV charges count from case text
    """
    return Charges(text)[8]
def PardonDQCount(text):
    """
    Return pardon-to-vote charges count from case text
    """
    return Charges(text)[9]
def PermanentDQChargeCount(text):
    """
    Return permanent no vote charges count from case text
    """
    return Charges(text)[10]
def CERVConvictionCount(text):
    """
    Return CERV convictions count from case text
    """
    return Charges(text)[11]
def PardonDQConvictionCount(text):
    """
    Return pardon-to-vote convictions count from case text
    """
    return Charges(text)[12]
def PermanentDQConvictionCount(text):
    """
    Return permanent no vote convictions count from case text
    """
    return Charges(text)[13]
def ChargeCodes(text):
    """
    Return charge codes as string from case text
    """
    return Charges(text)[14]
def ConvictionCodes(text):
    """
    Return convictions codes as string from case text
    """
    return Charges(text)[15]
def ChargesString(text):
    """
    Return charges as string from case text
    """
    return Charges(text)[16]
