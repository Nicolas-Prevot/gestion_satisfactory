from sqlalchemy import create_engine, MetaData, Table
import pandas as pd
import os
import streamlit as st

@st.cache_resource
def get_connexion():
    try:
        # Chaîne de connexion à la base de données PostgreSQL
        db_url = f"postgresql://{os.environ['USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['HOST']}:{os.environ['PORT_POSTGRES']}/{os.environ['POSTGRES_DB']}"
        # Création du moteur SQLAlchemy
        engine = create_engine(db_url)
        with engine.connect() as conn:
            pass  # Connection successful
    except:
        db_path = os.path.join('data', 'sqlite', 'satisfactory.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
    return engine


def load_df(name_table):
    conn = get_connexion()
    query = f'SELECT * FROM {name_table}'
    df = pd.read_sql(query, conn)
    return df


def save_df(name_table, table):
    conn = get_connexion()
    table.to_sql(name_table, conn, if_exists='replace', index=False)


def get_list_tables():
    conn = get_connexion()
    metadata = MetaData()
    metadata.reflect(bind=conn)
    table_names = metadata.tables.keys()
    return list(table_names)


def delete_table(table_name:str):
    conn = get_connexion()
    metadata = MetaData()
    metadata.reflect(bind=conn)
    your_table = Table(table_name, metadata)
    your_table.drop(conn, checkfirst=True)
    