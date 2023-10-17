import streamlit as st
from pathlib import Path
from PIL import Image
import sys
import os

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        if (sys.argv[1] == "__setEnv"):
            print(f"{os.path.realpath(os.path.dirname(__file__))}\\..\\.env")
            try:
                with open(f"{os.path.realpath(os.path.dirname(__file__))}\\..\\.env") as file:
                    lines = file.readlines()
                    for line in lines:
                        os.environ[line.split("=")[0]] = line.split("=")[1].split("\n")[0]
                os.environ["HOST"] = "localhost"
            except Exception as error:
                print(error)
            print(list(os.environ.items())[-len(lines):])
    
    st.set_page_config(
    page_icon=Image.open("pages/logo.png"),
    layout="wide",
    initial_sidebar_state="auto",)

    try:
        intro_markdown = Path("readme.md").read_text()
        st.markdown(intro_markdown, unsafe_allow_html=True)
    except:
        st.write("Coming soon...")