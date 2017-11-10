import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import os

# Excel data file name
data_file_name = '06222016 Staph Array Data.xlsx'

# File contains columns to be plotted
layout_file_name = 'output-layout.txt'


# Function to parse Sample ID into 3 columns: PID, Visit and Dilution
def parse_sid(sample_id):
    words = re.split('\s+', sample_id.strip())  # Get all the words in the Sample ID string
    dilution = None  # Initialize Dilution as None
    visit = 'NA'  # Initialize Visit as 'NA'

    # Add the first word in the Sample ID string into PID\
    # This is to ensure the first word always be parsed as PID, \
    # even when it matches the pattern of visit or dilution
    pid = words.pop(0)

    # Loop through the rest of words to get Visit and Dilution info
    if len(words) > 0:
        for w in words:
            if re.match('[Vv]\d', w) and visit == 'NA':  # First check if match 'V\d'\
                # If visit is already assigned, skip
                visit = w.upper()  # If yes, assign the word as Visit, and capitalize 'v'
            elif re.match('[1-9]0+', w) and dilution is None:  # If not match Visit pattern,\
                #  match it to Dilution pattern of multiple '0's after a digit
                dilution = int(w)
            else:
                pid = pid + ' ' + w  # If the word not matching Visit or Dilution, add it to PID

    return [pid, visit, dilution]  # Return the parsed 3 variables as list

# Function to set the title for each of the plot
# in the format of PID(Gnder Age yr Hospital) Analyte
def set_plot_title(pid, pid_data, col_to_plot):

    if 'Gender' not in pid_data.columns or pid_data['Gender'].iloc[0] == '':  # If no Gender column or Gender is missing
        gender = ''  # Set gender as empty string
    else:
        gender = pid_data['Gender'].iloc[0].strip() + ' '  # If Gender is available assign it to gender, add space

    if 'Age' not in pid_data.columns or pid_data['Age'].iloc[0] == '':  # If no Age column or Gender is missing
        age = ''  # # Set age as empty string
    else:
        age = str(int(pid_data['Age'].iloc[0])) + ' yr '  # If Age is available assign it to age and add ' yr '

    if 'Hospital' not in pid_data.columns:  # # If no Hospital column
        hospital = ''
    else:
        hospital = pid_data['Hospital'].iloc[0].strip()

    if list(map(len, [gender, age, hospital])) == [0, 0, 0]:  #If data in Gender, Age, and Hospital all missing
        plot_title = pid + ' ' + col_to_plot  # Skip the part for patient info in title
    else:
        plot_title = '{}({}{}{}) {}'.format(pid, gender, age, hospital, col_to_plot)  # Generate proper title string

    return plot_title

# Function to make individual plot
# pid: Patient ID;
# pid_data: the data frame for one patient;
# col_to_plot: the name of the analyte;
# plot_fn: file name of the output plot
def plot_by_visit(pid, pid_data, col_to_plot, plot_fn):

    # Set the plot title
    plot_title = set_plot_title(pid, pid_data, col_to_plot)

    # Plot intensity of analyte with Visit as grouping
    pid_data.groupby('Visit')[col_to_plot].plot(marker='o', markerfacecolor='white')

    # Add lengend for the plot
    plt.legend(title='Visit')

    # Set proper x axis to make sure data points are not on the edge
    plt.xlim(min(pid_data.index) / 2, max(pid_data.index) * 2)

    # Plot in log scale
    plt.xscale('log')
    plt.yscale('log')

    # Add Y axis label
    plt.ylabel('Intensity')

    # Add plot title
    plt.title(plot_title)

    # Save figure
    plt.savefig(plot_fn)
    plt.close()

    print(plot_title + ' Done')


# Read in the variables that need to be plotted
cols_to_plot = []
with open(layout_file_name, 'r') as fh:
    for line in fh:
        cols_to_plot.extend(line.strip().split('\t'))

# Read all sheets in excel file, skip first line, define na as 'NaN'
sheets = pd.read_excel(data_file_name, sheetname=None, skiprows=0, header=1, na_values='NaN')

# Loop through each of the sheet in the excel file
for sheet_name, df in sheets.items():

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

        # Replace empty age and gender as empty string
        df.loc[df.Hospital.notnull(), ['Age', 'Gender']] = first_lines.replace(np.nan, '')

        # Get the columns that need to filled with implied values
        patient_info = df[['Hospital', 'Age', 'Gender']]

        # Fill empty cells with previous row
        df.loc[:, ['Hospital', 'Age', 'Gender']] = patient_info.fillna(method='ffill')

        # Replace the rest of np.nan as empty string
        df.loc[:, ['Hospital', 'Age', 'Gender']] = df[['Hospital', 'Age', 'Gender']].replace(np.nan, '')

        # Change string 'NA' to np.nan to keep consistency
        #df = df.replace('NA', np.nan)

    # Output formated dataframe to text file
    out_file_name = sheet_name + '.txt'
    df.to_csv(out_file_name, sep='\t', na_rep='', index=False)
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

        if any(pid_data.Dilution.notnull()):  # Only generate plot when there are Dilution information
            # Only plot the rows with Dilution information
            pid_data = pid_data[pid_data.Dilution.notnull()]
            # Set the Dilution as the index for the data frame
            pid_data.set_index('Dilution', inplace=True)

            # A loop for creating plots for each of the columns need to be plotted
            for col_to_plot in cols_to_plot:  # For loop through each of the analyte to be plotted
                if any(pid_data[col_to_plot].notnull()):  # Only plot when the column has values
                    # Set plot file name as sheet_name-PID-col_to_plot
                    plot_fn = '{}/{}-{}-{}.png'.format(plot_dir, sheet_name, pid, col_to_plot)

                    # Plot the graph
                    plot_by_visit(pid, pid_data, col_to_plot, plot_fn)
                else:
                    print('No data for ' + col_to_plot)
        else:
            print('No dilution information for ' + pid)
