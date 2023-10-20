import streamlit as st
from PIL import Image
import os

from utils.update_bdd_from_web import main


if __name__ == "__main__":
    st.set_page_config(
        page_icon=Image.open(f"{os.path.realpath(os.path.dirname(__file__))}\\logo.png"),
        layout="wide",
        initial_sidebar_state="auto",
    )

    st.title("Getting data from Satisfactory wiki")
    st.link_button(label="Satisfactory wiki", url="https://satisfactory.fandom.com/wiki/Satisfactory_Wiki")
    if (st.button(label="Fetch data")):
        with st.status("Downloading data...", expanded=True) as status:
            main(streamlit_display=True)
        
        st.success('Done !', icon='✅')