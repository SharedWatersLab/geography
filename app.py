import streamlit as st
import os
from utils import get_user, full_process

st.title("Nexis-Uni Downloader")

uname = st.text_input("Enter username:")

with open("basins.txt", "r") as f:
    basins = [b.strip() for b in f.readlines()]
    
# basins = [
#     "amur", "bakr", "buzi", "caxx", "cnct", "cull" "dnpr", 
#     "donx", "drin", "elbe", "emsx", "frth", "gamb", "gash"
# ]
basin = st.selectbox("Select basin code:", basins)

if st.button("Start Download"):
    if uname:
        paths, current_user = get_user(basin, uname, "pdf")
        with st.spinner("Downloading..."):
            full_process(current_user, paths)
        st.success("Download completed successfully!")
    else:
        st.error("Please enter a username.") 