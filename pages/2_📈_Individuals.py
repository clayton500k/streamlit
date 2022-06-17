import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid

# Donation Matrix by Individual
def individuals_page():

    DM = data = st.session_state.DM

    individual = st.selectbox('',DM['Renamer'].unique(),index=list(DM['Renamer'].unique()).index('Edward Foster')) #header instructs

    view_individual_data = DM[DM['Renamer']==individual]

    st.plotly_chart(px.bar(view_individual_data, x="Y", y="Credit Amount", color="Source Type", height=400))

    AgGrid(view_individual_data)

st.set_page_config(page_title="Individuals", page_icon="📈")

st.title('By Individual')

st.sidebar.header("By Individual")

if 'password_check' in st.session_state:
    individuals_page()
else:
    st.subheader('Error: Go to Home to enter Password')
