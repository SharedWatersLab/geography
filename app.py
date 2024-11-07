import streamlit as st
import os
from utils import get_user, full_process

st.title("Nexus-Uni Downloader")

dload_type = st.selectbox("Select download type:", ["excel", "pdf"])
uname = st.text_input("Enter username:")
basin = st.selectbox("Select basin code:", [p.removesuffix(".csv") for p in os.listdir(f"./data/status/{dload_type}")])

if st.button("Start Download"):
    if uname:
        paths, current_user = get_user(basin, uname, dload_type)
        with st.spinner("Downloading..."):
            full_process(current_user)
        st.success("Download completed successfully!")
    else:
        st.error("Please enter a username.") 