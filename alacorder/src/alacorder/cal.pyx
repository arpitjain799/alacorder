import re, fitz # requires PyMuPDF

def getPDFText(path: str) -> str:
     """
     From path, return full text of PDF as string (PyMuPdf engine required!)
     """
     try:
          doc = fitz.open(path)
     except:
          return ''
     text = ''
     for pg in doc:
          try:
               text += ' \n '.join(x[4].replace("\n"," ") for x in pg.get_text(option='blocks'))
          except:
               pass
     text = re.sub(r'(<image\:.+?>)','', text).strip()
     return text
def getName(text: str):
    try:
        return re.sub(r'Case Number:','',re.search(r'(?:VS\.|V\.| VS | V | VS: |-VS-{1})([A-Z\s]{10,100})(Case Number)*', str(text)).group(1)).rstrip("C").strip()
    except:
        return ''
def getAlias(text: str):
    try:
        return re.sub(r':','',re.search(r'(?:SSN)(.{5,75})(?:Alias)', str(text)).group(1)).strip()
    except:
        return ''
def getDOB(text: str):
    try:
        return re.sub(r'[^\d/]','',re.search(r'(\d{2}/\d{2}/\d{4})(?:.{0,5}DOB:)', str(text)).group(1)).strip()
    except:
        return ''
def getPhone(text: str):
    try:
        m = re.sub(r'[^0-9]','',re.search(r'(Phone: )(.+)', str(text)).group(2)).strip()
        if len(m) < 7:
            return ''
        elif m[0:10] == "2050000000":
            return ''
        elif len(m) > 10:
            return m[0:10]
    except:
        return ''
def getRace(text: str):
    try:
        return re.search(r'(B|W|H|A)/(F|M)', str(text)).group(1)
    except:
        return ''
def getSex(text: str):
    try:
        return re.search(r'(B|W|H|A)/(F|M)', str(text)).group(2)
    except:
        return ''
def getAddress1(text: str):
    try:
        return re.sub(r'Phone.+','',re.search(r'(?:Address 1:)(.+)(?:Phone)*?', str(text)).group(1)).strip()
    except:
        return ''
def getAddress2(text: str):
    try:
        return re.sub(r'Defendant Information|JID:.+','',re.search(r'(?:Address 2:)(.+)', str(text)).group(1).strip())
    except:
        return ''
def getCity(text: str):
    try:
        return re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(1)
    except:
        return ''
def getState(text: str):
    try:
        return re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(2)
    except:
        return ''
def getCountry(text: str):
    try:
        return re.sub(r'Country:','',re.sub(r'(Enforcement|Party|Country)','',re.search(r'Country: (\w*+)', str(text)).group()).strip())
    except:
        return ''
def getZipCode(text: str):
    try:
        return re.sub(r'-0000$|[A-Z].+','',re.search(r'(Zip: )(.+)', str(text)).group(2)).strip()
    except:
        return ''
def getAddress(text: str):
    try:
        street1 = re.sub(r'Phone.+','',re.search(r'(?:Address 1:)(.+)(?:Phone)*?',str(text)).group(1)).strip()
    except:
        street1 = ''
    try:
        street2 = getAddress2(text).strip()
    except:
        street2 = ''
    try:
        zipcode = re.sub(r'[A-Z].+','',re.search(r'(Zip: )(.+)',str(text)).group(2)).strip()
    except:
        zipcode = ''
    try:
        city = re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(1).strip()
    except:
        city = ''
    try:
        state = re.search(r'(?:City: )(.*)(?:State: )(.*)', str(text)).group(2).strip()
    except:
        state = ''
    if len(city)>3:
        return f"{street1} {street2} {city}, {state} {zipcode}".strip()
    else:
        return f"{street1} {street2} {city} {state} {zipcode}".strip()
def getChargesRows(text: str):
    m = re.findall(r'(\d{3}\s{1}[A-Z0-9]{4}.{1,200}?.{3}-.{3}-.{3}[^a-z\n]{10,75})', str(text))
    return m
