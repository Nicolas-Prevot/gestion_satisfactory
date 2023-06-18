from sqlalchemy import create_engine
import pandas as pd
from omegaconf import OmegaConf


def get_configurable_parameters(config_path: str):
    config = OmegaConf.load(config_path)
    return config


def get_connexion(config):
    # Chaîne de connexion à la base de données PostgreSQL
    db_url = f'postgresql://{config.PostgreSQL.user}:{config.PostgreSQL.password}@{config.PostgreSQL.host}:{config.PostgreSQL.port}/{config.PostgreSQL.database}'
    # Création du moteur SQLAlchemy
    engine = create_engine(db_url)

    return engine


def load_df(name_table):
    config = get_configurable_parameters("configs/postgre.yaml")
    conn = get_connexion(config)

    query = f'SELECT * FROM {name_table}'
    # Utilisation de la méthode `read_sql` de pandas pour exécuter la requête SQL et obtenir un DataFrame
    df = pd.read_sql(query, conn)

    return df


def save_df(name_table, table):
    config = get_configurable_parameters("configs/postgre.yaml")
    conn = get_connexion(config)

    table.to_sql(name_table, conn, if_exists='replace', index=False)