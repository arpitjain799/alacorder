import os
import sys
import re, regex
import alac
import PyPDF2
import pandas as pd

a = alac.config("/Users/samuelrobson/Desktop/Tutwiler.pkl.xz", max_cases=2000)
b = pd.DataFrame()
pd.set_option('display.width', 2000)

c = pd.read_pickle("/Users/samuelrobson/Desktop/pickleC.pkl")

# print(c.tolist())

def getCaseActionSummary(text):
	text = pd.Series([text]).str.normalize('NFC')[0]
	if bool(re.search(r'(\nOperator\n){1}(.{100,}?)(Images){1}', text.strip(), [re.DOTALL, re.MULTILINE]__init__)):
		portion = pd.Series(re.search(r'(\nOperator\n){1}(.{100,}?)(Images){1}', text.strip(), re.DOTALL).group(2))
		CASRows = portion.str.split("\n")
		print(CASRows.to_string())
		return CASRows


b = alac.parse(a, getCaseActionSummary)

b.to_pickle("/Users/samuelrobson/Desktop/todayisthursday.pkl")