import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode
from streamlit_agraph import agraph

import pandas as pd
import base64

import connect_bdd
from utils.recipes_search import get_recipes, get_rec_recipes, create_raws_recipes
from utils.graph import create_genealogy_graph

# streamlit run .\streamlit.py --server.enableStaticServing true --server.port 1885


def ReadPictureFile(wch_fl):
    try:
        return base64.b64encode(open(wch_fl, 'rb').read()).decode()

    except:
        return ""


def main():

    st.set_page_config(
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="auto",)

    # st.title("Visualisation des recettes de production")

    df_items = connect_bdd.load_df("items")
    new_path = []
    new_path_web = []
    for i,url in enumerate(df_items["url_img"]):
        new_path.append("app/"+url)
        imgExtn = url[-4:]
        new_path_web.append(f'data:image/{imgExtn};base64,' + ReadPictureFile(url))
    df_items["streamlit_path_img"] = new_path
    df_items["web_img"] = new_path_web

    item_to_img = {}
    for i,row in df_items.iterrows():
        item_to_img[row["name"]] = row["web_img"]

    # st.write(df_items)

    # st.title("items")
    # st.data_editor(df_items[["name", "streamlit_path_img"]],
    #                column_config={"streamlit_path_img": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots")},
    #                hide_index=True,
    #                )

    df_buildings = connect_bdd.load_df("buildings")
    new_path = []
    for i,url in enumerate(df_buildings["url_img"]):
        new_path.append("app/"+url)
    df_buildings["streamlit_path_img"] = new_path
    st.title("buildings")
    st.data_editor(df_buildings[["name", "base_power_use", "streamlit_path_img"]],
                   column_config={"streamlit_path_img": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots")},
                   hide_index=True,
                   width=1000
                   )

    df_recipes = connect_bdd.load_df("recipes")
    st.title("recipes")
    st.write(df_recipes)

    # st.selectbox(   label="Get an item recipes",
    #                 options=df_items["name"],
    #                 index=0)

    thumbnail_renderer = JsCode("""
        class ThumbnailRenderer {
            init(params) {
                this.eGui = document.createElement('img');
                this.eGui.setAttribute('src', params.value);
                this.eGui.setAttribute('width', '27');
                this.eGui.setAttribute('height', 'auto');
            }
            getGui() {
                return this.eGui;
            }
        }
        """)

    gb = GridOptionsBuilder.from_dataframe(df_items[["name", "web_img"]])

    gb.configure_column("web_img", cellRenderer=thumbnail_renderer)
    gb.configure_default_column(editable=False, min_column_width=5)
    gb.configure_selection("single")
    grid_options = gb.build()


    st.title("Select Recipe")

    col1, col2 = st.columns(spec=[1,3])

    with col1:
        response = AgGrid(df_items[["name", "web_img"]],
                        theme="streamlit",
                        #key='table1',
                        fit_columns_on_grid_load=True,
                        # width=200,
                        height=600,
                        gridOptions=grid_options,
                        allow_unsafe_jscode=True,
                        reload_data=False,
                        #try_to_convert_back_to_original_types=False
                        )

    with col2:

        tab1, tab2, tab3 = st.tabs(["Recipe", "Genealogy", "Raw rates"])

        with tab1:
            if len(response["selected_rows"]) == 1:
                item_name = response["selected_rows"][0]["name"]
                rows = get_recipes(item_name, df_recipes, blacklist_building=[])

                # Définir le style CSS pour le conteneur
                container_style = """
                    display: flex;
                    align-items: center;
                """
                # Définir le style CSS pour les items sortants
                out_item_style = """
                    margin: 20px;
                """
                # Définir le style CSS pour les items entrants
                in_item_style = """
                    margin: 20px;
                """
                for index, row in rows.iterrows():

                    out_items = f''
                    for i in range(1,3):
                        item = row[f"item_out_{i}"]
                        if item is None:
                            break
                        src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]

                        rate = row[f"rate_out_{i}"]
                        out_items += f'{rate} <figure class="image" style="{out_item_style}"><img src="{src_img}" width=50px><figcaption style="font-size: 12px;">{item}</figcaption></figure>'
                    
                    in_items = ""
                    for i in range(1,5):
                        item = row[f"item_in_{i}"]
                        if item is None:
                            break
                        src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]
                        
                        rate = row[f"rate_in_{i}"]
                        in_items += f'{rate} <figure class="image" style="{in_item_style}"><img src="{src_img}" width=50px><figcaption style="font-size: 12px;">{item}</figcaption></figure>'

                    src_img = df_buildings[df_buildings["name"] == row["building"]]["streamlit_path_img"].tolist()[0]
                    st.markdown(f'<div style="{container_style}">{row["name"]}, {"🔄" if row["alternate"] else "🟦"} {out_items}: <img src="{src_img}" width=80px> {in_items}</div>', unsafe_allow_html=True)
        
        with tab2:
            blacklist_potential = ["Water", "Empty_Canister"]
            blacklist = []
            for item_blacklist in blacklist_potential:
                accept = st.checkbox(item_blacklist)
                if not accept:
                    blacklist.append(item_blacklist)

            if len(response["selected_rows"]) == 1:
                item_name = response["selected_rows"][0]["name"]
                recipes = get_rec_recipes(item_name, df_recipes, blacklist)
                # st.write(recipes)
                nodes, edges, config = create_genealogy_graph(recipes, item_to_img, blacklist)
                return_value = agraph(nodes=nodes, edges=edges, config=config)
                st.write(return_value)
        
        with tab3:
            if len(response["selected_rows"]) == 1 and st.button('Compute'):
                item_name = response["selected_rows"][0]["name"]
                # recipes = get_rec_recipes(item_name, df_recipes, blacklist)
                # st.write(recipes)
                blacklist = ["Water", "Empty_Canister"]
                raws_forced = ["Plastic", "Rubber"]
                res = create_raws_recipes(item_name, df_recipes, blacklist, raws_forced=raws_forced)
                st.write(res)

if __name__ == "__main__":
    main()