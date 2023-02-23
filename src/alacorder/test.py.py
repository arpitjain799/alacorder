# batcher test py py
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
import get #
import write #
import conf #
import parse
import logs
import PyPDF2
from io import StringIO
try:
    import xlsxwriter
except ImportError:
    pass

def batcher(conf):
	q = config.QUEUE
	if config.IS_FULL_TEXT: 
		batchsize = 2500
	else: 
		batchsize = 1000
	if config.FOUND < 1000:
		batchsize = 100
	if config.FOUND > 10000:
		batchsize = config.FOUND / 20
	batches = np.array_split(config.QUEUE, math.floor(config.FOUND/batchsize))
	return batches



a = config.inputs("/Users/samuelrobson/Desktop/Tutwiler2.pkl.xz")
print(a.ECHO)
b = config.outputs("/Users/samuelrobson/Desktop/Tutwiler3.pkl.xz")
print(b.ECHO)
# def set(inputs,outputs,count=0,table='',overwrite=False,append=True,launch=False,log=True,dedupe=False,warn=False,no_write=False,no_prompt=False,skip_echo=False)

c = config.set(a,b)
print(c.ECHO)

batcher(c)
