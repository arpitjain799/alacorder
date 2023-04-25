"""
 get.py

 ALACORDER 79
 ┌─┐┌─┐┬─┐┌┬┐┬ ┬┌┬┐┌─┐┬ ┬┌┐┌┌┬┐┌─┐┬┌┐┌
 ├─┘├─┤├┬┘ │ └┬┘││││ ││ ││││ │ ├─┤││││
 ┴  ┴ ┴┴└─ ┴  ┴ ┴ ┴└─┘└─┘┘└┘ ┴ ┴ ┴┴┘└┘
 (c) 2023 Sam Robson <sbrobson@crimson.ua.edu>

 Dependencies: 
    python = ^3.9
    pymupdf = ^1.21.1
    tqdm = ^4.65.0
"""


import fitz, re, glob


def get_paths(dirpath):
    """
    From path-like `dirpath`, return list of paths to pdfs in directory
    """
    return glob.glob(dirpath + "**/*.pdf", recursive=True)


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
            r"Date: Time Code Comments   Case Action Summary", "", wit.re.DOTALL
        )
        wit = re.sub(r"© Alacourt.com \d\d?/\d\d?/\d\d\d\d", "", wit.re.DOTALL)
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