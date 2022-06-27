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
                    col = str(col)
                    #gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                    gb.configure_column(col,type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=0)
                else:
                    gb.configure_column(col,pinned=True)
        
        gb.configure_column('Total',pinned=True)

        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(600,32*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

def individuals_annual():

    view = st.radio('Choose View:',['Table','Chart'],horizontal=True)

    # Retrive Individual summed data from session_state
    input_data = st.session_state.data

    # Sum by Year - Month
    df = input_data.groupby(['Renamer','Y']).sum().reset_index()
    df['Year'] = df['Y'].astype(int)
    #df['Year'] = df["Y"].astype(str) + '01' + '01'
    #df['Year'] = df['Year'].apply(lambda x: datetime.strptime(x,"%Y%m%d").date())

    output = df.pivot(index='Renamer',columns='Year',values='Credit Amount').reset_index().fillna(0)

    # Cast to Wide and flip order: https://www.geeksforgeeks.org/how-to-reverse-the-column-order-of-the-pandas-dataframe/
    values = output.iloc[:,1:]  
    output = pd.concat([output['Renamer'],values[values.columns[::-1]]],axis=1)

    # Calculate Total column to rank table by
    total = df[['Renamer','Credit Amount']].groupby(['Renamer']).sum().reset_index()
    total.columns = ['Renamer','Total']
    output.insert(1,"Total",total['Total'])
    output = output.sort_values(by='Total',ascending=False)

    output.columns = output.columns.astype(str)

    if view == 'Table':

        AgGrid_default(output)

        # Possible future To-Do: load chart from interactive chart
        # Example: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/example.py
    
    else:
   
        # Multiselect Donors: https://docs.streamlit.io/library/api-reference/widgets/st.multiselect
        Donors = st.multiselect('Select Donors:',output['Renamer'].tolist(),output['Renamer'].tolist()[0:3])

        # Slider select daterange
        # date_range = st.date_input("Date Range:",value=[datetime.strptime('20160101',"%Y%m%d").date(),max(df['Year'])],
        # min_value=min(df['Year']), 
        # max_value=max(df['Year']))

        # Whole year daterange
        date_range = st.slider('', min_value=min(df['Year']), max_value=max(df['Year']), value=[min(df['Year']),max(df['Year'])], step=1)

        plot_df = df[(df['Year']>=date_range[0]) & (df['Year']<=date_range[1])].pivot(index='Year',columns='Renamer',values='Credit Amount').fillna(0)

        fig = px.bar(plot_df[Donors], facet_row="Renamer", facet_row_spacing=0.02,height=550)

        # hide and lock down axes and remove facet/subplot labels
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(title="",matches=None)
        fig.update_layout(annotations=[], overwrite=True)
        fig.update_layout(legend=dict(x=-0.40),margin=dict(r=0,l=30,t=10,b=10))

        # disable the modebar for such a small plot
        st.plotly_chart(fig,use_container_width=True)

st.set_page_config(page_title="Individuals (Annual)", page_icon="👫",layout='centered')

st.title('Individuals Annual')

if 'password_check' in st.session_state:
    individuals_annual()
else:
    st.subheader('Error: Go to Home to enter Password')