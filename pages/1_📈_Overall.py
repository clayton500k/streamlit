import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time 
from datetime import datetime

def AgGrid_default(DF):
        gb = GridOptionsBuilder.from_dataframe(DF)
        gb.configure_grid_options(enableRangeSelection=True)
        
        for col in DF.columns:
                if (col!='Source Type') & (col!='Y') & (st.session_state["currency_choice"]=='GBP'):
                    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                elif (col!='Source Type') & (col!='Y') & (st.session_state["currency_choice"]=='USD'):
                    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="$", aggFunc='max')
                else:
                    gb.configure_column(col,pinned=True)

        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(600,32*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

def overall_page():

    page_view = st.radio('Choose View:',['Income & Expenditure','Income by Source Type','Income by Core Vs Project','Expense by Source Type'],horizontal=True)

    # Retrive data from session_state
    data = st.session_state.data

    if page_view=='Income & Expenditure':

        # Calculate Overall Income and Expenditure by Year         
        df2 = data[['Y','Credit Amount','Debit Amount']].groupby(['Y']).sum().reset_index()
        df3 = pd.melt(df2, id_vars = ['Y'], var_name='Group')
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(df3, x="Y", y="value", color='Group', barmode='group', height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig, use_container_width=True)

        AgGrid_default(df2)
    
    elif page_view=='Income by Source Type':

        # Calculate Income by Year & Source Type
        df4 = data[['Y','Credit Amount','Source Type']].groupby(['Y','Source Type']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig2 = px.bar(df4, x="Y", y="Credit Amount", color='Source Type', height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig2 = fig2.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig2, use_container_width=True)

        df5 = df4.pivot(index='Source Type',columns='Y',values='Credit Amount').reset_index().fillna(0)
        df5.columns = df5.columns.astype(str)

        AgGrid_default(df5)

    elif page_view=='Expense by Source Type':

        # Calculate Income by Year & Source Type
        df6 = data[['Y','Debit Amount','Source Type']].groupby(['Y','Source Type']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig3 = px.bar(df6, x="Y", y="Debit Amount", color='Source Type', height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig3 = fig3.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig3, use_container_width=True)

        df7 = df6.pivot(index='Source Type',columns='Y',values='Debit Amount').reset_index().fillna(0)
        df7.columns = df7.columns.astype(str)

        AgGrid_default(df7) 
    elif page_view=='Income by Core Vs Project':

        # Calculate Income by Year & Core/Project
        df8 = data[['Y','Credit Amount','Core/Project']].groupby(['Y','Core/Project']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig2 = px.bar(df8, x="Y", y="Credit Amount", color='Core/Project', height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig2 = fig2.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig2, use_container_width=True)

        df9 = df8.pivot(index='Core/Project',columns='Y',values='Credit Amount').reset_index().fillna(0)
        df9.columns = df9.columns.astype(str)

        AgGrid_default(df9)
    

st.set_page_config(page_title="Overall", page_icon="📈",layout='centered')

st.title('Overall')

if 'password_check' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to enter Password')
