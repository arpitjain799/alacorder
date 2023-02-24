# test.py
# Sam Robson

import get, parse, write, logs, config
import pandas as pd
import click

a = config.setpaths("/Users/samuelrobson/Desktop/NewTut.pkl.xz","/Users/samuelrobson/Desktop/Tutwiler2ElectricBoogaloo.csv",count=200,no_batch=True,table="fees",debug=True,log=True)

b = parse.cases(a)

