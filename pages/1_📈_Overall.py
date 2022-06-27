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

def overall_page():

    # Calculate Overall Income and Expenditure by Year 
    def overall_data():

        # Retrive data from session_state
        data = st.session_state.data
        DMY = data[['Y','Credit Amount','Debit Amount']]
        DMY = DMY.groupby(['Y']).sum().reset_index()
        DMY = pd.melt(DMY, id_vars = ['Y'], var_name='Group')

        return DMY

    df2 = overall_data()
    
    # Plotly bar chart: https://plotly.com/python/bar-charts/
    fig = px.bar(df2, x="Y", y="value", color='Group', barmode='group', height=400)
    
    # Legend positioning: https://plotly.com/python/legend/
    fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
    
    st.plotly_chart(fig, use_container_width=True)

st.set_page_config(page_title="Overall", page_icon="📈",layout='centered')

st.title('Overall')

if 'password_check' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to enter Password')
