from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from streamlit_agraph import agraph




def item_selector(df_items):
    gb = GridOptionsBuilder.from_dataframe(df_items[["name", "web_img"]])

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

    gb.configure_column("web_img", cellRenderer=thumbnail_renderer)
    gb.configure_default_column(editable=False, min_column_width=5)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)# gb.configure_selection("single")
    grid_options = gb.build()


    item_to_optim_prod = AgGrid(df_items[["name", "web_img"]],
                                    theme="streamlit",
                                    key='Optimization',
                                    fit_columns_on_grid_load=True,
                                    height=600,
                                    gridOptions=grid_options,
                                    allow_unsafe_jscode=True,
                                    reload_data=False,
                                    )
    
    return item_to_optim_prod