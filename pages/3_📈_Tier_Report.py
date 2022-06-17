import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid

def tier_page():

    DM = st.session_state.DM

    # Choose Year
    select_year = st.selectbox()

    st.markdown('### Tier 1 Table (£50k+)')
    AgGrid(DM[DM['Y'==select_year && 'Credit Amount'>=50000]])

    st.markdown('### Tier 2 Table (£20k+)')
    AgGrid(DM[DM['Y'==select_year && 'Credit Amount'>=20000]])

    st.markdown('### Tier 3 Table (£2k+)')
    AgGrid(DM[DM['Y'==select_year && 'Credit Amount'>=2000]])

    st.markdown('### Tier 4 Table (£400+)')
    AgGrid(DM[DM['Y'==select_year && 'Credit Amount'>=400]])

    st.markdown('### Tier 5 Table (<£400)')
    AgGrid(DM[DM['Y'==select_year && 'Credit Amount'<400]])

    st.subheader('Custom Slider')

    #custom_range = st.slider()

    # Table with Slider

    # Pie chart with share - reacts to slider