def getFeeSheetRows(text: str):
    m = re.findall(r'(ACTIVE [^\(\n]+\$[^\(\n]+ACTIVE[^\(\n]+[^\n]|Total:.+\$[^A-Za-z\n]*)', str(text))
    return m
def getTotalRow(text: str):
    try:
        mmm = re.search(r'(Total:.+\$[^\n]*)', str(text)).group()
        mm = re.sub(r'[^0-9|\.|\s|\$]', '', str(mmm))
        m = re.findall(r'\d+\.\d{2}', str(mm))
        return m
    except:
        return ["0.00","0.00","0.00","0.00"]
def getTotalAmtDue(text: str):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[0]))
    except:
        return 0.00
def getTotalAmtPaid(text: str):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[1]))
    except:
        return 0.00
def getTotalBalance(text: str):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[2]))
    except:
        return 0.00
def getTotalAmtHold(text: str):
    try:
        return float(re.sub(r'[\$\s]','',getTotalRow(text)[3]))
    except:
        return 0.00
def getPaymentToRestore(text: str):
    try:
        tbal = getTotalBalance(text)
    except:
        return 0.0
    try:
        d999mm = re.search(r'(ACTIVE[^\n]+D999[^\n]+)',str(text)).group()
        d999m = re.findall(r'\$\d+\.\d{2}',str(d999mm))
        d999 = float(re.sub(r'[\$\s]','',d999m[-1]))
    except:
        d999 = 0.0
    return float(tbal - d999)
def getShortCaseNumber(text: str):
    try:
        return re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group()
    except:
        return ''
def getCounty(text: str):
    try:
        return re.search(r'Case Number: (\d\d-\w+) County:', str(text)).group(1)
    except:
        return ''
def getCaseNumber(text: str):
    try:
        return re.search(r'Case Number: (\d\d-\w+) County:', str(text)).group(1)[0:2] + "-" + re.search(r'(\w{2}\-\d{4}-\d{6}\.\d{2})', str(text)).group()
    except:
        return ''
def getCaseYear(text: str):
    try:
        return re.search(r'\w{2}\-(\d{4})-\d{6}\.\d{2}', str(text)).group(1)
    except:
        return ''
def getLastName(text: str):
    try:
        return getName(text).split(" ")[0].strip()
    except:
        return ''
def getFirstName(text: str):
    try:
        return getName(text).split(" ")[-1].strip()
    except:
        return ''
def getMiddleName(text: str):
    try:
        if len(getName(text).split(" ")) > 2:
            return " ".join(getName(text).split(" ")[1:-2]).strip()
        else:
            return ''
    except:
        return ''
def getRelatedCases(text: str):
    return re.findall(r'(\w{2}\d{12})',str(text))
