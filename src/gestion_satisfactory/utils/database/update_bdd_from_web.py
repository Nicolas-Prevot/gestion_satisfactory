from gestion_satisfactory.scraper.scraper import create_dfs
from gestion_satisfactory.utils.database.connect_bdd import get_connexion


def update_bdd(streamlit_display: bool = False) -> None:
    """
    Update the database by scraping data from the web and saving it to the database.

    Parameters
    ----------
    streamlit_display : bool, optional
        Flag to enable Streamlit display during the process, by default False.

    Returns
    -------
    None

    """
    engine = get_connexion()

    buildings_df, recipes_df, items_df = create_dfs(streamlit_display)

    table_name = "items"
    items_df.to_sql(table_name, engine, if_exists="replace", index=False)

    table_name = "recipes"
    recipes_df.to_sql(table_name, engine, if_exists="replace", index=False)

    table_name = "buildings"
    buildings_df.to_sql(table_name, engine, if_exists="replace", index=False)
