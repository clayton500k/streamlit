import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

def AgGrid_default(DF):
        gb = GridOptionsBuilder.from_dataframe(DF)
        gb.configure_grid_options(enableRangeSelection=True)
        
        for col in DF.columns:
                if (col!='Renamer') & (col!='Y'):
                    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                    
        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(400,32*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

# Donation Matrix by Individual
def individuals_page():

    # Retrive Individual summed data from session_state
    DM = st.session_state.DM

    # Choose Individual with streamlit selectbox: 
    # https://docs.streamlit.io/library/api-reference/widgets/st.selectbox
    individual = st.selectbox('',DM['Renamer'].unique(),index=list(DM['Renamer'].unique()).index('Edward Foster')) #header instructs

    # filter for selected individual
    view_individual_data = DM[DM['Renamer']==individual]
    
    # plot with integer x-axis
    view_individual_data['Y'] = view_individual_data['Y'].astype(int)
    fig = px.bar(view_individual_data, x="Y", y="Credit Amount", color="Source Type")
    fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=10,b=10))
    st.plotly_chart(fig,use_container_width=True)

    AgGrid_default(view_individual_data) 

st.title('By Individual')

if 'password_check' in st.session_state:
    individuals_page()
else:
    st.subheader('Error: Go to Home to enter Password')
