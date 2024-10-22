import streamlit as st
from loguru import logger
from streamlit_option_menu import option_menu
from PIL import Image
import sys
import os

from gestion_satisfactory.utils.config.load_pages_config import (
    display_sidebar_header,
    footer_streamlit_style,
    load_pages_config,
)
from gestion_satisfactory.web_pages import recipes_optimizer, factory_planner


# Set up logging
logger.add("logs/app.log", rotation="10 MB", level="INFO")


def main():
    st.set_page_config(
        page_title="Satisfactory - Gestion Project",
        page_icon=Image.open("conf/static/logo_gestion_satisfactory.png"),
        initial_sidebar_state="expanded",
        layout="wide",
    )
    # Hide developer options menu (right side) and footer
    custom_style = footer_streamlit_style(
        show_main_menu=True
    )  # set to False to hide dev menu
    st.markdown(custom_style, unsafe_allow_html=True)

    # Load page config from pages.toml
    pages_config = load_pages_config()
    v_menu = [page["name"] for page in pages_config["pages"]]
    icons = [page["icon"] for page in pages_config["pages"]]

    with st.sidebar:
        # display_sidebar_header()
        
        selected = option_menu(
            menu_title="Menu",  # required
            options=v_menu,  # required
            icons=icons,  # optional
            menu_icon="app-indicator",  # optional
            default_index=0,  # optional
            styles={
                # "container": {"padding": "5!important", "background-color": "#fafafa"},
                # "icon": {"color": "purple", "font-size": "15px"},
                # "text": {"color": "purple"},
                "nav-link": {
                    # "font-color": "purple",
                    # "font-size": "18px",
                    # "text-align": "left",
                    # "margin": "0px",
                    "--hover-color": "#e8e8c2",
                },
                # "nav-link-selected": {"background-color": "#31F1CB"},
            },
        )

    if selected == v_menu[0]:
        recipes_optimizer.create_page(title=selected)

    if selected == v_menu[1]:
        factory_planner.create_page(title=selected)


if __name__ == "__main__":
    main()
