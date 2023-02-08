import numpy as np
import pandas as pd
import xlrd
import openpyxl
import PyPDF2
import glob
import os
import sys
from io import StringIO
from math import floor
import alac
import re


c = alac.config("/Users/samuelrobson/Desktop/Tutwiler/","/Users/samuelrobson/Desktop/outputs.xls",save_archive=True)

alac.writeTables(c)