def getFilingDate(text: str):
    try:
        return re.sub(r'Filing Date: ','',re.search(r'Filing Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group()).strip()
    except:
        return ''
def getCaseInitiationDate(text: str):
    try:
        return re.sub(r'Case Initiation Date: ','',re.search(r'Case Initiation Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group())
    except:
        return ''
def getArrestDate(text: str):
    try:
        return re.search(r'Arrest Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getOffenseDate(text: str):
    try:
        return re.search(r'Offense Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getIndictmentDate(text: str):
    try:
        return re.search(r'Indictment Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getYouthfulDate(text: str):
    try:
        return re.search(r'Youthful Date: (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getRetrieved(text: str):
    try:
        return re.search(r'Alacourt\.com (\d\d?/\d\d?/\d\d\d\d)', str(text)).group(1)
    except:
        return ''
def getCourtAction(text: str):
    try:
        return re.search(r'Court Action: (BOUND|GUILTY PLEA|WAIVED TO GJ|DISMISSED|TIME LAPSED|NOL PROSS|CONVICTED|INDICTED|DISMISSED|FORFEITURE|TRANSFER|REMANDED|WAIVED|ACQUITTED|WITHDRAWN|PETITION|PRETRIAL|COND\. FORF\.)', str(text)).group(1)
    except:
        return ''
def getCourtActionDate(text: str):
    try:
        return re.search(r'Court Action Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)
    except:
        return ''
def getDescription(text: str):
    try:
        return re.search(r'Charge: ([A-Z\.0-9\-\s]+)', str(text)).group(1).rstrip("C").strip()
    except:
        return ''
def getJuryDemand(text: str):
    try:
        return re.search(r'Jury Demand: ([A-Z]+)', str(text)).group(1).strip()
    except:
        return ''
def getInpatientTreatmentOrdered(text: str):
    try:
        return re.search(r'Inpatient Treatment Ordered: ([YES|NO]?)', str(text)).group(1).strip()
    except:
        return ''
def getTrialType(text: str):
    try:
        return re.sub(r'[S|N]$','',re.search(r'Trial Type: ([A-Z]+)', str(text)).group(1)).strip()
    except:
        return ''
def getJudge(text: str):
    try:
        return re.search(r'Judge: ([A-Z\-\.\s]+)', str(text)).group(1).rstrip("T").strip()
    except:
        return ''
def getProbationOfficeNumber(text: str):
    try:
        return re.sub(r'(0-000000-00)','',re.search(r'Probation Office \#: ([0-9\-]+)', str(text)).group(1).strip())
    except:
        return ''
def getDefendantStatus(text: str):
    try:
        return re.search(r'Defendant Status: ([A-Z\s]+)', str(text)).group(1).rstrip("J").strip()
    except:
        return ''
def getArrestingAgencyType(text: str):
    try:
        return re.sub(r'\n','',re.search(r'([^0-9]+) Arresting Agency Type:', str(text)).group(1)).strip()
    except:
        return ''
def getArrestingOfficer(text: str):
    try:
        return re.search(r'Arresting Officer: ([A-Z\s]+)', str(text)).group(1).rstrip("S").rstrip("P").strip()
    except:
        return ''
def getProbationOfficeName(text: str):
    try:
        return re.search(r'Probation Office Name: ([A-Z0-9]+)', str(text)).group(1).strip()
    except:
        return ''
def getTrafficCitationNumber(text: str):
    try:
        return re.search(r'Traffic Citation \#: ([A-Z0-9]+)', str(text)).group(1).strip()
    except:
        return ''
def getPreviousDUIConvictions(text: str):
    try:
        return int(re.search(r'Previous DUI Convictions: (\d{3})', str(text)).group(1).strip())
    except:
        return ''
def getCaseInitiationType(text: str):
    try:
        return re.search(r'Case Initiation Type: ([A-Z\s]+)', str(text)).group(1).rstrip("J").strip()
    except:
        return ''
def getDomesticViolence(text: str):
    try:
        return re.search(r'Domestic Violence: ([YES|NO])', str(text)).group(1).strip()
    except:
        return ''
def getAgencyORI(text: str):
    try:
        return re.search(r'Agency ORI: ([A-Z\s]+)', str(text)).group(1).rstrip("C").strip()
    except:
        return ''
def getDriverLicenseNo(text: str):
    try:
        m = re.search(r'Driver License N°: ([A-Z0-9]+)', str(text)).group(1).strip()
        if m == "AL":
            return ''
        else:
            return m
    except:
        return ''
def getSSN(text: str):
    try:
        return re.search(r'SSN: ([X\d]{3}\-[X\d]{2}-[X\d]{4})', str(text)).group(1).strip()
    except:
        return ''
def getStateID(text: str):
    try:
        m = re.search(r'([A-Z0-9]{11}?) State ID:', str(text)).group(1).strip()
        if m == "AL000000000":
            return ''
        else:
            return m
    except:
        return ''
def getWeight(text: str):
    try:
        return int(re.search(r'Weight: (\d+)', str(text)).group(1).strip())
    except:
        return ''
def getHeight(text: str):
    try:
        return re.search(r"Height : (\d'\d{2})", str(text)).group(1).strip() + "\""
    except:
        return ''
def getEyes(text: str):
    try:
        return re.search(r'Eyes/Hair: (\w{3})/(\w{3})',str(text)).group(1).strip()
    except:
        return ''
def getHair(text: str):
    try:
        return re.search(r'Eyes/Hair: (\w{3})/(\w{3})',str(text)).group(2).strip()
    except:
        return ''
def getCountry(text: str):
    try:
        return re.sub(r'(Enforcement|Party|Country:)','',re.search(r'Country: (\w*+)',str(text)).group(1).strip())
    except:
        return ''
def getWarrantIssuanceDate(text: str):
    try:
        return re.search(r'(\d\d?/\d\d?/\d\d\d\d) Warrant Issuance Date:',str(text)).group(1).strip()
    except:
        return ''
def getWarrantActionDate(text: str):
    try:
        return re.search(r'Warrant Action Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantIssuanceStatus(text: str):
    try:
        return re.search(r'Warrant Issuance Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantActionStatus(text: str):
    try:
        return re.search(r'Warrant Action Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getWarrantLocationStatus(text: str):
    try:
        return re.search(r'Warrant Location Status: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getNumberOfWarrants(text: str):
    try:
        return re.search(r'Number Of Warrants: (\d{3}\s\d{3})',str(text)).group(1).strip()
    except:
        return ''
def getBondType(text: str):
    try:
        return re.search(r'Bond Type: (\w)',str(text)).group(1).strip()
    except:
        return ''
def getBondTypeDesc(text: str):
    try:
        return re.search(r'Bond Type Desc: ([A-Z\s]+)',str(text)).group(1).strip()
    except:
        return ''
def getBondAmt(text: str):
    try:
        return float(re.sub(r'[^0-9\.\s]','',re.search(r'([\d\.]+) Bond Amount:',str(text)).group(1).strip()))
    except:
        return ''
def getSuretyCode(text: str):
    try:
        return re.search(r'Surety Code: ([A-Z0-9]{4})',str(text)).group(1).strip()
    except:
        return ''
def getBondReleaseDate(text: str):
    try:
        return re.search(r'Release Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getFailedToAppearDate(text: str):
    try:
        return re.search(r'Failed to Appear Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getBondsmanProcessIssuance(text: str):
    try:
        return re.search(r'Bondsman Process Issuance: ([^\n]*?) Bondsman Process Return:',str(text)).group(1).strip()
    except:
        return ''
def getBondsmanProcessReturn(text: str):
    try:
        return re.search(r'Bondsman Process Return: (.*?) Number of Subponeas',str(text)).group(1).strip()
    except:
        return ''
def getAppealDate(text: str):
    try:
        return re.sub(r'[\n\s]','',re.search(r'([\n\s/\d]*?) Appeal Court:',str(text)).group(1).strip())
    except:
        return ''
def getAppealCourt(text: str):
    try:
        return re.search(r'([A-Z\-\s]+) Appeal Case Number',str(text)).group(1).strip()
    except:
        return ''
def getOriginOfAppeal(text: str):
    try:
        return re.search(r'Orgin Of Appeal: ([A-Z\-\s]+)',str(text)).group(1).rstrip("L").strip()
    except:
        return ''
def getAppealToDesc(text: str):
    try:
        return re.search(r'Appeal To Desc: ([A-Z\-\s]+)',str(text)).group(1).rstrip("D").rstrip("T").strip()
    except:
        return ''
def getAppealStatus(text: str):
    try:
        return re.search(r'Appeal Status: ([A-Z\-\s]+)',str(text)).group(1).rstrip("A").strip()
    except:
        return ''
def getAppealTo(text: str):
    try:
        return re.search(r'Appeal To: (\w?) Appeal',str(text)).group(1).strip()
    except:
        return ''
def getLowerCourtAppealDate(text: str):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'LowerCourt Appeal Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)).strip()
    except:
        return ''
def getDispositionDateOfAppeal(text: str):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'Disposition Date Of Appeal: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1)).strip()
    except:
        return ''
def getDispositionTypeOfAppeal(text: str):
    try:
        return re.sub(r'[\n\s:\-]','',re.search(r'Disposition Type Of Appeal: [^A-Za-z]+',str(text)).group(1)).strip()
    except:
        return ''
def getNumberOfSubpoenas(text: str):
    try:
        return int(re.sub(r'[\n\s:\-]','',re.search(r'Number of Subponeas: (\d{3})',str(text)).group(1)).strip())
    except:
        return ''
def getAdminUpdatedBy(text: str):
    try:
        return re.search(r'Updated By: (\w{3})',str(text)).group(1).strip()
    except:
        return ''
def getTransferToAdminDocDate(text: str):
    try:
        return re.search(r'Transfer to Admin Doc Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getTransferDesc(text: str):
    try:
        return re.search(r'Transfer Desc: ([A-Z\s]{0,15} \d\d?/\d\d?/\d\d\d\d)',str(text)).group(1).strip()
    except:
        return ''
def getTBNV1(text: str):
    try:
        return re.search(r'Date Trial Began but No Verdict \(TBNV1\): ([^\n]+)',str(text)).group(1).strip()
    except:
        return ''
def getTBNV2(text: str):
    try:
        return re.search(r'Date Trial Began but No Verdict \(TBNV2\): ([^\n]+)',str(text)).group(1).strip()
    except:
        return ''
def getSentencingRequirementsCompleted(text: str):
    try:
        return re.sub(r'[\n:]|Requrements Completed','', ", ".join(re.findall(r'(?:Requrements Completed: )([YES|NO]?)',str(text))))
    except:
        return ''
def getSentenceDate(text: str):
    try:
        return re.search(r'(Sentence Date: )(\d\d?/\d\d?/\d\d\d\d)',str(text)).group(2).strip()
    except:
        return ''
def getProbationPeriod(text: str):
    try:
        return "".join(re.search(r'Probation Period: ([^\.]+)',str(text)).group(1).strip()).strip()
    except:
        return ''
def getLicenseSuspPeriod(text: str):
    try:
        return "".join(re.sub(r'(License Susp Period:)','',re.search(r'License Susp Period: ([^\.]+)',str(text)).group(1).strip()))
    except:
        return ''
def getJailCreditPeriod(text: str):
    try:
        return "".join(re.search(r'Jail Credit Period: ([^\.]+)',str(text)).group(1).strip())
    except:
        return ''
def getSentenceProvisions(text: str):
    try:
        return re.search(r'Sentence Provisions: ([Y|N]?)',str(text)).group(1).strip()
    except:
        return ''
def getSentenceStartDate(text: str):
    try:
        return re.sub(r'(Sentence Start Date:)','',", ".join(re.findall(r'Sentence Start Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getSentenceEndDate(text: str):
    try:
        return re.sub(r'(Sentence End Date:)','',", ".join(re.findall(r'Sentence End Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getProbationBeginDate(text: str):
    try:
        return re.sub(r'(Probation Begin Date:)','',", ".join(re.findall(r'Probation Begin Date: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getSentenceUpdatedBy(text: str):
    try:
        return re.sub(r'(Updated By:)','',", ".join(re.findall(r'Updated By: (\w{3}?)',str(text)))).strip()
    except:
        return ''
def getSentenceLastUpdate(text: str):
    try:
        return re.sub(r'(Last Update:)','',", ".join(re.findall(r'Last Update: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''
def getProbationRevoke(text: str):
    try:
        return re.sub(r'(Probation Revoke:)','',", ".join(re.findall(r'Probation Revoke: (\d\d?/\d\d?/\d\d\d\d)',str(text)))).strip()
    except:
        return ''

