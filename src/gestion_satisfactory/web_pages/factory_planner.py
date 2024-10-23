import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import numpy as np
import os
from PIL import Image
from typing import Tuple, Dict, Any

from gestion_satisfactory.utils.database.load_df import get_df_from_tables
from gestion_satisfactory.utils.display.display import display_results_item, display_recipes_frame
from gestion_satisfactory.utils.database.connect_bdd import load_df, save_df, get_list_tables, delete_table
from gestion_satisfactory.utils.database.update_bdd_from_web import update_bdd
from gestion_satisfactory.utils.config.config import df_factory_planner_columns
from gestion_satisfactory.utils.helpers.string_utils import (
    display_name_to_table_name,
    table_name_to_display_name
)


@st.cache_data
def cached_get_df_from_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Cache and retrieve dataframes from tables.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        A tuple containing dataframes for items, buildings, and recipes.

    """
    return get_df_from_tables()


def create_page(title: str) -> None:
    """
    Create a Streamlit page for factory planning.

    Parameters
    ----------
    title : str
        The title of the page.

    Returns
    -------
    None
    
    """
    try:
        list_tables = get_list_tables()
        list_tables.remove("items")
        list_tables.remove("buildings")
        list_tables.remove("recipes")
    except:
        update_bdd(streamlit_display=True)
        st.rerun()

    dict_display_table = {table_name_to_display_name(name):name for name in list_tables}

    with st.sidebar:
        st.title("Here plan your factory")

        with st.expander(f"Create a new party", expanded=False):
            with st.form("form_create_party"):
                name_new_table = st.text_input(label="Choose a name", value="")
                if name_new_table != "":
                    new_table_name = display_name_to_table_name(name_new_table)
                    display_name = table_name_to_display_name(new_table_name)
                
                submitted = st.form_submit_button("Submit")
                if submitted:
                    if display_name in dict_display_table.keys():
                        st.error("This name is already used")
                    else:
                        dict_display_table[display_name] = new_table_name
                        save_df(new_table_name, pd.DataFrame(columns=df_factory_planner_columns))
                        st.success("New table created!")


        with st.expander(f"Delete party", expanded=False):
            with st.form("form_delete_party"):
                factory_planner_selected_to_delete_display = st.selectbox(label="Select your party", options=list(dict_display_table.keys()))
                ok = False
                if st.checkbox('Write "delete" to confirm'): #st.button("Do you want to remove this area ?", key="remove_area_button"):
                    confirmation = st.text_input('Write "delete" to confirm', '')
                    if confirmation == "delete":
                        ok = True

                submitted = st.form_submit_button("Submit")
                if submitted:
                    if ok:
                        delete_table(dict_display_table[factory_planner_selected_to_delete_display])
                        st.success("Table deleted!")
                        st.rerun()
                    else:
                        st.warning("Are you sure ? Please confirm")

        st.divider()

        factory_planner_selected_display = st.selectbox(label="Select your party", options=list(dict_display_table.keys()))
    
    if factory_planner_selected_display is None:
        st.markdown(
            """
            <h2 style='text-align: center; color: #FF4B4B;'>
                ⚠️ No Factory Selected!
            </h2>
            <p style='text-align: center; font-size: 18px;'>
                Please create or select a factory from the sidebar.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        factory_planner_selected = dict_display_table[factory_planner_selected_display]

        st.markdown(
            f"""
            <h1 style='text-align: center;'>
                🏭 Welcome to Your Factory: <i>{factory_planner_selected_display}</i>
            </h1>
            """,
            unsafe_allow_html=True,
        )

        df_factory_planner = load_df(factory_planner_selected)
        df_items, df_buildings, df_recipes = cached_get_df_from_tables()

        with st.expander("General informations", False):
            st.dataframe(df_factory_planner, use_container_width=True,)

        display_results_item(df_factory_planner, df_items, True)

        st.divider()

        col1, col2 = st.columns(spec=[1,5])

        with col1:
            try:
                options = list(df_factory_planner["area"].unique())
            except:
                options = []
            
            df_options_area = pd.DataFrame(options, columns=["area"])

            gb = GridOptionsBuilder.from_dataframe(df_options_area)
            gb.configure_selection("single")
            grid_options = gb.build()

            area_choice = AgGrid(df_options_area,
                                theme="streamlit",
                                fit_columns_on_grid_load=True,
                                gridOptions=grid_options,
                                allow_unsafe_jscode=True,
                                reload_data=False,
                                )
                            
            with st.expander(f"Add Area", expanded=False):
                new_area_name = st.text_input("Add area", placeholder="Name of the area", value="")
                if st.button("Confirm", key="add_area_button") and new_area_name != "":
                    row = [[str(new_area_name)]+[np.nan]*(len(df_factory_planner_columns)-1)]
                    df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                    save_df(factory_planner_selected, df_factory_planner)
                    st.success(f'Area added: "{new_area_name}"')
                    st.rerun()
        
        if area_choice["selected_rows"] is not None:
            area_selected = area_choice["selected_rows"].iloc[0]["area"]

            with col2:
                st.markdown(
                    f"""
                    <h1 style='text-align: center;'>
                        🏙️ <i>{area_selected}</i> 🌐🏭
                    </h1>
                    """,
                    unsafe_allow_html=True,
                )
                display_results_item(df_factory_planner[df_factory_planner["area"] == area_selected], df_items, True)


            with st.expander(f"⚙️ Manage Area **{area_selected}** ⚙️", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_factory_name = st.text_input("Add factory", placeholder="Name of factory", value="")
                    if st.button("Confirm") and new_factory_name != "":
                        row = [[area_selected, str(new_factory_name)]+[np.nan]*(len(df_factory_planner_columns)-2)]
                        df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                        save_df(factory_planner_selected, df_factory_planner)
                        st.rerun()
                with col2:
                    if st.checkbox('Rename area ?'):
                        confirmation = st.text_input(label='New name:', placeholder=f'Name to replace "{area_selected}"', value="")
                        if confirmation != "":
                            df_factory_planner['area'].replace(area_selected, confirmation, inplace=True)
                            save_df(factory_planner_selected, df_factory_planner)
                            st.rerun()
                with col3:
                    if st.checkbox('Delete area ?'):
                        confirmation = st.text_input(f'Write "{area_selected}" to confirm', value="")
                        if confirmation == area_selected:
                            df_factory_planner = df_factory_planner[df_factory_planner["area"] != area_selected]
                            save_df(factory_planner_selected, df_factory_planner)
                            st.rerun()

            st.divider()

            with st.container():

                col1_factory, col2_factory = st.columns(spec=[1,5])

                with col1_factory:
                    try:
                        df_factory_planner_factories = df_factory_planner[df_factory_planner["area"] == area_selected]
                        factories_list = list(df_factory_planner_factories["factory"].unique())
                        if None in factories_list:
                            factories_list.remove(None)
                    except:
                        factories_list = []
                        st.write("No factory created")
                    
                    df_options_factory = pd.DataFrame(factories_list, columns=["factory"])

                    gb = GridOptionsBuilder.from_dataframe(df_options_factory)
                    gb.configure_selection("single")
                    grid_options = gb.build()

                    

                    factory_choice = AgGrid(df_options_factory,
                                            theme="streamlit",
                                            fit_columns_on_grid_load=True,
                                            gridOptions=grid_options,
                                            allow_unsafe_jscode=True,
                                            reload_data=False,
                                            )
                
                if factory_choice["selected_rows"] is not None:
                    factory_selected = factory_choice["selected_rows"].iloc[0]["factory"]

                    with col2_factory:
                        st.markdown(
                            f"""
                            <h1 style='text-align: center;'>
                                🏭 <i>{factory_selected}</i> 🏗️
                            </h1>
                            """,
                            unsafe_allow_html=True,
                        )
                        display_results_item(df_factory_planner_factories[df_factory_planner_factories["factory"] == factory_selected], df_items)

                    with st.expander(f"⚙️ Manage Factory **{factory_selected}** ⚙️", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            new_line_name = st.text_input("Add production line", placeholder="Name of production line", key=f"text_input_{factory_selected}", value="")
                            if st.button("Confirm", key=f"button_confirm_{factory_selected}") and new_line_name != "":
                                row = [[area_selected, factory_selected, str(new_line_name)]+[np.nan]*(len(df_factory_planner_columns)-3)]
                                df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)], ignore_index=True)
                                save_df(factory_planner_selected, df_factory_planner)
                                st.rerun()
                        with col2:
                            if st.checkbox('Rename factory ?'):
                                confirmation = st.text_input(label='New name:', placeholder=f'Name to replace "{factory_selected}"', value="")
                                if confirmation != "":
                                    df_factory_planner_factories.replace(factory_selected, confirmation, inplace=True)
                                    df_factory_planner.drop(list(df_factory_planner_factories.index), inplace=True)
                                    df_factory_planner = pd.concat([df_factory_planner, df_factory_planner_factories], ignore_index=True)
                                    save_df(factory_planner_selected, df_factory_planner)
                                    st.rerun()
                        with col3:
                            if st.checkbox('Delete factory ?', key=f"delete_factory_{factory_selected}"):
                                confirmation = st.text_input(f'Write "{factory_selected}" to confirm', value="")
                                if confirmation == factory_selected:
                                    df_factory_planner = df_factory_planner[(df_factory_planner["area"] != area_selected) | 
                                                                            ((df_factory_planner["area"] == area_selected) & (df_factory_planner["factory"] != factory_selected))]
                                    save_df(factory_planner_selected, df_factory_planner)
                                    st.rerun()
                    
                    st.divider()

                    with st.container():

                        col1_line, col2_line = st.columns(spec=[1,5])

                        with col1_line:
                            try:
                                df_factory_planner_lines = df_factory_planner_factories[df_factory_planner_factories["factory"] == factory_selected]
                                lines_list = list(df_factory_planner_lines["line"].unique())
                                if None in lines_list:
                                    lines_list.remove(None)
                            except:
                                lines_list = []
                                st.write("No line created")
                            
                            df_options_line = pd.DataFrame(lines_list, columns=["line"])

                            gb = GridOptionsBuilder.from_dataframe(df_options_line)
                            gb.configure_selection("single")
                            grid_options = gb.build()

                            line_choice = AgGrid(df_options_line,
                                                theme="streamlit",
                                                fit_columns_on_grid_load=True,
                                                gridOptions=grid_options,
                                                allow_unsafe_jscode=True,
                                                reload_data=False,
                                                )
                        
                            if line_choice["selected_rows"] is not None:
                                line_selected = line_choice["selected_rows"].iloc[0]["line"]

                                with st.expander(f"⚙️ Manage line **{line_selected}** ⚙️", expanded=False):
                                    if st.checkbox('Delete production line ?', key=f"delete_line_{line_selected}"):
                                        confirmation = st.text_input(f'Write "{line_selected}" to confirm', value="")
                                        if confirmation == line_selected:
                                            df_factory_planner_to_delete = df_factory_planner_lines[df_factory_planner_lines["line"] == line_selected]
                                            df_factory_planner.drop(list(df_factory_planner_to_delete.index), inplace=True)
                                            save_df(factory_planner_selected, df_factory_planner)
                                            st.rerun()
                                    if st.checkbox('Rename production line ?'):
                                        confirmation = st.text_input(label='New name:', placeholder=f'Name to replace "{line_selected}"', value="")
                                        if confirmation != "":
                                            df_factory_planner_lines.replace(line_selected, confirmation, inplace=True)
                                            df_factory_planner.drop(list(df_factory_planner_lines.index), inplace=True)
                                            df_factory_planner = pd.concat([df_factory_planner, df_factory_planner_lines], ignore_index=True)
                                            save_df(factory_planner_selected, df_factory_planner)
                                            st.rerun()

                        if line_choice["selected_rows"] is not None:
                            line_selected = line_choice["selected_rows"].iloc[0]["line"]

                            with col2_line:
                                st.markdown(
                                    f"""
                                    <h1 style='text-align: center;'>
                                        🛠️➡️📦 <i>{line_selected}</i> 🔧
                                    </h1>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                display_results_item(df_factory_planner_lines[df_factory_planner_lines["line"] == line_selected], df_items)

                                with st.expander("Edit lines", expanded=False):
                                    list_of_recipes = sorted(list(df_recipes["recipe_name"].unique()))
                                    df_line = df_factory_planner_lines[df_factory_planner_lines["line"] == line_selected]
                                    df_line_custom = pd.DataFrame(df_line[["nb_building", "rate/overclock", "recipe_name"]]).reset_index(drop=True)

                                    column_config = {
                                        "rate/overclock": st.column_config.NumberColumn(disabled=False,
                                                                                        label="🌡️💯",
                                                                                        required=True,
                                                                                        default=1.,
                                                                                        min_value=0.00,
                                                                                        max_value=2.5,
                                                                                        step=0.01),
                                        "nb_building": st.column_config.NumberColumn(label="Number",
                                                                                    help="Number of building(s)",
                                                                                    required=True,
                                                                                    default=1,
                                                                                    min_value=1,
                                                                                    step=1),
                                        "recipe_name": st.column_config.SelectboxColumn(label="Recipe",
                                                                                help="Recipe to manufacture",
                                                                                required=True,
                                                                                options=list_of_recipes),
                                    }
                                    df_edited = st.data_editor(data=df_line_custom,
                                                            column_config=column_config,
                                                            use_container_width=True, 
                                                            num_rows="dynamic",
                                                            hide_index=True,
                                                            column_order=["nb_building", "rate/overclock", "recipe_name"],
                                                            key=f"data_editor_{line_selected}")

                                    if st.button("Save updates", key=f"update_{line_selected}"):
                                        col_recipe = ["building_name", "duration", "min_consumption","max_consumption","ingredient_1","ingredient_amount_1","ingredient_2","ingredient_amount_2","ingredient_3","ingredient_amount_3","ingredient_4","ingredient_amount_4","product_1","product_amount_1","product_2","product_amount_2"]
                                        col_building = ["power_usage"]
                                        rows = []
                                        for i, df_edited_row in df_edited.iterrows():
                                            new_row = df_recipes[df_recipes["recipe_name"] == df_edited_row["recipe_name"]][col_recipe].values.tolist()[0]
                                            new_row += [df_buildings[df_buildings["name"] == new_row[0]][["power_usage"]].values.tolist()[0][0], area_selected, factory_selected, line_selected]
                                            rows.append(new_row)
                                        rows = np.array(rows)

                                        for i, name_col in enumerate(col_recipe+col_building+["area", "factory", "line"]):
                                            df_edited[name_col] = rows[:,i]

                                        df_factory_planner.drop(list(df_line.index), inplace=True)
                                        df_factory_planner = pd.concat([df_factory_planner, df_edited], ignore_index=True)
                                        save_df(factory_planner_selected, df_factory_planner)
                                        st.rerun()
                                
                                recipe_vars = dict(zip(df_line["recipe_name"], df_line["nb_building"]))
                                recipe_var_to_name = dict(zip(df_line["recipe_name"], df_line["recipe_name"]))
                                recipe_vars.pop(None, None)
                                recipe_var_to_name.pop(None, None)

                                display_recipes_frame(df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name)

                            st.divider()