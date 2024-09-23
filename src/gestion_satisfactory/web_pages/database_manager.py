import streamlit as st
from PIL import Image
import os

from gestion_satisfactory.utils.update_bdd_from_web import main


def create_page(title: str) -> None:
    """
    Create a streamlit page.

    Parameters
    ----------
    title: str, optional
        The title of the page.

    """
    title = "Getting data from Satisfactory wiki"
    st.write(
        f"""<h1 style='text-align: center;'>
        🌴🤖 <i>{title}</i> 🖥️🔋
        </h1>""",
        unsafe_allow_html=True,
        )
    st.link_button(label="Satisfactory wiki", url="https://satisfactory.wiki.gg/wiki/Satisfactory_Wiki")
    if (st.button(label="Fetch data")):
        with st.status("Downloading data...", expanded=True) as status:
            main(streamlit_display=True)
        
        st.success('Done !', icon='✅')