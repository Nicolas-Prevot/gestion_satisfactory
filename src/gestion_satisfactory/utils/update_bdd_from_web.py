from ..web_scraping.web_scraping import create_dfs
from .connect_bdd import get_connexion


def update_bdd(streamlit_display=False):
    engine = get_connexion()

    buildings_df, recipes_df, items_df = create_dfs(streamlit_display)

    table_name = 'items'
    items_df.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'recipes'
    recipes_df.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'buildings'
    buildings_df.to_sql(table_name, engine, if_exists='replace', index=False)
