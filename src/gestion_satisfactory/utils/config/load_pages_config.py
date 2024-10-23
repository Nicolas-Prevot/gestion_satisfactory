from typing import Optional, Dict
import requests
import streamlit as st
import toml


def load_lottieurl(url: str) -> Optional[Dict]:
    """
    Load a Lottie animation from a URL.

    Parameters
    ----------
    url : str
        The URL of the Lottie animation file.

    Returns
    -------
    dict or None
        A dictionary containing the Lottie animation data if successful; otherwise, None.

    """
    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()


def load_pages_config() -> Dict:
    """
    Load and parse the page configuration from a TOML file.

    This function reads the 'pages.toml' file located in the '.streamlit' directory
    and parses it to extract the configuration of pages. The configuration
    includes details such as the path, name, and icon for each page.

    Returns
    -------
    dict
        A dictionary containing the parsed page configuration. Each key in the
        dictionary represents a different aspect of the page configuration (e.g.,
        'path', 'name', 'icon') with corresponding values.

    """
    with open(".streamlit/pages.toml", "r") as file:
        pages_config = toml.load(file)
    return pages_config


def footer_streamlit_style(show_main_menu: bool = False) -> str:
    """
    Customizes the footer of a Streamlit application.

    This function generates a style tag as a string that hides the default
    Streamlit footer and optionally the main menu.

    Parameters
    ----------
    show_main_menu : bool, optional
        A flag to determine if the main menu of the Streamlit application should be
        visible or not. Default is False, which means the main menu will be hidden.

    Returns
    -------
    str
        A string containing the HTML <style> tag with the customized CSS to hide
        the default Streamlit footer (and optionally the main menu),
        and replace it with a custom footer message.

    Notes
    -----
    The function defaults to hiding both the main menu and the footer if `show_main_menu`
    is False. If `show_main_menu` is True, only the footer is hidden and replaced.

    The custom footer message is set to '[CLOSED-BETA] Version, by Nicolas PREVOT'.

    Example
    -------
    >>> custom_style = footer_streamlit_style(show_main_menu=False)
    >>> st.markdown(custom_style, unsafe_allow_html=True)

    This will hide the default Streamlit footer and display the custom footer,
    while keeping the main menu visible.
    """

    if show_main_menu:
        hide_streamlit_style = """
                <style>
                footer {visibility: hidden;}
                footer:after {
                        content:'[CLOSED-BETA] Version, by Nicolas PREVOT';
                        visibility: visible;
                        display: block;
                        position: relative;
                        #background-color: red;
                        padding: 5px;
                        top: 2px;}
                </style>
                """
    else:
        hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                footer:after {
                        content:'[CLOSED-BETA] Version, by Nicolas PREVOT';
                        visibility: visible;
                        display: block;
                        position: relative;
                        #background-color: red;F
                        padding: 5px;
                        top: 2px;}
                </style>
                """
    return hide_streamlit_style


def display_sidebar_header(display_links: bool = False) -> None:
    """
    Display the sidebar header/footer in the Streamlit app.

    Parameters
    ----------
    display_links : bool, optional
        If True, display additional links in the sidebar; otherwise, do not display.
        Default is False.

    Returns
    -------
    None
    
    """
    with st.sidebar:
        # Logo
        st.image(
            "conf/****.png", use_column_width=True
        )

        # Nice to have links
        if display_links:
            pass
