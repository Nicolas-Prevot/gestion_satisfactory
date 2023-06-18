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
        assert True is False
    except:
        df_factory_planner = pd.DataFrame(columns=df_factory_planner_columns)
        #    [
        #    {"Number": 1, "Building": "truc1", "Output item": "iron", "Overclock (%)": 100, "rate": 3.5},
        #    {"Number": 1, "Building": "truc2", "Output item": "copper", "Overclock (%)": 100, "rate": 10.2},
        #    {"Number": 1, "Building": "truc3", "Output item": "iron rod", "Overclock (%)": 100, "rate": 5.4},
        #]
        
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

    df_factory_planner = st.dataframe(df_factory_planner, use_container_width=True,)

    # if st.button('Save changes', key="temp save"):
    #     connect_bdd.save_df("factory_planner", df_factory_planner)
    

    ##########################################################################################################

    col1, col2 = st.columns(spec=[1,3])

    with col1:
        try:
            options = list(df_factory_planner["area"].unique())
        except:
            options = []
        
        df_options = pd.DataFrame(options, columns=["area"])

        gb = GridOptionsBuilder.from_dataframe(df_options)
        gb.configure_selection("single")
        grid_options = gb.build()

        response = AgGrid(df_options,
                        theme="streamlit",
                        fit_columns_on_grid_load=True,
                        gridOptions=grid_options,
                        allow_unsafe_jscode=True,
                        reload_data=False,
                        )
                        
        with st.expander(f"Add Area"):
            new_area_name = st.text_input("Add area", placeholder="Name of the area")
            if st.button("Confirm", key="add_area_button") and new_area_name != "":
                row = np.array([[new_area_name]+[None]*(len(df_factory_planner_columns)-1)]).T
                print(row)
                df_factory_planner = pd.concat([df_factory_planner, pd.DataFrame(row, columns=df_factory_planner_columns)])
                st.success(f'Area added: "{new_area_name}"')

    with col2:
        with st.expander(f"⚙️ Manage Area ⚙️"):
            col1, col2 = st.columns(2)
            with col1:
                new_factory_name = st.text_input("Add factory", placeholder="Name of factory")
                if st.button("Confirm") and new_factory_name != "":
                    st.success(f'Factory added: "{new_factory_name}"')
            with col2:
                st.write("Do you want to delete the area ?")
                if st.button("Remove area"):
                    st.warning('Area removed')
        
        factories_list = ["1", "2", "3"]
        factories_list = st.tabs(factories_list)

        for factory in factories_list:
            with factory:
                with st.expander(f"⚙️ Manage Factory ⚙️"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_line_name = st.text_input("Add production line", placeholder="Name of production line", key=f"text_input_{factory}")
                        if st.button("Confirm", key=f"button_confirm_{factory}") and new_line_name != "":
                            st.success(f'Production line added: "{new_line_name}"')
                    with col2:
                        st.write("Do you want to delete the factory ?")
                        if st.button("Remove factory", key=f"button_fact_{factory}"):
                            st.warning('Factory removed')

                lines = ["1", "2", "3"]
                for line in lines:
                    with st.expander(f"{line}"):
                        st.write("My line !")
    
