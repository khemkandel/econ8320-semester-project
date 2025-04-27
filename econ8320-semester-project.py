#pip install openpyxl
#pip install pgeocode
import subprocess
import sys

# Show all rows
#pd.set_option('display.max_rows', None)

# (optional) Show all columns too
#pd.set_option('display.max_columns', None)
#pd.set_option('future.no_silent_downcasting', True)


# List of required packages
required_packages = ['pgeocode', 'openpyxl', 'pandas','numpy','re']

# Function to install missing packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check and install if needed
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing missing package: {package}")
        install(package)



import pandas as pd
import numpy as np
import pgeocode
import re

class hopeFoundationCancerDatabase(object):

    def clean_zip(self,zip_code):
        #nomi = pgeocode.Nominatim('us')
        if pd.isna(zip_code):
            return np.nan
        zip_code = re.sub(r'\D', '', str(zip_code))  # remove non-digit
        zip_code = zip_code[:5]  # keep first 5 digits
        if len(zip_code) == 5:
            zip_info = self.nomi.query_postal_code(zip_code)
            if pd.isna(zip_info.state_name):  # check state_name properly
                return np.nan
            else:
                return zip_code
        else:
            return np.nan

    def clean_payment_method(self,df):

        payment_map = {
            r'(?i)check': 'CK',
            r'(?i)ck': 'CK',
            r'(?i)gc': 'GC',
            r'(?i)cc': 'CC',
            r'(?i)EFT': 'CK',
            r'(?i)ACH': 'CK'

        }

        def update_pm_notes(row):
            original_value = row['Payment Method']
            # Loop through the mapping and check for matches
            if (not pd.isna(original_value)):
                row['Payment Method'] = 'other'
                for pattern, value in payment_map.items():
                    if re.search(pattern, str(original_value)):
                        row['Payment Method'] = value
                        row['Notes'] = f"{row['Notes']} - {original_value}"
                        break  # Stop once a match is found
                   
            return row

        return df.apply(update_pm_notes, axis=1)       

    def remap_column(self,df,map,column_name):
        if (not isinstance(map, dict)):
            raise Exception("Not a dictionary")
        if ( not column_name in df.columns):
            raise Exception("Column not found in DF")

        
        def update_row(row):
            original_value = row[column_name]
            updated = False
            if (not pd.isna(original_value)):
                if 'date_ref' in map:
                    if pd.to_datetime(row[column_name], errors='coerce') is not pd.NaT:
                        row[column_name] = map['date_ref']
                        updated = True

                for pattern, value in map['valid_vals'].items():
                    if re.search(pattern, str(row[column_name])):
                        row[column_name] = value
                        updated = True
                        break  # Stop once a match is found
                if not updated:
                    if 'valid_others' in map:
                        row[column_name] = map['valid_others']
                        updated = True

                if updated:
                    if 'save_orig' in map: 
                        if map['save_orig']['column_name'] in df.columns:
                            row[column_name] = f"{row[column_name]} - {original_value}"

            return row

        return df.apply(update_row, axis=1)  



    def clean_patient_letter_notified(self,df):

        payment_map = {
            r'(?i)Yes': 'Yes',
            r'(?i)no': 'No',
            r'(?i)na': 'No',
            r'(?i)HOLD': 'No'
        }
        
    
        def update_patient_letter_notified(row):
            original_value = row['Patient Letter Notified? (Directly/Indirectly through rep)']
            # Loop through the mapping and check for matches
            if (not pd.isna(original_value)):
                if pd.to_datetime(row['Patient Letter Notified? (Directly/Indirectly through rep)'], errors='coerce') is not pd.NaT:
                    row['Patient Letter Notified? (Directly/Indirectly through rep)'] = 'Yes'
                else:
                    for pattern, value in payment_map.items():
                        if re.search(pattern, str(original_value)):
                            row['Patient Letter Notified? (Directly/Indirectly through rep)'] = value
                            break  # Stop once a match is found
                   
            return row

        return df.apply(update_patient_letter_notified, axis=1)  


    def load_db(self,url):
        df = pd.read_excel(url,sheet_name='PA Log Sheet')
        return df

    def replace_whitespace_with_nan(self,df):
        # Apply a function to each cell to check for whitespace or empty strings and replace with NaN
        df = df.apply(lambda x: np.nan if isinstance(x, str) and x.strip() == '' else x)
        return df

    def validate_values(self,df, column_name, valid_values):
        """
        Replaces values not in valid_values with NaN for a specific column in a DataFrame.
        
        Parameters:
        - df: DataFrame
        - column_name: Name of the column to validate
        - valid_values: List of allowed values
        """
        df[column_name] = df[column_name].apply(lambda x: x if x in valid_values else np.nan)
        return df

    def clean_datafile(self,df):
        df = df.replace(r'(?i)missing', np.nan, regex=True)
        df = df.replace(r'(?i)yes', 'Yes', regex=True)
        df = df.replace(r'(?i)no', 'No', regex=True)
        df = self.replace_whitespace_with_nan(df)
        df['Patient ID#'] = df['Patient ID#'].astype(int)
        df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'])
        df['App Year'] = df['App Year'].astype(int)
        df['Remaining Balance'] = df['Remaining Balance'].astype(float,2)
                
        valid_requst_status = ['Approved', 'Pending', 'Denied']
        df = self.validate_values(df,'Request Status',valid_requst_status)
        #df['Request Status'] = df['Request Status'].where(df['Request Status'].isin(valid_requst_status))

        payment_map = {
            'valid_vals' : {
                r'(?i)Yes': 'Yes',
                r'(?i)no': 'No'
            },
            'date_ref': 'Yes',
            'save_orig': {
                'column_name' : 'notes'
            }
        }
        #df['Payment Submitted?'] = df['Payment Submitted?'].apply(lambda x: 'yes' if str(x).lower() == 'yes' or pd.to_datetime(x, errors='coerce') is not pd.NaT else 'no')
        df = self.remap_column(df,payment_map,'Payment Submitted?')


        df['Pt Zip'] =  df['Pt Zip'].apply(self.clean_zip)

        payment_type_map = {
            'valid_vals': {
                r'(?i)check': 'CK',
                r'(?i)ck': 'CK',
                r'(?i)gc': 'GC',
                r'(?i)cc': 'CC',
                r'(?i)EFT': 'CK',
                r'(?i)ACH': 'CK'
            },
            'valid_others': 'other'
        }
        df = self.remap_column(df,payment_type_map,'Payment Method')
        #df = self.clean_payment_method(df)

        df = self.clean_patient_letter_notified(df)

        return df

    def __init__(self,url):
        self.nomi = pgeocode.Nominatim('us')
        self.database_orig = self.load_db(url)
        self.database_clean = self.clean_datafile(self.database_orig)


    # def __repr__(self):
    #     print(self.database)


url="./UNO Service Learning Data Sheet De-Identified Version.xlsx"
db = hopeFoundationCancerDatabase(url)
data_o = db.database_orig
data_c = db.database_clean