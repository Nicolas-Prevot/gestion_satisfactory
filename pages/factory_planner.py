import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode
from streamlit_agraph import agraph
import connect_bdd

import pandas as pd
import numpy as np

if __name__ == "__main__":
    st.set_page_config(
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="auto",)
        
    st.title("Here plan your factory")


    df_factory_planner_columns = ["area", "factory", "line", "building", "nb_building", "power_usage", "rate/overclock", "recipe",
    "out_1", "out_1_rate", "out_2", "out_2_rate", "in_1", "in_1_rate", "in_2", "in_2_rate", "in_3", "in_3_rate", "in_4", "in_4_rate"]

    try:
        df_factory_planner = connect_bdd.load_df("factory_planner")
        # assert True is False
    except:
        df_factory_planner = pd.DataFrame(columns=df_factory_planner_columns)
        #    [
        #    {"Number": 1, "Building": "truc1", "Output item": "iron", "Overclock (%)": 100, "rate": 3.5},
        #    {"Number": 1, "Building": "truc2", "Output item": "copper", "Overclock (%)": 100, "rate": 10.2},
        #    {"Number": 1, "Building": "truc3", "Output item": "iron rod", "Overclock (%)": 100, "rate": 5.4},
        #]
    
    df_recipes = connect_bdd.load_df("recipes")
    df_buildings = connect_bdd.load_df("buildings")
    new_path = []
    for i,url in enumerate(df_buildings["url_img"]):
        new_path.append("app/"+url)
    df_buildings["streamlit_path_img"] = new_path
        
    #column_config={
    #    "Number": "Streamlit Command",
    #    "rating": st.column_config.NumberColumn(
    #        "Your rating",
    #        help="How much do you like this command (1-5)?",
    #        min_value=1,
    #        max_value=5,
    #        step=1,
    #        format="%d ⭐",
    #    ),
    #    "is_widget": "Widget ?",
    #}

    # st.data_editor(df_factory_planner, column_config=column_config, use_container_width=True, num_rows="dynamic")

    st.dataframe(df_factory_planner, use_container_width=True,)

    # if st.button('Save changes', key="temp save"):
    #     connect_bdd.save_df("factory_planner", df_factory_planner)
    

    ##########################################################################################################

    col1, col2 = st.columns(spec=[1,3])

    with col1:
        try:
            options = list(df_factory_planner["area"].unique())
        except:
            options = []
        
        df_options_area = pd.DataFrame(options, columns=["area"])

        gb = GridOptionsBuilder.from_dataframe(df_options_area)
        gb.configure_selection("single")
        grid_options = gb.build()

        response = AgGrid(df_options_area,
                        theme="streamlit",
                        fit_columns_on_grid_load=True,
                        gridOptions=grid_options,
                        allow_unsafe_jscode=True,
                        reload_data=False,
                        )
                        
        with st.expander(f"Add Area", expanded=False):
            new_area_name = st.text_input("Add area", placeholder="Name of the area")
            if st.button("Confirm", key="add_area_button") and new_area_name != "":
                row = [[str(new_area_name)]+[np.nan]*(len(df_factory_planner_columns)-1)]
                df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                connect_bdd.save_df("factory_planner", df_factory_planner)
                st.success(f'Area added: "{new_area_name}"')
                st.experimental_rerun()   
        
    with col2:
        if len(response["selected_rows"]) > 0:
            area_selected = response["selected_rows"][0]["area"]

            try:
                df_factory_planner_factories = df_factory_planner[df_factory_planner["area"] == area_selected]
                factories_list = list(df_factory_planner_factories["factory"].unique())
                if None in factories_list:
                    factories_list.remove(None)
            except:
                factories_list = []

            with st.expander(f"⚙️ Manage Area ⚙️", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    new_factory_name = st.text_input("Add factory", placeholder="Name of factory")
                    if st.button("Confirm") and new_factory_name != "":
                        row = [[area_selected, str(new_factory_name)]+[np.nan]*(len(df_factory_planner_columns)-2)]
                        df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                        connect_bdd.save_df("factory_planner", df_factory_planner)
                        st.experimental_rerun()
                with col2:
                    if st.checkbox('Write "delete" to confirm'): #st.button("Do you want to remove this area ?", key="remove_area_button"):
                        confirmation = st.text_input('Write "delete" to confirm', '')
                        if confirmation == "delete":
                            df_factory_planner = df_factory_planner[df_factory_planner["area"] != area_selected]
                            connect_bdd.save_df("factory_planner", df_factory_planner)
                            st.experimental_rerun()

            if len(factories_list) == 0:
                st.write("No factory created")
            else:
                tabs_factories_list = st.tabs(factories_list)

                for factory, tab_factory in zip(factories_list, tabs_factories_list):
                    with tab_factory:

                        try:
                            df_factory_planner_lines = df_factory_planner_factories[df_factory_planner_factories["factory"] == factory]
                            lines_list = list(df_factory_planner_lines["line"].unique())
                            if None in lines_list:
                                lines_list.remove(None)
                        except:
                            lines_list = []
                        
                        
                        with st.expander(f"⚙️ Manage Factory ⚙️", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_line_name = st.text_input("Add production line", placeholder="Name of production line", key=f"text_input_{factory}")
                                if st.button("Confirm", key=f"button_confirm_{factory}") and new_line_name != "":
                                    row = [[area_selected, factory, str(new_line_name)]+[np.nan]*(len(df_factory_planner_columns)-3)]
                                    df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                                    connect_bdd.save_df("factory_planner", df_factory_planner)
                                    st.experimental_rerun()
                            with col2:
                                if st.checkbox('Write "delete" to confirm', key=f"delete_factory_{factory}"): #st.button("Do you want to remove this area ?", key="remove_area_button"):
                                    confirmation = st.text_input('Write "delete" to confirm', '')
                                    if confirmation == "delete":
                                        df_factory_planner = df_factory_planner[(df_factory_planner["area"] != area_selected) | 
                                                                                ((df_factory_planner["area"] == area_selected) & (df_factory_planner["factory"] != factory))]
                                        connect_bdd.save_df("factory_planner", df_factory_planner)
                                        st.experimental_rerun()

                        if len(lines_list) == 0:
                            st.write("No line created")
                        else:
                            for line in lines_list:
                                with st.expander(f"{line}"):
                                    df_line = df_factory_planner_lines[df_factory_planner_lines["line"] == line]
                                    df_line = df_line[df_factory_planner_columns[3:]]
                                    df_line["image_building"] = [None if (list(df_buildings[df_buildings["name"] == building]["streamlit_path_img"]) == []) else list(df_buildings[df_buildings["name"] == building]["streamlit_path_img"])[0] for building in df_line["building"]]
                                    
                                    list_of_buildings = list(df_buildings["name"].unique())
                                    list_of_recipes = list(df_recipes["name"].unique())

                                    column_config = {
                                        #"image_building": st.column_config.ImageColumn("Image"),
                                        #"building": st.column_config.SelectboxColumn(
                                        #    label="Building",
                                        #    help="Building to manufacture the item(s)",
                                        #    required=True,
                                        #    options=list_of_buildings
                                        #),
                                        #"nb_building": st.column_config.NumberColumn(
                                        #    label="Number",
                                        #    help="Number of building(s)",
                                        #    required=True,
                                        #    default=1,
                                        #    min_value=1,
                                        #    step=1
                                        #),
                                        #"rate/overclock": st.column_config.NumberColumn(
                                        #    label="🌡️💯",
                                        #    help="Overclock rate of the machine",
                                        #    required=True,
                                        #    default=100,
                                        #    min_value=1,
                                        #    max_value=250,
                                        #    step=1
                                        #),
                                        #"power_usage": st.column_config.NumberColumn(
                                        #    label="⚡",
                                        #    help="Power usage of the recipe",
                                        #    disabled=True,
                                        #    min_value=1,
                                        #    step=1
                                        #),
                                        #"recipe": st.column_config.SelectboxColumn(
                                        #    label="Recipe",
                                        #    help="Recipe to manufacture",
                                        #    required=True,
                                        #    options=list_of_recipes
                                        #),
                                        #"out_1": st.column_config.Column(disabled=True),
                                        #"out_1_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                        #"out_2": st.column_config.Column(disabled=True),
                                        #"out_2_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                        #"in_1": st.column_config.Column(disabled=True),
                                        #"in_1_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                        #"in_2": st.column_config.Column(disabled=True),
                                        #"in_2_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                        #"in_3": st.column_config.Column(disabled=True),
                                        #"in_3_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                        #"in_4": st.column_config.Column(disabled=True),
                                        #"in_4_rate": st.column_config.NumberColumn(disabled=True, min_value=0.00, step=0.01),
                                    }

                                    df_line_ = st.data_editor(data=df_line, 
                                                              #column_config=column_config, 
                                                              use_container_width=True, 
                                                              num_rows="dynamic",
                                                              hide_index=True,
                                                              #column_order=("image_building", "building", "nb_building", "rate/overclock", "recipe", "power_usage", 
                                                              #              "out_1", "out_1_rate", "out_2", "out_2_rate", 
                                                              #              "in_1", "in_1_rate", "in_2", "in_2_rate", "in_3", "in_3_rate", "in_4", "in_4_rate")
                                                                            )
                                    st.write(df_line_)

                                    if st.button("Save updates", key=f"update_{line}"):
                                        

                                        rows = df_line[["building", "nb_building", "power_usage", "rate/overclock", "recipe", "out_1", "out_1_rate", "out_2", "out_2_rate", "in_1", "in_1_rate", "in_2", "in_2_rate", "in_3", "in_3_rate", "in_4", "in_4_rate"]]
                                        rows["area"] = [area_selected]*len(rows)
                                        rows["factory"] = [factory]*len(rows)
                                        rows["line"] = [line]*len(rows)

                                        st.write(rows)
                                        df_factory_planner = pd.concat([df_factory_planner, rows], ignore_index=True)
                                        df_factory_planner = df_factory_planner.drop_duplicates()

                                        st.write(df_factory_planner)

                                        # connect_bdd.save_df("factory_planner", df_factory_planner)
                                        # st.experimental_rerun()
                                    
                                    df_temp = pd.DataFrame([[1,2,None], [8,9,None]], columns=["name", "streamlit_path_img", "etert"])
                                    column_config = {
                                        "name": st.column_config.NumberColumn(disabled=False, label="🌡️💯", required=True, min_value=0.00, step=0.01),
                                        "streamlit_path_img": st.column_config.NumberColumn(min_value=0.00, step=0.01),
                                        "etert": st.column_config.SelectboxColumn(
                                            label="Recipe",
                                            help="Recipe to manufacture",
                                            options=list_of_recipes
                                        ),
                                    }
                                    df_temp = st.data_editor(data=df_temp,
                                                             column_config=column_config, 
                                                             use_container_width=True, 
                                                             num_rows="dynamic",
                                                             hide_index=True,
                                                             column_order=["streamlit_path_img", "name", "etert"])
                                    st.write(df_temp)


