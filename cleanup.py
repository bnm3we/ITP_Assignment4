import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import os

# Excel data file name
data_file_name = '06222016 Staph Array Data.xlsx'
layout_file_name = 'output-layout.txt'


# Function to parse Sample ID into 3 columns: PID, Visit and Dilution
def parse_sid(sample_id):
    words = re.split('\s+', sample_id.strip())  # Get all the words in the Sample ID string
    dilution = None  # Initialize Dilution as None
    visit = None  # Initialize Visit as None

    # Add the first word in the Sample ID string into PID\
    # This is to ensure the first word always be parsed as PID, \
    # even when it matches the pattern of visit or dilution
    pid = words.pop(0)

    # Loop through the rest of words to get Visit and Dilution info
    if len(words) > 0:
        for w in words:
            if re.match('[Vv]\d', w) and visit is None:  # First check if match 'V\d'\
                # If visit is already assigned, skip
                visit = w  # If yes, assign the word as Visit
            elif re.match('[1-9]0+', w) and dilution is None:  # If not match Visit pattern,\
                #  match it to Dilution pattern of mutiple '0's after a digit
                dilution = int(w)
            else:
                pid = pid + ' ' + w  # If the word not matching Visit or Dilution, add it to PID

    return ([pid, visit, dilution])  # Return the parsed 3 variables as list

# Read in the variables that need to be plotted
cols_to_plot = []
with open(layout_file_name, 'r') as fh:
    for line in fh:
        cols_to_plot.extend(line.strip().split('\t'))

# Read all sheets in excel file, skip first line, define na as 'NaN'
sheets = pd.read_excel(data_file_name, sheetname=None, skiprows=0, header=1, na_values='NaN')

for sheet_name, df in sheets.items():

    sheet_name = 'Plate 1'
    df = sheets['Plate 1']

    # Remove white space and new line at the start and end of column names
    df.columns = df.columns.str.strip()

    # Map the function parse_sid to the column 'Sample ID' and \
    # zip it into 3 new columns: PID, Visit and Dilution
    df['PID'], df['Visit'], df['Dilution'] = zip(*df['Sample ID'].map(parse_sid))

    # Re-arrange the columns that PID, Visit and Dilution are the first 3 columns
    # The original Sample ID column is removed
    column_names = list(df.columns)  # Get all column names as list
    # Re-arrange column names that it start with PID, Visit and Dilution, original 'Sample ID' dropped
    column_names = column_names[-3:] + column_names[1:-3]
    df = pd.DataFrame(df[column_names])

    # Fill the missing values in column Hospital, Age and Gender
    if 'Hospital' in df.columns:
        # Get the lines with hospital value, these are the first row for each patient
        first_lines = df.loc[df.Hospital.notnull(), ['Age', 'Gender']]

        # Replace empty age and gender as empty string 'NA'
        df.loc[df.Hospital.notnull(), ['Age', 'Gender']] = first_lines.replace(np.nan, 'NA')

        # Get the columns that need to filled with implied values
        patient_info = df[['Hospital', 'Age', 'Gender']]

        # Fill empty cells with previous row
        df.loc[:, ['Hospital', 'Age', 'Gender']] = patient_info.fillna(method='ffill')

        # Change string 'NA' to np.nan to keep consistency
        df = df.replace('NA', np.nan)

    # Output formated dataframe to text file
    out_file_name = sheet_name + '.txt'
    df.to_csv(out_file_name, sep='\t', na_rep=np.nan, index=False)
    print(out_file_name + ' is complete.')


    # Draw plots codes below

    # Create a directory for all plots of the plate with the name of the plate if not exist
    plot_dir = sheet_name
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Split the data frame by patient ID
    pid_groups = df.groupby('PID')

    # A loop to loop through each of the patient ID
    for pid in pid_groups.groups.keys():  # pid_groups.groups is dictionary with PID as keys
        # Get the data of specific PID
        pid_data = pid_groups.get_group(pid)
        # Set the Dilution as the index for the data frame
        pid_data.set_index('Dilution', inplace=True)

        # Make first part of plot title string
        gender = str(list(pid_data['Gender'])[0])
        age = str(int(list(pid_data['Age'])[0]))
        hospital = str(list(pid_data['Hospital'])[0])
        plot_title_pre = '{}({} {} yr {})'.format(pid, gender, age, hospital)

        # A loop for creating plots for each of the columns need to be plotted
        for col_to_plot in cols_to_plot:
            # Set plot file name as sheet_name-PID-col_to_plot
            plot_fn = '{}/{}-{}-{}.png'.format(plot_dir, sheet_name, pid, col_to_plot)

            # Add the analyte name to the end of plot title
            plot_title = plot_title_pre + ' ' + col_to_plot

            pid_data.groupby('Visit')[col_to_plot].plot(marker='o', markerfacecolor='white')
            plt.xlim(min(pid_data.index)/2, max(pid_data.index)*2)
            plt.xscale('log')
            plt.yscale('log')
            plt.legend(title='Visit')
            plt.ylabel('Intensity')
            plt.title(plot_title)
            plt.savefig(plot_fn)
            plt.close()

