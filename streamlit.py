import streamlit as st
import pandas as pd

import connect_bdd

# streamlit run .\streamlit.py --server.enableStaticServing true


def main():

    st.set_page_config(
    page_icon="🧊",
    layout="wide",)

    st.title("Visualisation des recettes de production")

    df_items = connect_bdd.load_df("items")
    for i,url in enumerate(df_items["url_img"]):
        df_items["url_img"][i] = "app/"+url

    # st.write(df_items)

    st.title("items")
    st.data_editor(df_items[["name", "url_img"]],
                   column_config={"url_img": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots")},
                   hide_index=True,
                   )

    df_buildings = connect_bdd.load_df("buildings")
    for i,url in enumerate(df_buildings["url_img"]):
        df_buildings["url_img"][i] = "app/"+url
    st.title("buildings")
    st.data_editor(df_buildings,
                   column_config={"url_img": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots")},
                   hide_index=True,
                   width=1000
                   )

    df_recipes = connect_bdd.load_df("recipes")
    st.title("recipes")
    st.write(df_recipes)



if __name__ == "__main__":
    main()