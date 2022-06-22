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

    #Sum over Source Type
    DM = DM.drop(columns=['Debit Amount','Source Type'])
    DM = DM.groupby(['Renamer','Y']).sum().reset_index()
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)
    DM['Category'] = DM['Credit Amount'].apply(categorize_donor)
    DM = DM[DM['Credit Amount']!=0] #eliminate zeros to reduce table length

    # User Input Year
    year_list = ['All',2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index('All'))

    # horizontal radio buttons: https://discuss.streamlit.io/t/horizontal-radio-buttons/2114
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

    if select_year=='All':
        df2 = DM.groupby(['Y','Category']).sum().reset_index()
        df2 = df2.sort_values(by=['Category'])
        df2['Category'] = df2['Category'].astype(str)
        fig = px.bar(df2, x="Y", y="Credit Amount", color="Category")
        fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
        fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
        st.plotly_chart(fig,use_container_width=True)
    else:
        tier = st.radio("Select Tier",[1,2,3,4,5])
        df = DM[(DM['Y']==select_year) & (DM['Category']==tier)]
        df_total = pd.to_numeric(df['Credit Amount'].sum())
        
        st.markdown(f'### Tier {tier} Table: Total = £{df_total:,.2f}')

        AgGrid(df.drop(columns=['Category']),fit_columns_on_grid_load=True,height=min(400,32*(1+len(df))))
        # 32 hardcoded as the pixel size of one row, +1 for header
    
        
st.set_page_config(page_title="Tier Report", page_icon="💼")

st.title('Tier Report')

if 'password_check' in st.session_state:
    tier_page()
    st.markdown("<h5 style='text-align: center;'> Tier 1: £50k+ | Tier 2: £20k+ | Tier 3: £2k+ | Tier 4: £400+ | Tier 5: <£400 </h5>", unsafe_allow_html=True)
else:
    st.subheader('Error: Go to Home to enter Password')

