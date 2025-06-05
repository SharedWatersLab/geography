import streamlit as st
import os
from utils import get_user, full_process

st.title("Nexis-Uni Downloader")

uname = st.text_input("Enter username:")

with open("basins.txt", "r") as f:
    basins = [b.strip() for b in f.readlines()]
    
#basin = st.selectbox("Select basin code:", basins)
chosen_basins = st.multiselect("Select basin code(s):", basins)

if st.button("Start Download"):
    if uname:
        
        with st.spinner("Downloading..."):
            for basin in chosen_basins:
                paths, username = get_user(basin, uname)
                full_process(basin, username, paths) 
        #st.success("Download completed successfully!")
    else:
        st.error("Please enter a username.") 