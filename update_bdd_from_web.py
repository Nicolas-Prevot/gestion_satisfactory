from operator import ge
from omegaconf import OmegaConf
from sqlalchemy import create_engine

from web_scraping.web_scraping import create_dfs


def get_configurable_parameters(config_path: str):
    config = OmegaConf.load(config_path)
    return config


def main():
    config = get_configurable_parameters("configs/postgre.yaml")
    
    # Chaîne de connexion à la base de données PostgreSQL
    db_url = f'postgresql://{config.PostgreSQL.user}:{config.PostgreSQL.password}@{config.PostgreSQL.host}:{config.PostgreSQL.port}/{config.PostgreSQL.database}'
    # Création du moteur SQLAlchemy
    engine = create_engine(db_url)


    df_items, df_buildings, df_recipes = create_dfs()

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