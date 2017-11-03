#cleanup


import xlrd
import pandas as pd
import re
import numpy as np
# import itertools

#Excel data file name
data_file_name = '06222016 Staph Array Data.xlsx'

# sheets = pd.read_excel(data_file_name, sheetname=None, skiprows=0, header=1, na_values='NaN')
# for sh_name, df in sheets.items():
#     print(sh_name)
#
# df = sheets['Plate 1']


def parse_sid(sample_id):
    words = re.split('\s+', sample_id.strip())
    dilution = None
    visit = None
    pid = words.pop(0)

    if len(words) > 0:
        for w in words:
            if re.match('V\d', w) and visit is None:
                visit = w
            elif re.match('[1-9]0+',w) and dilution is None:
                dilution = w
            else:
                pid = pid + ' ' +w

    return([pid, visit, dilution])

sample_id = "100000  vessfdf 10   "
print(parse_sid(sample_id))
