import streamlit as st

import update_bdd_from_web

if __name__ == "__main__":
    st.title("Getting data from Satisfactory wiki")
    st.link_button(label="Satisfactory wiki", url="https://satisfactory.fandom.com/wiki/Satisfactory_Wiki")
    if (st.button(label="Fetch data")):
        with st.status("Downloading data...", expanded=True) as status:
            update_bdd_from_web.main(streamlit_display=True)
        
        st.success('Done !', icon='✅')