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
required_packages = ['pgeocode', 'openpyxl', 'pandas','numpy','re','operator']

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
import operator
from difflib import get_close_matches

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

    def remap_column(self,df,column_name,map):
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
                    valid_list = list(set(map['valid_vals'].values()))
                    matched_val = get_close_matches(str(row[column_name]), valid_list, n=1, cutoff=.8)
                    if (matched_val):
                        row[column_name] = matched_val[0]
                        updated = True
                    elif 'valid_others' in map:
                        row[column_name] = map['valid_others']
                        updated = True

                if updated:
                    if 'save_orig' in map: 
                        if map['save_orig']['column_name'] in df.columns:
                            row[map['save_orig']['column_name']] = f"{row[map['save_orig']['column_name']]} - {column_name}: {original_value}"
                            #print(f"{map['save_orig']['column_name']} - being updated to {original_value}")
                        else:
                            raise Exception("Column not found in DF")
            else:
                if 'NaN_map' in map: 
                     row[column_name] = map['NaN_map']


            return row

        return df.apply(update_row, axis=1)  


    def load_db(self,url):
        df = pd.read_excel(url,sheet_name='PA Log Sheet')
        return df

    def replace_whitespace_with_nan(self,df):
        # Apply a function to each cell to check for whitespace or empty strings and replace with NaN
        df = df.map(lambda x: np.nan if isinstance(x, str) and x.strip() == '' else x)
        return df

    def trim_whitespace(self,df):
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
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

    def clean_currency_column(self, df, column_name):
        """
        Cleans up a currency column:
        - Removes dollar signs, commas, spaces, etc.
        - Converts to float
        - Handles missing or invalid values gracefully
        """
        if column_name not in df.columns:
            raise Exception(f"Column '{column_name}' not found in DataFrame")
        
        def clean_value(val):
            if pd.isna(val):
                return np.nan
            
            if bool(re.search(r'\d.*[a-zA-Z]|[a-zA-Z].*\d', str(val))):
                return np.nan  # Return NaN if mixed text and numbers\

            # Remove anything that is not a digit, period or minus sign
            val = re.sub(r'[^\d\.\-]', '', str(val))
            try:
                return float(val)
            except ValueError:
                return np.nan
        
        df[column_name] = df[column_name].apply(clean_value)
        return df

    def clean_and_convert_to_float(self, df, column_name):
        """
        Cleans up a column by:
        - Removing non-numeric characters (e.g., dollar signs, commas).
        - Converts the column values to float.
        - Handles invalid or missing values by converting them to NaN.
        """
        if column_name not in df.columns:
            raise Exception(f"Column '{column_name}' not found in DataFrame")
        
        def clean_value(val):
            if pd.isna(val):
                return np.nan

            if bool(re.search(r'\d.*[a-zA-Z]|[a-zA-Z].*\d', str(val))):
                return np.nan  # Return NaN if mixed text and numbers

            # Remove any non-numeric characters except for decimal point and minus sign
            val = re.sub(r'[^\d\.\-]', '', str(val))
            try:
                return float(val)
            except ValueError:
                return np.nan
        
        df[column_name] = df[column_name].apply(clean_value)
        return df

    def clean_datafile(self,df):
        df = df.replace(r'(?i)^missing$', np.nan, regex=True)
        df = df.replace(r'(?i)^yes$', 'Yes', regex=True)
        df = df.replace(r'(?i)^no$', 'No', regex=True)
        df = self.replace_whitespace_with_nan(df)
        df = self.trim_whitespace(df)

        df['Patient ID#'] = df['Patient ID#'].astype(int)
        df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'])
        df['App Year'] = df['App Year'].astype(int)
        df['Remaining Balance'] = df['Remaining Balance'].astype(float,2)
                
        valid_requst_status = ['Approved', 'Pending', 'Denied']
        df = self.validate_values(df,'Request Status',valid_requst_status)

        payment_map = {
            'valid_vals' : {
                r'(?i)Yes': 'Yes',
                r'(?i)no': 'No'
            },
            'date_ref': 'Yes',
            'NaN_map': 'Missing',
            'save_orig': {
                'column_name' : 'Notes'
            }
        }
        df = self.remap_column(df,'Payment Submitted?',payment_map)


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
            'valid_others': 'other',
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Payment Method',payment_type_map)


        language_map ={
            'valid_vals': {
                r'(?i)english': 'English',
                r'(?i)spanish': 'Spanish'
            },
            'valid_others': 'other',
            'NaN_map': 'Missing',            
            'save_orig': {
                'column_name' : 'Notes'
            }

        }
        df = self.remap_column(df,'Language',language_map)
        
        marital_status_map ={
            'valid_vals': {
                r'(?i)Single': 'Single',
                r'(?i)Married': 'Married',
                r'(?i)Divorced': 'Divorced',
                r'(?i)Separated': 'Separated',
                r'(?i)Domestic Partnership': 'Domestic Partnership'
            },
            'valid_others': 'other',
            'NaN_map': 'Missing'

        }
        df = self.remap_column(df,'Marital Status',marital_status_map)

        gender_map ={
            'valid_vals': {
                r'(?i)Male': 'Male',
                r'(?i)Female': 'Female',
                r'(?i)Transgender Male': 'Transgender Male',
                r'(?i)Non-Binary': 'Non-Binary',
                r'(?i)Another Gender Identity': 'Another Gender Identity',
                r'(?i)Decline to Answer': 'Decline to Answer'
            },
            'valid_others': 'other',
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Gender',gender_map)

        race_ethnicity_map = {
            'valid_vals': {
                r'(?i)American Indian or Alaskan Native': 'American Indian or Alaskan Native',
                r'(?i)American Indian or Alaksa Native': 'American Indian or Alaskan Native',
                r'(?i)American Indian or Alaska Native': 'American Indian or Alaskan Native',
                r'(?i)Asian': 'Asian',
                r'(?i)Black or African American': 'Black or African American',
                r'(?i)Native Hawaiian or Other Pacific Islander': 'Native Hawaiian or Other Pacific Islander',
                r'(?i)White': 'White',
                r'(?i)Whiate': 'White',
                r'(?i)Decline to Answer': 'Decline to Answer',
                r'(?i)Two or more races': 'Two or more races',
            },
            'valid_others': 'other',
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Race',race_ethnicity_map)

        hispanic_map= {
            'valid_vals': {
                r'(?i)^No$': 'No',
                r'(?i)^Yes$': 'Yes',
                r'(?i)^Non-Hispanic or Latino$': 'No',
                r'(?i)^Non-Hispanic$': 'No',
                r'(?i)^Non-hispanic latino$': 'No',
                r'(?i)^Decline to answer$': 'Decline to Answer',
                r'(?i)^Hispanic or Latino$': 'Yes',
                r'(?i)^Hispanic of Latino$': 'Yes',
            },
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Hispanic/Latino',hispanic_map)


        sexual_orientation_map = {
            'valid_vals': {
                r'(?i)^Heterosexual$': 'Straight',
                r'(?i)^Straight$': 'Straight',
                r'(?i)^Stright$': 'Straight',
                r'(?i)^Staight$': 'Straight',
                r'(?i)^Striaght$': 'Straight',
                r'(?i)^straight$': 'Straight',
                r'(?i)^Male$': 'Straight',
                r'(?i)^Female$': 'Straight',
                r'(?i)^Decline to answer$': 'Decline to Answer',
                r'(?i)^Decline$': 'Decline to Answer',
                r'(?i)^Gay or lesbian$': 'Gay or Lesbian',
                r'(?i)^Queer$': 'Queer',
                r'(?i)^Bisexual$': 'Bisexual',
                r"(?i)^I don't know$": "I don't know",
                r'(?i)^Something else': 'Something else'
            },
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Sexual Orientation',sexual_orientation_map)


        insurance_type_map = {
            'valid_vals': {
                r'(?i)^Uninsured$': 'Uninsured',
                r'(?i)^Uninsurred$': 'Uninsured',
                r'(?i)^Unisured$': 'Uninsured',
                r'(?i)^Medicare$': 'Medicare',
                r'(?i)^MEdicare$': 'Medicare',
                r'(?i)^Medicaid$': 'Medicaid',
                r'(?i)^medicaid$': 'Medicaid',
                r'(?i)^Medicare & Medicaid$': 'Medicare & Medicaid',
                r'(?i)^Medicaid & Medicare$': 'Medicare & Medicaid',
                r'(?i)^Medicare & Other$': 'Medicare & Other',
                r'(?i)^Medicare & Private$': 'Medicare & Private',
                r'(?i)^Private$': 'Private',
                r'(?i)^Military Program$': 'Military Program',
                r'(?i)^Heathcare.gov$': 'Unknown',
                r'(?i)^Unknown$': 'Unknown',
            },
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Insurance Type',insurance_type_map)

        df['Household Size'] = df['Household Size'].astype('Int64')

        df = self.clean_currency_column(df,'Total Household Gross Monthly Income')
        df['Total Household Gross Monthly Income'] = df['Total Household Gross Monthly Income'].astype('Float64')

        df = self.clean_and_convert_to_float(df, 'Distance roundtrip/Tx')
        df['Distance roundtrip/Tx'] = df['Distance roundtrip/Tx'].astype('Float64')

        expense_category_map = {
            'valid_vals': {
                r'(?i)^Medical Supplies/Prescription Co-pay(s)$': 'Medical Supplies/Prescription Co-pay(s)',
                r'(?i)^Food/Groceries$': 'Food/Groceries',
                r'(?i)^Gas$': 'Gas',
                r'(?i)^Other$': 'Other',
                r'(?i)^Hotel$': 'Hotel',
                r'(?i)^Housing$': 'Housing',
                r'(?i)^Utilities$': 'Utilities',
                r'(?i)^Car Payment$': 'Car Payment',
                r'(?i)^Phone/Internet$': 'Phone/Internet',
                r'(?i)^utilities$': 'Utilities'  # Standardize "utilities" case
            },
            'valid_others': 'Other'
        }
        df = self.remap_column(df,'Type of Assistance (CLASS)',expense_category_map)

        df = self.clean_and_convert_to_float(df, 'Amount') 

        patient_notification_map ={
            'valid_vals': {
                r'(?i)Yes': 'Yes',
                r'(?i)no': 'No',
                r'(?i)na': 'No',
                r'(?i)HOLD': 'No'
            },
            'date_ref': 'Yes'
        }
        df = self.remap_column(df,'Patient Letter Notified? (Directly/Indirectly through rep)',patient_notification_map)

        application_signed_map ={
            'valid_vals': {
                r'(?i)Yes': 'Yes',
                r'(?i)no': 'No',
                r'(?i)na': 'No'
            },
            'date_ref': 'Yes',
            'NaN_map': 'Missing'
        }
        df = self.remap_column(df,'Application Signed?',application_signed_map)

        return df

    def __init__(self,url):
        self.nomi = pgeocode.Nominatim('us')
        self.database_orig = self.load_db(url)
        self.database_clean = self.clean_datafile(self.database_orig)


    def subset_df(self, column, condition, op='=='):
        """
        Return the rows of df where df[column] meets the given condition.

        Parameters
        ----------
        df : pandas.DataFrame
        column : str
            The column to test.
        condition : scalar or callable
            • If scalar: compare df[column] to this value using operator `op`.
            • If callable: should accept a Series and return a boolean Series.
        op : str, one of ['==','!=','>','>=','<','<='], default '=='
            The comparison operator to use when condition is a scalar.

        Returns
        -------
        pandas.DataFrame
            Subset of df where the condition holds.
        """
        df = self.database_clean
        # If user passed a function, just apply it
        if callable(condition):
            mask = condition(df[column])
        else:
            # map operator string to actual function
            ops = {
                '==': operator.eq,
                '!=': operator.ne,
                '>':  operator.gt,
                '>=': operator.ge,
                '<':  operator.lt,
                '<=': operator.le,
            }
            if op not in ops:
                raise ValueError(f"Unsupported operator {op!r}, choose from {list(ops)}")
            mask = ops[op](df[column], condition)
        
        return df.loc[mask]

    # def __repr__(self):
    #     print(self.database)


url="./UNO Service Learning Data Sheet De-Identified Version.xlsx"
db = hopeFoundationCancerDatabase(url)
data_o = db.database_orig
data_c = db.database_clean