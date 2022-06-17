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

#password check
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

        #settings
        SCOPE = "https://www.googleapis.com/auth/spreadsheets"
        SPREADSHEET_ID = "1uAa3CbD5uYpdEQs3RXenCb5trLqnZGbOtqfaxUhcp0E"
        SHEET_NAME = "Bank"
        GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

        st.sidebar.success("Select a page above")

        st.title('500k Analytics')
        st.write(f"This app shows how a Streamlit app can interact easily with a [Google Sheet]({GSHEET_URL}) to read or store data.")

        st.markdown("More fun text goes here")

if __name__ == "__main__":
    run()
