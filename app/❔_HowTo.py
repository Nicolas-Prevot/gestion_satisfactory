import streamlit as st
from pathlib import Path
from PIL import Image

if __name__ == "__main__":
    st.set_page_config(
    page_icon=Image.open("pages/logo.png"),
    layout="wide",
    initial_sidebar_state="auto",)

    try:
        intro_markdown = Path("readme.md").read_text()
        st.markdown(intro_markdown, unsafe_allow_html=True)
    except:
        st.write("Coming soon...")