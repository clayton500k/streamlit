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
    dfDA = df['Debit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
    df['Debit Amount'] = dfDA
    dfCA = df['Credit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
    df['Credit Amount'] = dfCA
    df['Y'] = pd.to_numeric(df['Y'])
    df['Y'] = df['Y'].astype(pd.Int32Dtype())

   # Filter data

    exclude_transfers = ['Transfers from 500k','Transfers from NCM to 500k','Transfer from savings account','Transfer from 500k USA']
    exclude_sources = ['Go Cardless (Churchapp)','Go Cardless','Stripe'] # ,'Gift Aid (HMRC Charities)','Transfer from 500k','500k Indiana']

    # Source Bank
    df_Bank = df[(df['Source Type']=="BANK") & (df['Audit Income'].isin(exclude_transfers)==False) & (df['Renamer'].isin(exclude_sources)==False) & (df['Grant Partner'].isnull()) & (df['Regular/Accrual']!='N/A')]
    
    # Savings Account
    df_SA = df[(df['Source Type']=="Savings Account") & (df['Regular/Accrual']!='N/A') & (df['Audit Income'].isin(exclude_transfers)==False)]

    # NCM
    df_NCM = df[(df['Source Type']=="NCM") & (df['Regular/Accrual']!='N/A') & (df['Audit Income']!='Transfers from 500k')]

    # CHURCHAPP
    df_CA = df[df['Source Type']=="CHURCHAPP"]

    # BEACON
    df_B = df[df['Source Type']=="BEACON"]

    # Bank Arizona
    df_BA = df[(df['Source Type']=="Bank (Arizona)") & (df['Renamer'] != "Paypal (Arizona)") & (df['Renamer'].isnull()==False) & (df['Regular/Accrual']!='N/A')]
    
    # Paypal Arizona
    df_PA = df[(df['Source Type']=="Paypal (Arizona)") &  (df['Renamer'].isnull()==False) & (df['Regular/Accrual']!="N/A")]
    
    # Bind
    df = pd.concat([df_Bank,df_SA,df_NCM,df_CA,df_B,df_BA,df_PA])

    #st.write(df.groupby(['Y']).sum().reset_index())
    
    # Paul Searle Override
    def override(x):
        if (x=='Paul Searle (AquaAid)') | (x=='Kirsten Searle') :
            x = 'Paul Searle'	
        return x

    df['Renamer'] = df['Renamer'].apply(override)

    # Return only first 16 columns
    df = df.iloc[:,:16]

    # Add Date Column
    df['M'] = df['M'].apply(leading_zero)
    df['Month'] = df["Y"].astype(str) + df["M"].astype(str) + '01'
    df['Month'] = df['Month'].apply(lambda x: datetime.strptime(x,"%Y%m%d").date())
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
                        st.session_state["giftaid_fake_name"] = tmp[tmp['Renamer']=='Gift Aid (HMRC Charities)']['Fake_Renamer'].tolist()[0]
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
                    st.session_state["TRD"] = DM[DM['Renamer']!='Gift Aid (HMRC Charities)']
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

        st.markdown(f"Data last updated {str(data[['Month']].iloc[-1,:][0])[0:10]}.")

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

