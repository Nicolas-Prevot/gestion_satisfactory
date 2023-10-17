from operator import ge
import os
from sqlalchemy import create_engine

from web_scraping.web_scraping import create_dfs


def main(streamlit_display=False):
    
    # Chaîne de connexion à la base de données PostgreSQL
    db_url = f"postgresql://{os.environ['USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['HOST']}:{os.environ['PORT_POSTGRES']}/{os.environ['POSTGRES_DB']}"
    # Création du moteur SQLAlchemy
    engine = create_engine(db_url)


    df_items, df_buildings, df_recipes = create_dfs(streamlit_display)

    # Nom de la nouvelle table à créer
    table_name = 'items'
    # Enregistrement du DataFrame en tant que nouvelle table
    df_items.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'buildings'
    df_buildings.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'recipes'
    df_recipes.to_sql(table_name, engine, if_exists='replace', index=False)



if __name__ == '__main__':
    main()