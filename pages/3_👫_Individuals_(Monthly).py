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
from st_aggrid.grid_options_builder import GridOptionsBuilder
from PIL import Image
import time 

# leading 0 for Jan-Sept
def leading_zero(x):
    if pd.to_numeric(x) < 10:
        x = '0' + str(x)
    return x

def AgGrid_default(DF):
        gb = GridOptionsBuilder.from_dataframe(DF)
        gb.configure_grid_options(enableRangeSelection=True)
        
        for col in DF.columns:
                if (col!='Renamer') & (col!='Y'):
                    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                    
        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(600,32*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

def individuals_monthly():

    view = st.radio('Choose View:',['Table','Chart'],horizontal=True)

    if view == 'Table':

        # Retrive Individual summed data from session_state
        input_data = st.session_state.data

        # Sum by Year - Month
        df = input_data.groupby(['Renamer','Y','M']).sum().reset_index()
        
        # Cast to Wide
        df['M'] = df['M'].apply(leading_zero)
        df['Month'] = df["Y"].astype(str) + df["M"]
        output = df.pivot(index='Renamer',columns='Month',values='Credit Amount').reset_index().fillna(0)

        # Flip order: https://www.geeksforgeeks.org/how-to-reverse-the-column-order-of-the-pandas-dataframe/
        values = output.iloc[:,1:]  
        output = pd.concat([output['Renamer'],values[values.columns[::-1]]],axis=1)

        output.columns = output.columns.astype(str)

        AgGrid_default(output)

st.set_page_config(layout='wide')

st.title('Individuals Monthly')

if 'password_check' in st.session_state:
    individuals_monthly()
else:
    st.subheader('Error: Go to Home to enter Password')