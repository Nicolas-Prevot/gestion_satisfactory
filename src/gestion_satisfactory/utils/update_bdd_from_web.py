import os
from sqlalchemy import create_engine

from web_scraping.web_scraping import create_dfs


def main(streamlit_display=False):
    
    # Chaîne de connexion à la base de données PostgreSQL
    db_url = f"postgresql://{os.environ['USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['HOST']}:{os.environ['PORT_POSTGRES']}/{os.environ['POSTGRES_DB']}"

    # Création du moteur SQLAlchemy
    engine = create_engine(db_url)

    buildings_df, recipes_df, items_df = create_dfs(streamlit_display)

    table_name = 'items'
    items_df.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'recipes'
    recipes_df.to_sql(table_name, engine, if_exists='replace', index=False)

    table_name = 'buildings'
    buildings_df.to_sql(table_name, engine, if_exists='replace', index=False)



if __name__ == '__main__':
    main()