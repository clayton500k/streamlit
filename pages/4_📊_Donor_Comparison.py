import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Select Year

# New Donors

# Increased 

# Decreased

def dc_page():
   
    # User Input Year
    year_list = [2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index(2022))

    DM = st.session_state.DM
    DM['Y'] = DM['Y'].astype(int)
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)

    selected_data = DM[(DM['Y']==select_year) | (DM['Y']==(select_year-1))]

    # Sum over all Source Types
    df = selected_data.groupby(['Renamer','Y']).sum().reset_index()

    output = df.pivot(index='Renamer',columns='Y',values='Credit Amount').reset_index().fillna(0)

    output['Delta'] = output[select_year] - output[(select_year-1)]

    output.columns = output.columns.astype(str)

    # Plot Lollipop Chart
    #https://towardsdatascience.com/lollipop-dumbbell-charts-with-plotly-696039d5f85

    #Format as Currency
    # GridOptionsBuilder.from_dataframe(output) 
    # gb.configure_column("Delta", 
    # type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=1)
    # AgGrid(output.sort_values(by=['Delta'],ascending=False))
    
    st.table(output.sort_values(by=['Delta'],ascending=False))

st.set_page_config(page_title="Donor Comparison", page_icon="📊")

st.title('Donor Comparison')

if 'password_check' in st.session_state:
    dc_page()
else:
    st.subheader('Error: Go to Home to enter Password')