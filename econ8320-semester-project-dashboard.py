
# Allows you to control what you see on Termial for Prompt PATH
#   function prompt { "$(Split-Path -Leaf (Get-Location))> " }
# Command to Run Steamlit
#   python -m streamlit run .\econ8320-semester-project.py
# Show all rows
# pd.set_option('display.max_rows', None)
# (optional) Show all columns too
# pd.set_option('display.max_columns', None)
# pd.set_option('future.no_silent_downcasting', True)

# Modules needed for Installing new packages
# If this is ran manually, below modules installs required modules
import subprocess
import sys

# List of required packages
required_packages = ['pgeocode', 'openpyxl', 'pandas','numpy','re','operator','streamlit','datetime','pyarrow','streamlit_option_menu']

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


#### Import Requied Modules
##--------------------------
import pandas as pd
import numpy as np
import pgeocode
import re
import operator
from difflib import get_close_matches
import streamlit as st
from datetime import datetime
from streamlit_option_menu import option_menu
import plotly.express as px




# Function that allows you to get the subset of a table 
#-----------------------------------------------------------

def subset_df(df, column, condition, op='=='):
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
    op : str, one of ['==','!=','>','>=','<','<=','isna','notna'], default '=='
        The comparison operator to use when condition is a scalar.

    Returns
    -------
    pandas.DataFrame
        Subset of df where the condition holds.
    """
   
    if callable(condition):
        mask = condition(df[column])
    else:
        # operator mapping
        ops = {
            '==': operator.eq,
            '!=': operator.ne,
            '>':  operator.gt,
            '>=': operator.ge,
            '<':  operator.lt,
            '<=': operator.le,
            'isna': pd.Series.isna,
            'notna': pd.Series.notna,
        }

        if op not in ops:
            raise ValueError(f"Unsupported operator {op!r}, choose from {list(ops)}")

        if op in ['isna', 'notna']:
            mask = ops[op](df[column])  # no condition needed
        else:
            mask = ops[op](df[column], condition)

    return df.loc[mask]



# Function to manage Streamlit Custom Headers. St.Header provides limited functionality to 
# change text, alignment, color , font size. With this function all that can be managed
#---------------------------------------------------------

def custom_header(text, size=20, weight='normal', color='#000000',align='left', icon=None):
    """
    Display a custom styled header in Streamlit.
    
    Parameters:
    - text (str): The text to display.
    - size (int): Font size in pixels.
    - weight (str or int): Font weight (e.g., 'normal', 'bold', '600').
    - color (str): Text color (e.g., '#333333' or 'red').
    - icon (str): Optional emoji or icon to prefix the header.
    """
    icon_prefix = f"{icon} " if icon else ""
    st.markdown(
        f"<div style='font-size:{size}px; font-weight:{weight}; color:{color};text-align:{align};'>{icon_prefix}{text}</div>",
        unsafe_allow_html=True
    )

# Custom function to change the style of text
#-------------------------------------------------------


def styled_text(text, size=16, color="black", weight="normal"):
    st.markdown(
        f"<p style='font-size:{size}px; color:{color}; font-weight:{weight};'>{text}</p>",
        unsafe_allow_html=True
    )


# Function to replace 'unknown' Year with Year1 of the same patient where APP Year is 1
def replace_unknown_year(group):
    # Get the Year1 value for APP Year == 1 for this patient
    year1_value = group.loc[group['App Year'] == 1, 'Year1'].values
    if len(year1_value) > 0:  # If there is a value
        group.loc[(group['Year'] == 'unknown'), 'Year'] = year1_value[0]
    return group

############# EXECUTION STARTS HERE ############################
#--------------------------------------------------------------#


data_o = pd.read_excel("./database_original_latest.xlsx")
data_c = pd.read_excel("./database_clean_latest.xlsx")


st.set_page_config(layout="wide")
# Custom CSS for sidebar background
st.markdown(
    """
    <style>
    /* Main Panel Background Color */
    [data-testid="stAppViewContainer"] {
        background-color: #fafaf3 !important; /* Change this to your preferred background color */
    }
    [data-testid="stSidebar"] {
        background-color: #ededdd; /* Change this color to your preferred background color */
        color: white; /* Text color */
    }
    [data-testid="stSidebarUserContent"] ul.nav > li > a {
        color: blue !important; /* Link color */
    }
    [data-testid="stSidebarUserContent"] .nav-link:hover {
        background-color: blue !important; /* Hover background color */
        color: blue !important; /* Hover text color */
    }
    </style>
    """,
    unsafe_allow_html=True
)



# Control Left Navaigation Panel
#-------------------------------#
with st.sidebar:
    selected = option_menu(
    menu_title = "Hope Foundation",
    options = ["Overview","Last Year - Overview", "Request Status", "Funds Distributions","Demographics", "Data Quality"],
    icons = ["house","rewind","activity","notepad","population","validation/test"],
    menu_icon = "cast",
    default_index = 0,
    #orientation = "horizontal",
)


# Main Content Based on Selection
#--------------------------------#


##              SUMMARY OF IMPACT AND PROGRESS THAT CAN BE SHOWN TO STAKEHOLDERS IN THE FOUNDATION       ##
##-------------------------------------------------------------------------------------------------------##
if selected == "Overview":

    custom_header(text="Annual Distribution of Funds",align='center',size=35,color='#94cd5f')
    r1col1,r1col2 = st.columns(2)
    custom_header(text="Transforming Lives Through Support",align='center',size=35,color='#94cd5f')
    r2col1, r2col2 = st.columns(2)
    
    with r1col1:
        
        by_columns = ['Patient ID#','Payment Date','Grant Req Date', 'App Year','Amount']
        df = data_c[by_columns].copy()
        # Extract year safely
        df['Year'] = pd.to_datetime(df['Payment Date'], errors='coerce').dt.year
        
        # Convert to Int (drop decimals), then to string, replacing NaNs with 'unknown'
        df['Year'] = df['Year'].apply(lambda x: str(int(x)) if pd.notnull(x) else 'unknown')
       
        # Create a new Colum
        df['Year1'] = pd.to_datetime(df['Grant Req Date'], errors='coerce').dt.year + ( df['App Year'] - 1)
        df = df.groupby('Patient ID#').apply(replace_unknown_year).reset_index(drop=True)
        

        by_columns = ['Year','Amount']
        df = df[by_columns].copy()

        # Filter and group
        df = df[df['Amount'] > 0].groupby('Year')['Amount'].sum()
        st.bar_chart(df)

    with r1col2:
        df_reset = df.reset_index()
        fig = px.pie(df_reset, names='Year', values='Amount')
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig)

    with r2col1:
        title='Patient Count by City in Nebraska'
        df = data_c.groupby(['Pt City','Pt State'])['Patient ID#'].nunique().reset_index()
        df.rename(columns={'Patient ID#': 'Patient Count'}, inplace=True)
        df['Pt City'] = df['Pt City'].str.title() 
        df['Pt State'] = df['Pt State'].str.upper()
        df = df.groupby(['Pt City','Pt State'])['Patient Count'].sum()

        us_cities = pd.read_csv("./us_cities.csv")


        merged_df = pd.merge(df, us_cities, left_on=['Pt City', 'Pt State'],right_on=['CITY','STATE_CODE'], how='left')
        
        fig = px.scatter_geo(
            merged_df,
            lat='LATITUDE',
            lon='LONGITUDE',
            size='Patient Count',
            hover_name='CITY'
        )
        fig.update_geos(
        scope='usa',
        center={'lat': 41.5, 'lon': -99.5},  # Centered on Nebraska
        projection_scale=5.5,  # Zooms into Nebraska
        showcountries=False,  # Hide country borders
        showcoastlines=False
        )
        # Style tweaks
        fig.update_traces(marker=dict(line=dict(width=0.5, color='red')))
        fig.update_layout(geo=dict(showland=True, landcolor="#D2B48C"))

        st.plotly_chart(fig, use_container_width=True)


    with r2col2:
        df = data_c.groupby(['Race','Gender'])['Amount'].sum().reset_index()
        fig = px.bar(
            df,
            x='Race',
            y='Amount',
            color='Gender',         # distinguishes bars side-by-side
            barmode='group'         # enables side-by-side bars
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


#SHOWCASES A HIGH-LEVEL SUMMARY OF IMPACT AND PROGRESS OVER THE PAST YEAR THAT CAN BE SHOWN TO STAKEHOLDERS IN THE FOUNDATION.#
##---------------------------------------------------------------------------------------------------------------------------##
elif selected == "Last Year - Overview":
    year = datetime.now().year - 1
    custom_header(text="Year in Review " + str(year),align='center',size=35,color='#94cd5f')

    by_columns = ['Patient ID#','Request Status','Application Signed?']
    df = data_c[data_c['Grant Req Date'].dt.year == (year)][by_columns].drop_duplicates()
    totalRequests = len(df)
    custom_header(text="Patient Approval ", size=25, color='#386d06',align='center', icon=None)

    show_by_breakdown = st.checkbox('Break by Application Signed Status',value=False)
    if show_by_breakdown:
        by_columns = ['Request Status','Application Signed?']
    else:
        by_columns = ['Request Status']
    df = df.groupby(by_columns).size().reset_index(name='Count')


    
    if show_by_breakdown:
        # Grouped bar chart
        fig = px.bar(
            df,
            x='Request Status',
            y='Count',
            color='Application Signed?',         # distinguishes bars side-by-side
            barmode='group',                     # enables side-by-side bars
            labels={
                'Request Status': 'Request Status',
                'Count': 'Patient Count'
            },
            title="Patient Approval Status"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:

        # Create pie chart with Plotly
        fig = px.pie(
            df,
            names='Request Status',
            values='Count',
            title= "Total Patient : " + str(totalRequests),
            hole=0.3  # optional: for donut-style pie
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

    # Total Paid Last Year
    by_columns = ['Type of Assistance (CLASS)','Race','Gender','Amount']
    df = data_c[(data_c['Amount'] > 0) & (data_c['Payment Date'].dt.year == year)][by_columns]
    total_paid = df['Amount'].sum().round(2)
    custom_header(text="Amount Paid", size=25, color='#386d06', align='center', icon=None)
    
    # Checkbox to filter
    show_by_total_paid = st.checkbox('Breakdown by Demography',value=False)
    if show_by_total_paid:
        by_columns = ['Type of Assistance (CLASS)','Race','Gender']
        sort_columns = ['Type of Assistance (CLASS)','Total Paid',  'Race', 'Gender']
        sort_order = [True,False, True, True]
    else:
        by_columns = ['Type of Assistance (CLASS)']
        sort_columns = ['Total Paid','Type of Assistance (CLASS)']
        sort_order = [False, True]

    df = df.groupby(by_columns)['Amount'].sum().reset_index(name='Total Paid')
    df['Total Paid'] = df['Total Paid'].round(2)
    df = df.sort_values(
        by=sort_columns,
        ascending=sort_order)


    if show_by_total_paid:
        st.dataframe(df.reset_index(drop=True).style.format({'Total Paid': '{:.2f}'}))
        st.write("Total Amount Paid : " + str(total_paid))
    else:
        # Create horizontal bar chart
        fig = px.bar(
            df,
            x='Total Paid',
            y='Type of Assistance (CLASS)',
            orientation='h',
            title='Amount Paid by Category',
            labels={'Total Paid': 'Expense ($)'},
            color='Type of Assistance (CLASS)'  # optional: color by category
        )
        # Remove legend
        fig.update_layout(showlegend=False)
        fig.update_layout( yaxis_title="")

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)


#----------------------------------------------------------------------------------------------------------#
# Create a page showing all of the applications that are "ready for review", and                           #
# can be filtered by whether or not the application has been signed by the necessary committee members.    #
#----------------------------------------------------------------------------------------------------------#
elif selected == "Request Status":


    custom_header(text="Request Ready for Review ",align='center',size=35,color='#94cd5f')
    df = subset_df(df=data_c,column='Request Status',condition="Approved",op='==')
    # Dropdown to select a category
    category_options = sorted(df['Application Signed?'].unique())
    selected_category = st.selectbox("Filter by Application Signed?", category_options,index=2)

    # Filter the DataFrame
    filtered_df = df[df['Application Signed?'] == selected_category]
    filtered_df['Grant Req Date'] = pd.to_datetime(filtered_df['Grant Req Date']).dt.strftime('%Y-%m-%d')

    # Display the filtered DataFrame
    st.dataframe(filtered_df.reset_index(drop=True),height=500)


#------------------------------------------------------------#    
#                         REPORT MISSING DATA                #
#------------------------------------------------------------#
elif selected == "Data Quality":

    totalGrantReqDate = data_c['Grant Req Date'].count()
    totalInvalidGrantReqDate = pd.to_datetime(data_c['Grant Req Date'], errors='coerce').isna().sum()
    totalInvalidGrantReqDatePerc = round(float(totalInvalidGrantReqDate / totalGrantReqDate), 2) if totalGrantReqDate > 0 else 0.0

    
    totalRemaingBalance = data_c['Remaining Balance'].count()
    totalInvalidRemaingBalance = ((data_c['Remaining Balance'] < 0) | (data_c['Remaining Balance'].isna())).sum()
    totalInvalidRemaingBalancePerc = round(float(totalInvalidRemaingBalance / totalRemaingBalance), 2) if totalRemaingBalance > 0 else 0.0

    allowed_statuses = ['Approved', 'Pending', 'Denied']
    totalRequestStatus = data_c['Request Status'].count()
    totalInvalidRequestStatus = (~data_c['Request Status'].isin(allowed_statuses)).sum()
    totalInvalidRequestStatusPerc = round(float(totalInvalidRequestStatus / totalRequestStatus), 2) if totalRequestStatus > 0 else 0.0


    totalPaymentDate =  data_o['Payment Submitted?'].count()
    totalInvalidPaymentDate =  data_o['Payment Submitted?'].str.lower().eq('yes').sum()
    totalInvalidPaymentDatePerc = round(float(totalInvalidPaymentDate / totalPaymentDate), 2) if totalPaymentDate > 0 else 0.0



    totalApplicationSigned = data_c['Application Signed?'].count()
    totalMissingApplicationSigned = (
        data_c['Application Signed?'].str.lower().eq('missing') &
        data_c['Request Status'].str.lower().eq('approved')
    ).sum()
    totalMissingApplicationSignedPerc = round(float(totalMissingApplicationSigned / totalApplicationSigned), 2) if totalApplicationSigned > 0 else 0.0

    # Create summary table
    summary_df = pd.DataFrame({
        'Row IDs': [
            'Grant Req Date',
            'Remaining Balance',
            'Request Status',
            'Payment Submitted?',
            'Application Signed (Approved only)'
        ],
        'Total Invalid Recs': [
            "{}".format(totalInvalidGrantReqDate),
            "{}".format(totalInvalidRemaingBalance),
            "{}".format(totalInvalidRequestStatus),
            "{}".format(totalInvalidPaymentDate),
            "{}".format(totalMissingApplicationSigned)
        ],
        'Invalid Recs %': [
            "{:.2%}".format(totalInvalidGrantReqDatePerc),
            "{:.2%}".format(totalInvalidRemaingBalancePerc),
            "{:.2%}".format(totalInvalidRequestStatusPerc),
            "{:.2%}".format(totalInvalidPaymentDatePerc),
            "{:.2%}".format(totalMissingApplicationSignedPerc)
        ]
    })

    # Display nicely in Streamlit
    #custom_header(text="Data Quality Summary", size=20, weight='bold', color='#000000',align='center', icon=None)
    custom_header(text="Data Quality Summary",align='center',size=35,color='#94cd5f')
    st.table(summary_df.reset_index(drop=True)) 

    
#---------------------------------------------------------------------------------------#
#   Create a page answering "how much support do we give, based on location, gender,    #
#   income size, insurance type, age, etc".                                             #
#   In other words, break out how much support is offered by the listed demographics.   #
#---------------------------------------------------------------------------------------#
elif selected == "Funds Distributions":  
    custom_header(text="Funds Distributions",align='center',size=35,color='#94cd5f')


    c = st.container()
    with c:
        #What are the average amounts given by assistance type? This would help us in terms of budgeting and determining future programming needs.
        # Checkbox to filter
        custom_header(text="Total Amount Paid by Assistance Type",size=25, color='#386d06',align='center', icon=None)
        #show_by_appyear = st.checkbox('Break by AppYear',value=False)
        col1, col2 = st.columns(2)
        with col1:
            #if show_by_appyear:
                by_columns = ['Type of Assistance (CLASS)','App Year']
                df = data_c[data_c['Amount'] > 0].groupby(by_columns)['Amount'].sum().reset_index()
                fig = px.bar(
                    df,
                    x='App Year',
                    y='Amount',
                    color='Type of Assistance (CLASS)',         # distinguishes bars side-by-side
                    barmode='group'                             # enables side-by-side bars
                )
                # Control X-axis breaks (ticks) using dtick
                fig.update_xaxes(
                    dtick=1  # Change this to your desired interval (e.g., 2, 5)
                )
                fig.update_layout(showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            #else:
                by_columns = ['Type of Assistance (CLASS)']
                df = data_c[data_c['Amount'] > 0].groupby(by_columns)['Amount'].sum().reset_index(name='Total Amount').sort_values(by='Total Amount', ascending=False)
                df = df.reset_index(drop=True)
                #df = df.sort_values(by='Amount', ascending=False)
                st.dataframe(df)

    c2 = st.container()
    with c2:
        #Create a page showing how long it takes between when we receive a patient request and actually send support.
        custom_header(text="Approval to Payment Duration",size=25, color='#386d06',align='center', icon=None)
        col1, col2 = st.columns(2)
            
        # # Checkbox to filter
        #show_by_pay_dur = st.checkbox('Break by Demographics',value=False)

        with col1:
            #else:
                df_columns = ['Race','Gender','Insurance Type','Grant Req Date','Payment Date']
                df = subset_df(df=data_c,column='Payment Date',condition='', op='notna')[df_columns] 
                df['DaysTillPaid']  =  (df['Payment Date'] - df['Grant Req Date']).dt.days
                df_columns = ['DaysTillPaid']
                df = df[df_columns]
                df_filtered_demography = df[df['DaysTillPaid'] >= 0]
                # Categorize values over 30 days as "Over 30 Days"
                #df_filtered_demography['DaysTillPaid'] = np.where(df_filtered_demography['DaysTillPaid'] > 30, 'Over 30 Days', df_filtered_demography['DaysTillPaid'])
                df_filtered_demography = df_filtered_demography.groupby(df_columns)['DaysTillPaid'].count().sort_values(ascending=False).reset_index(name='Count')
                #st.bar_chart(df_filtered_demography,x='DaysTillPaid',y='Count')
                # Display the bar chart
                #st.bar_chart(df_filtered_demography.set_index('DaysTillPaid'))

                fig = px.bar(
                    df_filtered_demography,
                    x='DaysTillPaid',
                    y='Count',
                    labels = {
                        'DaysTillPaid' : 'Total Duration for Payment',
                        'Count' : 'Total Transactions'
                    }
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            #if show_by_pay_dur:
                df_columns = ['Race','Gender','Insurance Type','Grant Req Date','Payment Date']
                df = subset_df(df=data_c,column='Payment Date',condition='', op='notna')[df_columns] 
                df['DaysTillPaid']  =  (df['Payment Date'] - df['Grant Req Date']).dt.days
                df_columns =  ['Race','Gender','Insurance Type','DaysTillPaid']
                df = df[df_columns]
                df_filtered_demography = df[df['DaysTillPaid'] >= 0].groupby(df_columns)['DaysTillPaid'].count().sort_values(ascending=False).reset_index(name='Count')
                st.dataframe(df_filtered_demography)


    c3 = st.container()
    with c3:
        #Create a page showing how many patients did not use their full grant amount in a given application year. 
        custom_header(text="Unused Funds Per Patients By Application Year",size=25, color='#386d06',align='center', icon=None)
        by_columns = ['App Year']
        df = data_c[data_c['Remaining Balance'] > 0].groupby(by_columns)['App Year'].size().sort_values(ascending=False).reset_index(name='# of Accounts')

        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df, names='App Year', values='# of Accounts')
            fig.update_layout(showlegend=True,
                            legend_title_text='Application Year')  # Set legend title here)
            st.plotly_chart(fig)

        with col2:
            st.dataframe(df)

elif selected == "Demographics":  
    custom_header(text="Demographics Information",align='center',size=35,color='#94cd5f')
    category_options = ['Race','Gender','Insurance Type']
    selected_category = st.selectbox("Select Demographic Category", category_options,index=0)

    sub_category_options = sorted(data_c[selected_category].unique())
    selected_sub_category = st.selectbox("Sub Category", sub_category_options,index=0)

    df_columns = category_options.copy()
    df_columns.append('Amount')
    df = subset_df(df=data_c, column='Amount',condition=0,op='>')[df_columns] 

    df_columns_groupby = [selected_category]
    df_columns_groupby = df_columns_groupby + list(set(df_columns_groupby).symmetric_difference(set(category_options)))
    df_filtered_demography = df[df[selected_category] == selected_sub_category].groupby(df_columns_groupby)['Amount'].sum().sort_values(ascending=False)
    #st.write("selected_category  is " + str(selected_category) + "selected_sub_category" + str(selected_sub_category))
    st.dataframe(df_filtered_demography)
else:
   st.write("The END")