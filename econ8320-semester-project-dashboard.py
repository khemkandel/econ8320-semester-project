#pip install openpyxl
#pip install pgeocode
#function prompt { "$(Split-Path -Leaf (Get-Location))> " }
#python -m streamlit run .\econ8320-semester-project.py

import subprocess
import sys

# Show all rows
#pd.set_option('display.max_rows', None)

# (optional) Show all columns too
#pd.set_option('display.max_columns', None)
#pd.set_option('future.no_silent_downcasting', True)


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

def custom_header(text, size=20, weight='bold', color='#000000',align='left', icon=None):
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

def styled_text(text, size=16, color="black", weight="normal"):
    st.markdown(
        f"<p style='font-size:{size}px; color:{color}; font-weight:{weight};'>{text}</p>",
        unsafe_allow_html=True
    )


data_o = pd.read_excel("./database_original_latest.xlsx")
data_c = pd.read_excel("./database_clean_latest.xlsx")


# Sidebar
# st.sidebar.title("📊 Hope Foundation")
# page = st.sidebar.radio("Go to", ["Overview", "Request Status", "Demographics", "Data Quality"])

with st.sidebar:
    selected = option_menu(
    menu_title = "Hope Foundation",
    options = ["Overview","Last Year - Overview", "Request Status", "Demographics", "Data Quality"],
    icons = ["house","rewind","activity","Population","	Validation/Test"],
    menu_icon = "cast",
    default_index = 0,
    #orientation = "horizontal",
)


# Main Content Based on Selection

if selected == "Last Year - Overview":
    #Finally, create a page that showcases a high-level summary of impact and progress over the past year that can be shown to stakeholders in the foundation.
    #Total Patient and their approval Status
    # Two columns
    year = datetime.now().year - 1
    st.title("📈 Year in Review " + str(year))

    # col1, col2 = st.columns(2)

    # with col1:

    by_columns = ['Patient ID#','Request Status','Application Signed?']
    df = data_c[data_c['Grant Req Date'].dt.year == (year)][by_columns].drop_duplicates()
    totalRequests = len(df)
    #st.write("Patient Approval ")
    custom_header(text="Patient Approval ", size=20, weight='bold', color='#000000',align='center', icon=None)

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
            barmode='group',       # enables side-by-side bars
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
        # st.dataframe(df.reset_index(drop=True))
        # st.write("Total Patient : " + str(totalRequests))




    # with col2:

    # Total Paid Last Year
    by_columns = ['Type of Assistance (CLASS)','Race','Gender','Amount']
    df = data_c[(data_c['Amount'] > 0) & (data_c['Payment Date'].dt.year == year)][by_columns]
    total_paid = df['Amount'].sum().round(2)
    custom_header(text="Amount Paid", size=20, weight='bold', color='#000000', align='center', icon=None)
    
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
            labels={'Total Paid': 'Expense ($)', 'Category': 'Category'},
            color='Type of Assistance (CLASS)'  # optional: color by category
        )
        # Remove legend
        fig.update_layout(showlegend=False)

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)



elif selected == "Request Status":
    # Create a page showing all of the applications that are "ready for review", and 
    # can be filtered by whether or not the application has been signed by the necessary committee members.

    st.title("📈 Request Ready for Review ")
    df = subset_df(df=data_c,column='Request Status',condition="Approved",op='==')
    # Dropdown to select a category
    category_options = sorted(df['Application Signed?'].unique())
    selected_category = st.selectbox("Filter by Category", category_options,index=2)

    # Filter the DataFrame
    filtered_df = df[df['Application Signed?'] == selected_category]

    # Display the filtered DataFrame
    st.dataframe(filtered_df.reset_index(drop=True))

elif selected == "Data Quality":
    
    ##row2:
    # Missing Data

    totalInvalidGrantReqDate = pd.to_datetime(data_c['Grant Req Date'], errors='coerce').isna().sum()
    totalInvalidRemaingBalance = ((data_c['Remaining Balance'] < 0) | (data_c['Remaining Balance'].isna())).sum()

    allowed_statuses = ['Approved', 'Pending', 'Denied']
    totalInvalidRequestStatus = (~data_c['Request Status'].isin(allowed_statuses)).sum()
    totalInvalidPaymentDate =  data_o['Payment Submitted?'].str.lower().eq('yes').sum()
    totalMissingApplicationSigned = (
        data_c['Application Signed?'].str.lower().eq('missing') &
        data_c['Request Status'].str.lower().eq('approved')
    ).sum()

    # Create summary table
    summary_df = pd.DataFrame({
        'Check': [
            'Invalid Grant Req Date',
            'Invalid Remaining Balance',
            'Invalid Request Status',
            'Invalid Payment Submitted?',
            'Missing Application Signed (Approved only)'
        ],
        'Count': [
            totalInvalidGrantReqDate,
            totalInvalidRemaingBalance,
            totalInvalidRequestStatus,
            totalInvalidPaymentDate,
            totalMissingApplicationSigned
        ]
    })

    # Display nicely in Streamlit
    #custom_header(text="Data Quality Summary", size=20, weight='bold', color='#000000',align='center', icon=None)
    st.title("Data Quality Summary")
    st.table(summary_df.reset_index(drop=True)) 

