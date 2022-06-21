import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid

# Donation Matrix by Individual
def overall_page():

    #Donation Matrix Overall 
    #@st.cache
    def overall_data():
        data = st.session_state.data
        DMY = data.groupby(['Y']).sum().reset_index()
        DMY = pd.melt(DMY,id_vars = ['Y'],var_name='Group')

        fig = px.bar(DMY, x="Y", y="value",
                    color='Group', barmode='group',
                    height=400)
        
        fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15))
        
        return fig
    
    fig = overall_data()

    st.plotly_chart(fig, use_container_width=True)

st.title('Overall')

if 'password_check' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to enter Password')
