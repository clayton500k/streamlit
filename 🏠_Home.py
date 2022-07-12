from pickle import FALSE
import google_auth_httplib2
import httplib2
import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from PIL import Image
import time 
from datetime import datetime
from anonymizedf.anonymizedf import anonymize
import pandas_datareader as dr

#Googlesheets data obtained using the methodology below:
#https://docs.streamlit.io/knowledge-base/tutorials/databases/private-gsheet

#settings
SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1uAa3CbD5uYpdEQs3RXenCb5trLqnZGbOtqfaxUhcp0E"
SHEET_NAME = "Bank"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

def connect_to_gsheet():
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[SCOPE],
    )

    # Create a new Http() object for every request
    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http()
        )
        return HttpRequest(new_http, *args, **kwargs)

    authorized_http = google_auth_httplib2.AuthorizedHttp(
        credentials, http=httplib2.Http()
    )
    service = build(
        "sheets",
        "v4",
        requestBuilder=build_request,
        http=authorized_http,
    )
    gsheet_connector = service.spreadsheets()
    return gsheet_connector

def get_data(gsheet_connector) -> pd.DataFrame:

    # Split into 2 requests to avoid downloading columns between P and AA

    values1 = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:P",
        )
        .execute()
    )

    values2 = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!AA:AE",
        )
        .execute()
    )

    df1 = pd.DataFrame(values1["values"])
    df2 = pd.DataFrame(values2["values"])
    df = pd.concat([df1,df2],axis=1)
    df.columns = df.iloc[0]
    df = df[1:]
    
    # Error handle formats
    
    # Remove null Months
    df = df[df['Y'].isnull()==False]
    
    try:
        dfDA = df['Debit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
        df['Debit Amount'] = dfDA
        dfCA = df['Credit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
        df['Credit Amount'] = dfCA
    except:
        sys.sleep(0.1)

    df['Y'] = pd.to_numeric(df['Y'])
    df['Y'] = df['Y'].astype(pd.Int32Dtype())

    # Filter data

    # Convert to lowercase to remove case-sensitivity
    # Ignore warning: https://www.dataquest.io/blog/settingwithcopywarning/
    df['Renamer'] = df['Renamer'].str.lower()
    df['Audit Income'] = df['Audit Income'].str.lower()
    df['Audit expense'] = df['Audit expense'].str.lower() 
    df['Source Type'] = df['Source Type'].str.lower() 

   # Store downloaded data for use in expenses filter
    working_data = df

    # Isolate income data for income filter
    df = df[df['Credit Amount'].isnull()==False]

    exclude_transfers = ['Transfers from 500k','Transfers from NCM to 500k','Transfer from savings account','Transfer from 500k USA']
    exclude_sources = ['Go Cardless (Churchapp)','Go Cardless','Stripe'] # ,'Gift Aid (HMRC Charities)','Transfer from 500k','500k Indiana']

    # Convert exclude lists to lowercase
    exclude_transfers = list(map(lambda x : x.lower(),exclude_transfers))
    exclude_sources = list(map(lambda x : x.lower(),exclude_sources))

    # Bank
    df_Bank = df[(df['Source Type']=="bank") & (df['Audit Income'].isin(exclude_transfers)==False) & (df['Renamer'].isin(exclude_sources)==False) & (df['Grant Partner'].isnull()) & (df['Regular/Accrual']!='N/A')]
    
    # Savings Account
    df_SA = df[(df['Source Type']=="savings account") & (df['Regular/Accrual']!='N/A') & (df['Audit Income'].isin(exclude_transfers)==False)]

    # NCM
    df_NCM = df[(df['Source Type']=="ncm") & (df['Regular/Accrual']!='N/A') & (df['Audit Income'].isin(exclude_transfers)==False)]

    # CHURCHAPP
    df_CA = df[df['Source Type']=="churchapp"]

    # BEACON
    df_B = df[df['Source Type']=="beacon"]

    # Bank Arizona
    df_BA = df[(df['Source Type']=="bank (arizona)") &  (df['Renamer'] != 'paypal (arizona)') & (df['Renamer'] != 'stripe') & (df['Renamer']!='beacon (arizona)') & (df['Renamer']!='') & (df['Regular/Accrual']!='N/A')]
    
    # Paypal Arizona
    df_PA = df[(df['Source Type']=="paypal (arizona)") &  (df['Renamer'].isnull()==False) & (df['Regular/Accrual']!="N/A")]

    # Stripe (Arizona)
    df_ST = df[(df['Source Type']=="stripe (arizona)")]

    # Paypal UK
    df_UK = df[(df['Source Type']=="paypal")]

    # Bind
    df_income = pd.concat([df_Bank,df_SA,df_NCM,df_CA,df_B,df_BA,df_PA,df_ST,df_UK])

    # Paul Searle Override
    def override(x):
        if (x=='paul searle (aquaaid)') | (x=='kirsten searle') :
            x = 'paul searle'	
        return x

    df_income['Renamer'] = df_income['Renamer'].apply(override)

    # Expense filter
    df = working_data[working_data['Debit Amount'].isnull()==False]

    exclude_transfers = ['Transfer to 500k','Transfer from 500K To NCM','Transfer to savings account','Grant (transfer) to 500k UK']
    exclude_transfers = list(map(lambda x : x.lower(),exclude_transfers))

    # Bank
    df_Bank = df[(df['Source Type']=="bank") & (df['Audit expense'].isin(exclude_transfers)==False)]

    # Savings Account
    df_SA = df[(df['Source Type']=="savings account") & (df['Audit expense'].isin(exclude_transfers)==False)]

    # NCM
    df_NCM = df[(df['Source Type']=="ncm") & (df['Audit expense'].isin(exclude_transfers)==False)]

    # Bank (Arizona)
    df_BA = df[(df['Source Type']=="bank (arizona)") & (df['Audit expense'].isin(exclude_transfers)==False)]

    # Paypal (Arizona)
    df_PA = df[(df['Source Type']=="paypal (arizona)") & (df['Audit expense'].isin(exclude_transfers)==False)]

    # Combine Expense filters
    df_expense = pd.concat([df_Bank,df_SA,df_NCM,df_BA,df_PA])

    # Combine Income and Expense
    df = pd.concat([df_income,df_expense])

    # Reformat as title case
    df['Renamer'] = df['Renamer'].str.title()
    df['Audit Income'] = df['Audit Income'].str.title()
    df['Audit expense'] = df['Audit expense'].str.title() 
    df['Source Type'] = df['Source Type'].str.title() 
    
    # Return only first 1 8columns
    df = df.iloc[:,:18]

    # Add Date Column
    df['M'] = df['M'].apply(leading_zero)
    df['Month'] = df["Y"].astype(str) + df["M"].astype(str) + '01'
    df['Month'] = df['Month'].apply(StringtoDate)
    df['Month'] = pd.to_datetime(df['Month'])

    # Select GBP or USD values
    # Currency rates downloaded from Yahoo Finance using: https://stackoverflow.com/a/66420251/18475595
    start_date = '2012-06-01'
    end_date = pd.Timestamp.today()  
        
    # retrieve market data of current ticker symbol
    gbpusd = dr.data.DataReader('GBPUSD%3DX', data_source='yahoo', start=start_date, end=end_date).reset_index()
    gbpusd['Month'] = pd.to_datetime(gbpusd['Date'])

    gbpusd = gbpusd[gbpusd['Month'].dt.day==1][['Month','Adj Close']]
    
    df = pd.merge(df,gbpusd,how='left',on='Month')
    
    df['Credit Amount GBP'] =  df['Credit Amount']
    df['Credit Amount USD'] =  df['Credit Amount GBP'] * df['Adj Close']

    df['Debit Amount GBP'] =  df['Debit Amount']
    df['Debit Amount USD'] =  df['Debit Amount GBP'] * df['Adj Close']

    return df

def StringToDec(x):
    if x == '':
        return np.nan
    else:
        return float(Decimal(x))

def StringtoDate(x):
    try:
        datetime.strptime(x,"%Y%m%d").date()
    except:
        x
    return x

# leading 0 for Jan-Sept
def leading_zero(x):
    if pd.to_numeric(x) < 10:
        x = '0' + str(x)
    return x

#password check
#using Option 2 here: https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def run():
    def check_password():
        """Returns `True` if the user had the correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
            ):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # don't store username + password
                #del st.session_state["username"] # store username for anon check

            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show inputs for username + password.
            st.text_input("Username", key="username") #on_change=password_entered,
            st.text_input("Password", type="password", on_change=password_entered, key="password")
            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error.
            st.text_input("Username", key="username") #on_change=password_entered,
            st.text_input("Password", type="password", on_change=password_entered, key="password")
            st.error("😕 User not known or password incorrect")
            return False
        else:
            # Password correct.
            return True

    if check_password():

        st.sidebar.success("Select a page above")

        if 'currency_choice' not in st.session_state:
            st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True)
        else:
            st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

        st.title('500k Donation Analytics')

        # Session state documentation: https://docs.streamlit.io/library/advanced-features/session-state
        
        # Password check used in other pages
        if 'password_check' not in st.session_state:
            st.session_state.password_check = 'correct'

        # Make success disappear after 2 seconds using st.empty()
        # https://docs.streamlit.io/library/api-reference/layout/st.empty

        placeholder = st.empty()

        # Spinner while downloading: https://docs.streamlit.io/library/api-reference/status/st.spinner        
        with st.spinner('Downloading Data from Google Sheet. Please Wait...'):  

            # Download all Bank Data
            if 'data' not in st.session_state:
                gsheet_connector = connect_to_gsheet()
                tmp = get_data(gsheet_connector)

                # If guest account, anonymize names:
                # https://towardsdatascience.com/how-to-quickly-anonymize-personal-names-in-python-6e78115a125b
                # https://pypi.org/project/anonymizedf/
                
                if st.session_state["username"]=="admin":
                    st.session_state["data"] = tmp
                else:    
                    an = anonymize(tmp)
                    an.fake_names("Renamer")
                    if "giftaid_fake_name" not in st.session_state:
                        st.session_state["giftaid_fake_name"] = tmp[tmp['Renamer']=='Gift Aid (Hmrc Charities)']['Fake_Renamer'].tolist()[0]
                    tmp['Renamer'] = tmp['Fake_Renamer']
                    st.session_state["data"] = tmp

            # Aggregate Individual Data
            if 'DM' not in st.session_state:
                data = st.session_state["data"]
                DM = data.groupby(['Renamer','Source Type','Y']).sum().reset_index()
                st.session_state["DM"] = DM

            # Remove Giftaid for Tier Report Data
            if 'TRD' not in st.session_state:
                if st.session_state["username"]=="admin":
                    st.session_state["TRD"] = DM[DM['Renamer']!='Gift Aid (Hmrc Charities)']
                else:
                    st.session_state["TRD"] = DM[DM['Renamer']!=st.session_state["giftaid_fake_name"]]

        placeholder.success('Done!')

        time.sleep(0.7)

        placeholder.empty()
    
        #Markdown documentation: https://docs.streamlit.io/library/api-reference/text/st.markdown
        
        st.markdown(f"This Streamlit app interacts with the [500k Finances Core Google Sheet]({GSHEET_URL}) to produce useful analytics.")

        st.markdown("Select **Overall** for a view of the overall financial picture.")

        st.markdown("Select **Individuals** to analyze donations from specific individuals.")

        st.markdown("Select **Tier Report** to group donors by size category and attribute overall giving to each category.")

        st.markdown("Select **Donor Comparison** to view each individual's change in donations each year.")

        st.markdown("This App was originally designed by <a href='mailto:claytongillespie116@gmail.com'>Clayton Gillespie</a> and is maintained by the 500k Tech Team.", unsafe_allow_html=True)
        
        st.markdown("Click **View App Source** in the top right menu to visit the GitHub containing this app's source code.")

        st.markdown(f"Data last updated {str(st.session_state.data[['Month']].iloc[-1,:][0])[0:10]}.")

        st.markdown("_Soli Deo Gloria_")

        # Image documentation: https://docs.streamlit.io/library/api-reference/media/st.image
        image = Image.open('India_map.jpg') #added to GitHub
        st.image(image)

        convert_gbpusd(st.session_state["currency_choice"])

# Convert to USD/GBP
def convert_gbpusd(curr): 

    tmp = st.session_state["data"]

    if curr=='USD':
        tmp['Credit Amount'] = tmp['Credit Amount USD']
        tmp['Debit Amount'] = tmp['Debit Amount USD']
    elif curr=='GBP':
        tmp['Credit Amount'] = tmp['Credit Amount GBP']
        tmp['Debit Amount'] = tmp['Debit Amount GBP']

    st.session_state["data"] = tmp

    # Choice flows through into DM and TRD
    DM = tmp[['Renamer','Source Type','Y','Credit Amount','Debit Amount']].groupby(['Renamer','Source Type','Y']).sum().reset_index()
    st.session_state["DM"] = DM
    try: 
        st.session_state["TRD"] = DM[DM['Renamer']!=st.session_state["giftaid_fake_name"]]           
    except:
        st.session_state["TRD"] = DM[DM['Renamer']!='Gift Aid (HMRC Charities)']

st.set_page_config(layout='centered')

run()

