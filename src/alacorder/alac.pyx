# alac 6 - c extension library
import cython
import pyximport; pyximport.install()
import os
import sys
from io import StringIO
import glob
import re
import xlrd
import openpyxl
import math
import datetime
import pandas as pd
import numpy as np
import PyPDF2 as pypdf


def getPDFText(path: str) -> str:
	text = ""
	pdf = pypdf.PdfReader(path)
	for pg in pdf.pages:
		text += pg.extract_text()
	return text

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
 
	if bool(re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE)) == True:
		name = re.search(r'(?a)(VS\.|V\.{1})(.+)(Case)*', text, re.MULTILINE).group(2).replace("Case Number:","").strip()
	else:
		if bool(re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE)) == True:
			name = re.search(r'(?:DOB)(.+)(?:Name)', text, re.MULTILINE).group(1).replace(":","").replace("Case Number:","").strip()
	if bool(re.search(r'(SSN).{5,75}?(Alias)',text, re.MULTILINE)) == True:
		alias = re.search(r'(SSN)(.{5,75})(Alias)?', text, re.MULTILINE).group(2).replace(":","").replace("Alias 1","").strip()
	else:
		pass
	try:
		dob: str = re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB\:)', str(text), re.DOTALL).group(1)
		phone: str = re.search(r'(?:Phone\:)(.*?)(?:Country)', str(text), re.DOTALL).group(1).strip()
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
		street_addr = re.search(r'(Address 1\:)(.+)', str(text), re.MULTILINE).group(2).strip()
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
	case = [case_num, name, alias, dob, race, sex, address, phone]
	return case

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

		feesheet = pd.DataFrame({
			'CaseNumber': cnum,
			'Total': '',
			'Code': coderows.tolist(),
			'Payor': payorrows.tolist(),
			'AmtDue': amtduerows.tolist(),
			'AmtPaid': amtpaidrows.tolist(),
			'Balance': balancerows.tolist(),
			'AmtHold': amtholdrows.tolist()
			})

		totalrdf = {
			'Total': 'TOTAL',
			'CaseNumber': cnum,
			'Code': '',
			'Payor': '',
			'AmtDue': tdue,
			'AmtPaid': tpaid,
			'Balance': tbal,
			'AmtHold': thold
		}


		feesheet = feesheet.append(totalrdf, ignore_index=True)

		try:
			d999 = feesheet[feesheet['Code']=='D999']['Balance']
		except (TypeError, IndexError):
			d999 = ""

		owe_codes = " ".join(feesheet['Code'][feesheet.Balance.str.len() > 0])
		codes = " ".join(feesheet['Code'])
		allrows = actives
		allrows.append(totalrow)
		allrowstr = "\n".join(allrows)
		return [tdue, tbal, d999, owe_codes, codes, allrowstr, feesheet]

def getCharges(text: str, cnum: str):
	# get all charges matches
	ch = re.findall(r'(\d{3}\s{1}.{1,100}?.{3}-.{3}-.{3}.{10,75})', str(text), re.MULTILINE)
	c = []
	for a in ch:
		b = str(a).replace("Sentences","").replace("Sentence 1","").replace("SentencesSentence 1","").replace("Sentence","").replace("Financial","")
		if b[-2:] == " 1" or b[-2:] == " 0":
			b = b.replace(" 1","").replace(" 0","").strip()
		if ":" in b:
			continue
		c.append(re.sub(r'[a-z]*','', b))
	cind = range(0, len(c))
	charges = pd.DataFrame({'Charges': c,'parentheses':'','decimals':''},index=cind)
	charges['CaseNumber'] = charges.index.map(lambda x: cnum)
	# find table fields
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
	charges['CourtActionDate'] = charges['Charges'].map(lambda x: re.search(r'\d{2}/\d{2}/\d{4}', x).group() if bool(re.search(r'\d{2}/\d{2}/\d{4}', x)) else "")
	charges['CourtAction'] = charges['Charges'].map(lambda x: re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x).group() if bool(re.search(r'(BOUND|GUILTY PLEA|PROBATION|WAIVED|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|OTHER|DISMISSED|FORFEITURE|TRANSFER|REMANDED|PROBATION|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', x)) else "")

	try:
		charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'([^\s]{3}-[^\s]{3}-[^\s]{3}[^s]{0,3}?\)*)', x).group())
	except (AttributeError, IndexError):
		try:
			charges['Cite'] = charges['Charges'].map(lambda x: re.search(r'(.{3}-.{3}-.{3})',x).group())
		except (AttributeError, IndexError):
			pass
	try:
		charges['parentheses'] = charges['Charges'].map(lambda x: re.search(r'(\([A-Z]\))', x).group())
		charges['Cite'] = charges['Cite'] + charges['parentheses']
	except (AttributeError, IndexError):
		pass
	try:
		charges['decimals'] = charges['Charges'].map(lambda x: re.search(r'(\.[0-9])', x).group())
		charges['Cite'] = charges['Cite'] + charges['decimals']
	except (AttributeError, IndexError):
		pass

	charges['TypeDescription'] = charges['Charges'].map(lambda x: re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x).group() if bool(re.search(r'(BOND|FELONY|MISDEMEANOR|OTHER|TRAFFIC|VIOLATION)', x)) else "")
	charges['Category'] = charges['Charges'].map(lambda x: re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x).group() if bool(re.search(r'(ALCOHOL|BOND|CONSERVATION|DOCKET|DRUG|GOVERNMENT|HEALTH|MUNICIPAL|OTHER|PERSONAL|PROPERTY|SEX|TRAFFIC)', x)) else "")
	charges['Description'] = charges['Charges'].map(lambda x: x[9:-1])
	charges['Description'] = charges['Description'].str.split(r'([^s]{3}-.{3}-.{3})', regex=True)
	charges['Description'] = charges['Description'].map(lambda x: x[2].strip() if bool(re.search(r'(\d{2}/\d{2}/\d{4})|\#|MISDEMEANOR|WAIVED|DISMISSED|CONVICTED|PROSS', x[0])) else ascii(x[0]).strip())
	charges['Description'] = charges['Description'].map(lambda x: x.replace("\'","").strip())
	charges.drop(columns=['PardonCode','PermanentCode','CERVCode','VRRexception','parentheses','decimals'], inplace=True)

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