elif selected == "Demographics":  
    #Create a page answering "how much support do we give, based on location, gender, income size, insurance type, age, etc". 
    #In other words, break out how much support is offered by the listed demographics.
    st.title("Demographics Information")
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


    #Create a page showing how long it takes between when we receive a patient request and actually send support.
    custom_header(text="Approval to Payment Duration",align='center')

    # Checkbox to filter
    show_by_pay_dur = st.checkbox('Break by Demographics',value=False)

    df_columns = ['Race','Gender','Insurance Type','Grant Req Date','Payment Date']
    df = subset_df(df=data_c,column='Payment Date',condition='', op='notna')[df_columns] 
    df['DaysTillPaid']  =  (df['Payment Date'] - df['Grant Req Date'])
    
    if show_by_pay_dur:
        df_columns =  ['Race','Gender','Insurance Type','DaysTillPaid']
    else:
        df_columns = ['DaysTillPaid']
        
    df = df[df_columns]
    df_filtered_demography = df[df['DaysTillPaid'] >= pd.Timedelta(days=0)].groupby(df_columns)['DaysTillPaid'].count().sort_values(ascending=False).reset_index(name='Count')
    st.dataframe(df_filtered_demography)

    #Create a page showing how many patients did not use their full grant amount in a given application year. 
    
    custom_header(text="Unused Funds Per Patients By Application Year",align='center')
    by_columns = ['App Year']
    df = data_c[data_c['Remaining Balance'] > 0].groupby(by_columns)['App Year'].size().sort_values(ascending=False).reset_index(name='# of Accounts')
    st.dataframe(df)

    #What are the average amounts given by assistance type? This would help us in terms of budgeting and determining future programming needs.
    # Checkbox to filter
    custom_header(text="Total Amount Paid by Assistance Type",align='center')
    show_by_appyear = st.checkbox('Break by AppYear',value=False)
    if show_by_appyear:
        by_columns = ['Type of Assistance (CLASS)','App Year']
    else:
        by_columns = ['Type of Assistance (CLASS)']
    df = data_c[data_c['Amount'] > 0].groupby(by_columns)['Amount'].sum()
    st.dataframe(df)

else:
    custom_header(text="Amount Distribution by Year",align='center')
    col1, col2 = st.columns(2)
    with col1:
        by_columns = ['Payment Date', 'Amount']
        df = data_c[by_columns].copy()

        # Extract year safely
        df['Year'] = pd.to_datetime(df['Payment Date'], errors='coerce').dt.year

        # Convert to Int (drop decimals), then to string, replacing NaNs with 'unknown'
        df['Year'] = df['Year'].apply(lambda x: str(int(x)) if pd.notnull(x) else 'unknown')

        # Filter and group
        df = df[df['Amount'] > 0].groupby('Year')['Amount'].sum()
        st.bar_chart(df)
        #st.dataframe(df)

    with col2:
        df_reset = df.reset_index()
        fig = px.pie(df_reset, names='Year', values='Amount')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)


    df = data_c.groupby(['Pt City','Pt State'])['Patient ID#'].nunique().reset_index()
    df.rename(columns={'Patient ID#': 'Patient Count'}, inplace=True)
    df['Pt City'] = df['Pt City'].str.title() 
    df['Pt State'] = df['Pt State'].str.upper()

    us_cities = pd.read_csv("./us_cities.csv")


    merged_df = pd.merge(df, us_cities, left_on=['Pt City', 'Pt State'],right_on=['CITY','STATE_CODE'], how='left')
    # coords = {
    #     'Lincoln': (40.8136, -96.7026),
    #     'Omaha': (41.2565, -95.9345),
    #     'Kearney': (40.6995, -99.0815),
    #     'Norfolk': (42.0324, -97.4160),
    # }

    # df['lat'] = df['Pt City'].map(lambda x: coords[x][0])
    # df['lon'] = df['Pt City'].map(lambda x: coords[x][1])

    #st.map(df[['lat', 'lon', 'Patient Count']])

    
    fig = px.scatter_geo(
        merged_df,
        lat='LATITUDE',
        lon='LONGITUDE',
        size='Patient Count',
        hover_name='Pt City',
        title='Patient Count by City in Nebraska'
    )
    fig.update_geos(
    scope='usa',
    center={'lat': 41.5, 'lon': -99.5},  # Centered on Nebraska
    projection_scale=5.5,  # Zooms into Nebraska
    showcountries=False,  # Hide country borders
    showcoastlines=False,  # Hide coastlines
    showland=True,
    landcolor="lightgrey"
    )

    st.plotly_chart(fig, use_container_width=True)