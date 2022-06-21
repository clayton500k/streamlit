import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

def categorize_donor(x):
    if x >= 50000:
        cat = 1
    elif x >= 20000:
        cat = 2
    elif x >= 2000:
        cat = 3
    elif x >= 400:
        cat = 4
    else:
        cat = 5
    return cat

def tier_page():

    DM = st.session_state.DM
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)
    DM['Category'] = DM['Credit Amount'].apply(categorize_donor)
    DM = DM.drop(columns=['Debit Amount'])
    DM = DM[DM['Credit Amount']!=0] #eliminate zeros to reduce table length

    # User Input Year
    year_list = [2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index(2022))

    for i in range(4):
        df = DM[(DM['Y']==select_year) & (DM['Category']==(i+1))]
        df_total = pd.to_numeric(df['Credit Amount'].sum())
        df['Credit Amount'] = df['Credit Amount'].apply(lambda x: "${:,.2f}".format(float(x)))
        
        st.markdown(f'### Tier {(i+1)} Table: Total = ${df_total:,.2f}')

        #Left align
        def left_align(s, props='text-align: left;'):
            return props

        #Add pagination
        # gb = GridOptionsBuilder.from_dataframe(df)
        # gb.configure_pagination()
        # gridOptions = gb.build()

        AgGrid(
        df, 
        fit_columns_on_grid_load=True, 
        height=min(400,32*(1+len(df))) # 32 hardcoded as the pixel size of one row, +1 for header
        # ,gridOptions=gridOptions
        )

    st.subheader('Stacked Column Chart')

    # Stacked Column Chart by year

st.set_page_config(page_title="Tier Report", page_icon="📈")

st.title('Tier Report')

if 'password_check' in st.session_state:
    tier_page()
else:
    st.subheader('Error: Go to Home to enter Password')