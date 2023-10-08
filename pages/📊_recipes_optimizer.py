import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode
from streamlit_agraph import agraph

import os
import pandas as pd
import numpy as np
from PIL import Image

from utils.optimize import get_items, get_recipes_vect, get_best_production
from pages.utils.load_df import get_df_from_tables
from pages.utils.grids import item_selector
from pages.utils.graph import create_recipe_optimize

list_item_type_1 = ['Raw_Quartz','Bauxite','Crude_Oil','Iron_Ore','Coal','Uranium','Sulfur','Nitrogen_Gas','Water','Caterium_Ore','Limestone','Copper_Ore']
list_item_type_2 = ['Wood','Blue_Power_Slug','Plasma_Spitter_Remains','Purple_Power_Slug','Flower_Petals','Stinger_Remains','Yellow_Power_Slug','Mycelia','Hog_Remains','Hatcher_Remains','Leaves']
list_item_type_1_value = [2.,3.,0.5,1.,1.,10.,1.,2.,0.,2.,1.,1.]
list_item_type_2_value = [1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]


if __name__ == "__main__":
    st.set_page_config(
    page_icon=Image.open("pages/logo.png"),
    layout="wide",
    initial_sidebar_state="auto",)


    df_items, df_buildings, df_recipes = get_df_from_tables()


    st.title("Here optimize your production recipes")

    with st.expander("See explanation"):
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
        

    col1, col2 = st.columns(spec=[1,3])

    items, items_raw = get_items(df_recipes, df_items)
    R, Rp, recipe_names = get_recipes_vect(df_recipes, items, items_raw)

    with col1:
        filtered_list = [item for item in items if "Packaged" not in item]
        df_items_prod = df_items[df_items["name"].isin(filtered_list)]
        item_to_optim_prod = item_selector(df_items_prod)

    with col2:
        weight_raw_items_dict = {item:nb for item,nb in zip(list_item_type_1+list_item_type_2,list_item_type_1_value+list_item_type_2_value)}
        
        if len(item_to_optim_prod["selected_rows"]) == 1:
            item_name = item_to_optim_prod["selected_rows"][0]["name"]

            Lmbda_soln, status_solution = get_best_production(item_name, items, items_raw, R, Rp, recipe_names, weight_raw_items_dict, quantity=100)

            st.write(status_solution)

            tab1, tab2 = st.tabs(["Recipes", "Materials"])

            with tab1:

                nodes, edges, config = create_recipe_optimize(df_items, df_buildings, df_recipes, recipe_names, Lmbda_soln)
                return_value = agraph(nodes=nodes, edges=edges, config=config)

                # def print_r(recipe):
                #     for i in range(4):
                #         if recipe[f"item_in_{i+1}"].values[0] is not None:
                #             st.write(f"In {recipe[f'rate_in_{i+1}'].values[0]} {recipe[f'item_in_{i+1}'].values[0]}")
                #     for i in range(2):
                #         if recipe[f"item_out_{i+1}"].values[0] is not None:
                #             st.write(f"Out {recipe[f'rate_out_{i+1}'].values[0]} {recipe[f'item_out_{i+1}'].values[0]}")

                for nb in np.where(Lmbda_soln > 1e-10)[0]:
                    # st.write(Lmbda_soln[nb], recipe_names[nb])
                    # print_r(df_recipes[df_recipes["name"] == recipe_names[nb]])
                    # st.write("-----------------------------")

                    row = df_recipes[df_recipes["name"] == recipe_names[nb]]
                    out_items = f''
                    for i in range(1,3):
                        item = row[f"item_out_{i}"].values[0]
                        if item is None:
                            break
                        src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]

                        rate = row[f"rate_out_{i}"].values[0]
                        out_items += f'{rate} <figure class="image" style="margin: 20px;"><img src="{src_img}" width=50px><figcaption style="font-size: 12px;">{item}</figcaption></figure>'
                    
                    in_items = ""
                    for i in range(1,5):
                        item = row[f"item_in_{i}"].values[0]
                        if item is None:
                            break
                        src_img = df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]
                        
                        rate = row[f"rate_in_{i}"].values[0]
                        in_items += f'{rate} <figure class="image" style="margin: 20px;"><img src="{src_img}" width=50px><figcaption style="font-size: 12px;">{item}</figcaption></figure>'

                    src_img = df_buildings[df_buildings["name"] == row["building"].values[0]]["streamlit_path_img"].tolist()[0]
                    container_style = """
                        display: flex;
                        align-items: center;
                    """
                    st.markdown(f'<div style="{container_style}">{Lmbda_soln[nb]} {row["name"].values[0]}, {"🔄" if row["alternate"].values[0] else "🟦"} {out_items}: <img src="{src_img}" width=80px> {in_items}</div>', unsafe_allow_html=True)
    
            
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



#        weight_raw_items_dict = {'Raw_Quartz':2,
#                        'Bauxite':3,
#                        'Crude_Oil':0.5,
#                        'Iron_Ore':1,
#                        'Coal':1,
#                        'Uranium':10,
#                        'Sulfur':1,
#                        'Nitrogen_Gas':2,
#                        'Water':0,
#                        'Caterium_Ore':2,
#                        'Limestone':1,
#                        'Copper_Ore':1,
#
#                        'Wood':1,
#                        'Blue_Power_Slug':1,
#                        'Plasma_Spitter_Remains':1,
#                        'Purple_Power_Slug':1,
#                        'Flower_Petals':1,
#                        'Stinger_Remains':1,
#                        'Yellow_Power_Slug':1,
#                        'Mycelia':1,
#                        'Hog_Remains':1,
#                        'Hatcher_Remains':1,
#                        'Leaves':1,
#                        }

