#%% Load
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
from PIL import Image

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
    df['Y'] = df['Y'].astype(pd.Int32Dtype())

    return df

def StringToDec(x):
    if x == '':
        return np.nan
    else:
        return float(Decimal(x))

#password check
#using Option 1 here: https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def run():
    def check_password():
        """Returns `True` if the user had the correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if st.session_state["password"] == st.secrets["password"]:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # don't store password
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show input for password.
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error.
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            st.error("😕 Password incorrect")
            return False
        else:
            # Password correct.
            return True

    if check_password():

        st.set_page_config(page_title="Home", page_icon="👋")

        st.sidebar.success("Select a page above")

        st.title('500k Donation Analytics')
        #Markdown documentation: https://docs.streamlit.io/library/api-reference/text/st.markdown
        st.markdown(f"This Streamlit app interacts with the [500k Finances Core Google Sheet]({GSHEET_URL}) to produce useful analytics.")

        st.markdown("Select **Overall** for a view of the overall financial picture.")

        st.markdown("Select **Individuals** to analyze donations from specific individuals.")

        st.markdown("Select **Tier Report** to group donors by size category and attribute overall giving to each category.")

        st.markdown("Select **Donor Comparison** to view each individual's change in donations each year.")

        st.markdown("This App was originally designed by <a href='mailto:claytongillespie116@gmail.com'>Clayton Gillespie</a> and is maintained by the 500k Tech Team.", unsafe_allow_html=True)
        
        st.markdown("Click **View App Source** in the top right menu to visit the GitHub containing this app's source code")

        st.markdown("_Soli Deo Gloria_")

        #Image: https://docs.streamlit.io/library/api-reference/media/st.image
        image = Image.open('India_map.jpg') #added to GitHub
        st.image(image)

        #SS Password check used in other pages
        if 'password_check' not in st.session_state:
            st.session_state.password_check = 'correct'

        #%% Download all Bank Data
        if 'data' not in st.session_state:
            gsheet_connector = connect_to_gsheet()
            st.session_state["data"] = get_data(gsheet_connector)

        #%% Aggregate Individual Data
        if 'DM' not in st.session_state:
            data = st.session_state["data"]
            st.session_state["DM"] = data.groupby(['Renamer','Source Type','Y']).sum().reset_index()
        

run()
