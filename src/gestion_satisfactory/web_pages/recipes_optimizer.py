import streamlit as st
from streamlit_agraph import agraph

import os
import pandas as pd
import numpy as np
from PIL import Image

from gestion_satisfactory.utils.optimize import get_items, get_recipes_vect, get_best_production
from gestion_satisfactory.utils.load_df import get_df_from_tables
from gestion_satisfactory.utils.grids import item_selector
from gestion_satisfactory.utils.graph import create_recipe_optimize
from gestion_satisfactory.utils.display import display_recipes_frame

list_item_type_1 = ['Raw_Quartz','Bauxite','Crude_Oil','Iron_Ore','Coal','Uranium','Sulfur','Nitrogen_Gas','Water','Caterium_Ore','Limestone','Copper_Ore']
list_item_type_2 = ['Wood','Blue_Power_Slug','Plasma_Spitter_Remains','Purple_Power_Slug','Flower_Petals','Stinger_Remains','Yellow_Power_Slug','Mycelia','Hog_Remains','Hatcher_Remains','Leaves']
list_item_type_1_value = [2.,3.,0.5,1.,1.,10.,1.,2.,0.,2.,1.,1.]
list_item_type_2_value = [1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]

@st.cache_data
def cached_get_df_from_tables():
    return get_df_from_tables()


def create_page(title: str) -> None:
    """
    Create a streamlit page.

    Parameters
    ----------
    title: str, optional
        The title of the page.

    """
    title = "Optimize your production recipes"
    st.write(
        f"""<h1 style='text-align: center;'>
        🌴🤖 <i>{title}</i> 🖥️🔋
        </h1>""",
        unsafe_allow_html=True,
        )

    try:
        df_items, df_buildings, df_recipes = cached_get_df_from_tables()
    except:
        st.error("There is no database, go to 🛠️_Database_manager and 'Fetch data'")
        st.stop()

    with st.expander("Change parameters"):
        col1, col2 = st.columns(spec=2)
        with col1:
            
            for i, (item, nb) in enumerate(zip(list_item_type_1, list_item_type_1_value)):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]
                    st.markdown(f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    list_item_type_1_value[i] = st.number_input("", key=f"input1_{i}", min_value=0., value=nb, label_visibility= "collapsed")

        with col2:
            for i, (item, nb) in enumerate(zip(list_item_type_2, list_item_type_2_value)):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]
                    st.markdown(f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    list_item_type_2_value[i] = st.number_input("", key=f"input2_{i}", min_value=0., value=nb, label_visibility= "collapsed")
        

    #col1, col2 = st.columns(spec=[1,3])

    items, items_raw = get_items(df_recipes, df_items)
    R, Rp, recipe_names = get_recipes_vect(df_recipes, items, items_raw)

    with st.sidebar:
        filtered_list = [item for item in items if "Packaged" not in item]
        df_items_prod = df_items[df_items["name"].isin(filtered_list)]
        item_to_optim_prod = item_selector(df_items_prod)
    
        items_to_produce = []
        quantities = []
        for e in item_to_optim_prod["selected_rows"]:
            items_to_produce.append(e['name'])
            quantities.append(st.number_input(f"Desired number of {e['name']} :", min_value=0, step=1, value=100))
        

    weight_raw_items_dict = {item:nb for item,nb in zip(list_item_type_1+list_item_type_2,list_item_type_1_value+list_item_type_2_value)}
    
    if len(item_to_optim_prod["selected_rows"]) >= 1:

        Lmbda_soln, status_solution = get_best_production(items_to_produce, items, items_raw, R, Rp, recipe_names, weight_raw_items_dict, quantities)

        st.write(status_solution)

        tab1, tab2, tab3 = st.tabs(["Recipes", "Materials", "Graph"])

        with tab1:
            recipe_names_kept = []
            nb_buildings = []
            for nb in np.where(Lmbda_soln > 1e-10)[0]:
                nb_buildings.append(Lmbda_soln[nb])
                recipe_names_kept.append(recipe_names[nb])

            display_recipes_frame(df_recipes, df_items, df_buildings, recipe_names_kept, nb_buildings, [1]*len(recipe_names))   
        
        with tab2:
            sol_Lmbda = Lmbda_soln

            sol_Lmbda[np.where(sol_Lmbda < 1e-10)] = 0

            Rp_final = np.sum([sol_Lmbda[j]*Rp[j] for j in range(0, len(recipe_names))], axis=0)

            for i,nb in enumerate(Rp_final):
                if nb == 0:
                    continue
                st.write(nb, items_raw[i])

            st.write("---------------------")
            R_final = np.sum([sol_Lmbda[j]*R[j] for j in range(0, len(recipe_names))], axis=0)

            for i,nb in enumerate(R_final):
                if nb == 0:
                    continue
                st.write(nb, items[i])

        with tab3:
            nodes, edges, config = create_recipe_optimize(df_items, df_buildings, df_recipes, recipe_names, Lmbda_soln)
            return_value = agraph(nodes=nodes, edges=edges, config=config)
