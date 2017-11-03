#cleanup
import xlrd
import pandas as pd
import re
import numpy as np
# import itertools

#Excel data file name
data_file_name = '06222016 Staph Array Data.xlsx'

#Function to parse Sample ID into 3 columns: PID, Visit and Dilution
def parse_sid(sample_id):
    words = re.split('\s+', sample_id.strip()) #Get all the words in the Sample ID string
    dilution = None #Initialize Dilution as None
    visit = None #Initialize Visit as None

    #Add the first word in the Sample ID string into PID\
    #This is to ensure the first word always be parsed as PID, \
    #even when it matches the pattern of visit or dilution
    pid = words.pop(0)

    #Loop through the rest of words to get Visit and Dilution info
    if len(words) > 0:
        for w in words:
            if re.match('V\d', w) and visit is None: #First check if match 'V\d'\
                #If visit is already assigned, skip
                visit = w #If yes, assign the word as Visit
            elif re.match('[1-9]0+',w) and dilution is None: #If not match Visit pattern,\
                #  match it to Dilution pattern of mutiple '0's after a digit
                dilution = w
            else:
                pid = pid + ' ' +w #If the word not matching Visit or Dilution, add it to PID

    return([pid, visit, dilution]) #Return the parsed 3 variables as list


sheets = pd.read_excel(data_file_name, sheetname=None, skiprows=0, header=1, na_values='NaN')
# for sh_name, df in sheets.items():
#     print(sh_name)

df = sheets['Plate 1']

#Remove white space and new line at the start and end of column names
df.columns = df.columns.str.strip()

#Map the function parse_sid to the column 'Sample ID' and \
#zip it into 3 new columns: PID, Visit and Dilution
df['PID'], df['Visit'], df['Dilution'] = zip(*df['Sample ID'].map(parse_sid))

#Re-arrange the columns that PID, Visit and Dilution are the first 3 columns
#The original Sample ID column is removed
cols = list(df.columns) #Get all column names as list
cols = cols[-3:] + cols[1:-3] #Re-arrange column names that it start with PID, Visit and Dilution, cols[0] dropped

#Fill the missing values in column Hospital, Age and Gender

#Get the first lines that has hospital, age and gender info for each PID
first_lines = df.loc[df.Hospital.notnull(), ['Age', 'Gender']]

#Replace empty age and gender as string 'NA'
df.loc[df.Hospital.notnull(), ['Age', 'Gender']] = first_lines.replace(np.nan, 'NA')

#Get the columns that need to filled with implied values
patient_info = df[['Hospital', 'Age', 'Gender']]

#Fill empty cells with previous row
df.loc[:, ['Hospital', 'Age', 'Gender']] = patient_info.fillna(method='ffill')

#Draw plots codes below
