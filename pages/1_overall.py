import google_auth_httplib2
import httplib2
import numpy as np
import pandas as pd
import streamlit as st
import math
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from re import sub
from decimal import Decimal
import plotly.express as px
from st_aggrid import AgGrid

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

@st.cache
def get_data(gsheet_connector) -> pd.DataFrame:
    values = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:P",
        )
        .execute()
    )

    df = pd.DataFrame(values["values"])
    df.columns = df.iloc[0]
    df = df[1:]
    
    #error handle formats (currency -> float)
    dfDA = df['Debit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
    df['Debit Amount'] = dfDA
    dfCA = df['Credit Amount'].apply(lambda x: StringToDec(sub(r'[^\d.]', '', x)))
    df['Credit Amount'] = dfCA
    df['Y'] = pd.to_numeric(df['Y'])

    return df

def StringToDec(x):
    if x == '':
        return np.nan
    else:
        return float(Decimal(x)) 

# Donation Matrix by Individual
def overall_page():
#%% Retrive Data
    gsheet_connector = connect_to_gsheet()
    data = get_data(gsheet_connector)

#%% Donation Analysis

    #Donation Matrix Overall 
    @st.cache
    def overall_data():
        DMY = data.groupby(['Y']).sum().reset_index()
        DMY = pd.melt(DMY,id_vars = ['Y'],var_name='Group')

        fig = px.bar(DMY, x="Y", y="value",
                    color='Group', barmode='group',
                    height=400)
        
        return fig
    
    fig = overall_data()

    st.plotly_chart(fig, use_container_width=True)

st.set_page_config(page_title="Overall", page_icon="📈")

st.markdown('Overall')

st.sidebar.header("Overall")

#settings
SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1uAa3CbD5uYpdEQs3RXenCb5trLqnZGbOtqfaxUhcp0E"
SHEET_NAME = "Bank"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

overall_page()