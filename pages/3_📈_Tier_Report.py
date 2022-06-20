import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid

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
    DM = DM.sort_values(by=['Credit Amount'], ascending=False) #order
    DM['Category'] = DM['Credit Amount'].apply(categorize_donor)
    DM = DM.drop(columns=['Debit Amount'])

    # Choose Year
    year_list = [2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index(2022))

    cat1 = DM[(DM['Y']==select_year) & (DM['Category']==1)]
    cat1_total = cat1['Credit Amount'].sum()
    st.markdown(f'### Tier 1 Table (£50k+): Total = {cat1_total}')
    st.dataframe(cat1)

    cat2 = DM[(DM['Y']==select_year) & (DM['Category']==2)]
    cat2_total = cat2['Credit Amount'].sum()
    st.markdown(f'### Tier 2 Table (£20k+): Total = {cat2_total}')
    st.dataframe(cat2)

    cat3 = DM[(DM['Y']==select_year) & (DM['Category']==3)]
    cat3_total = cat3['Credit Amount'].sum()
    st.markdown(f'### Tier 3 Table (£2k+): Total = {cat3_total}')
    st.dataframe(cat3)

    cat4 = DM[(DM['Y']==select_year) & (DM['Category']==4)]
    cat4_total = cat4['Credit Amount'].sum()
    st.markdown(f'### Tier 4 Table (£400+): Total = {cat4_total}')
    st.dataframe(cat4)

    cat5 = DM[(DM['Y']==select_year) & (DM['Category']==5)]
    cat5_total = cat5['Credit Amount'].sum()
    st.markdown(f'### Tier 5 Table (<£400): Total = {cat5_total}')
    st.dataframe(cat5)

    st.subheader('# Stacked Column Chart')

    # Stacked Column Chart by year

st.set_page_config(page_title="Tier Report", page_icon="📈")

st.title('Tier Report')

if 'password_check' in st.session_state:
    tier_page()
else:
    st.subheader('Error: Go to Home to enter Password')