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

def tier_page():

    DM = st.session_state.DM

    # Sum over Source Type
    DM = DM.drop(columns=['Debit Amount','Source Type'])
    DM = DM.groupby(['Renamer','Y']).sum().reset_index()
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)

    # Create Category Column
    DM['Category'] = DM['Credit Amount'].apply(categorize_donor)
    
    # Eliminate zeros to reduce table length for Tier 5
    DM = DM[DM['Credit Amount']!=0] 

    # User Input Year
    year_list = ['All',2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index('All'))

    if select_year=='All':
        
        # Sum by Category and Year
        df2 = DM.groupby(['Y','Category']).sum().reset_index()
        df2 = df2.sort_values(by=['Category'])
        df2['Category'] = df2['Category'].astype(str)
       
        # Plot
        fig = px.bar(df2, x="Y", y="Credit Amount", color="Category")
        fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
        fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
        st.plotly_chart(fig,use_container_width=True)
    
    else:
    
        # User Radio to enable User Tier Selection: https://docs.streamlit.io/library/api-reference/widgets/st.radio
        tier = st.radio("Select Tier", [1,2,3,4,5], horizontal=True)
        
        #Filter and sum
        df = DM[(DM['Y']==select_year) & (DM['Category']==tier)]
        df_total = pd.to_numeric(df['Credit Amount'].sum())
        df = df.drop(columns=['Category'])

        st.markdown(f'### Tier {tier} Table: Total = £{df_total:,.2f}')

        #Add Copy to Clipboard table
        AgGrid_default(df)
        
st.set_page_config(page_title="Tier Report", page_icon="💼")

st.title('Tier Report')

if 'password_check' in st.session_state:
    tier_page()
    
    # Tier Key at bottom
    st.markdown("<h5 style='text-align: center;'> Tier 1: £50k+ | Tier 2: £20k+ | Tier 3: £2k+ | Tier 4: £400+ | Tier 5: <£400 </h5>", unsafe_allow_html=True)

else:
    st.subheader('Error: Go to Home to enter Password')

