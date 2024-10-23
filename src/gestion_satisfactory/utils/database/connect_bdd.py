from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine import Engine
from typing import List
import pandas as pd
import os
import streamlit as st
from loguru import logger


@st.cache_resource
def get_connexion() -> Engine:
    """
    Establish a connection to the database.

    This function creates a connection to either a PostgreSQL or SQLite database
    based on the environment variables. It caches the connection using Streamlit's
    caching mechanism.

    Returns
    -------
    Engine
        A SQLAlchemy Engine connected to the database.

    """
    postgres_support = os.environ.get("POSTGRES_SUPPORT", "false").lower() == "true"
    if postgres_support:
        logger.info("Creating a PostgreSQL connection...")
        # Chaîne de connexion à la base de données PostgreSQL
        db_url = f"postgresql://{os.environ['USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['HOST']}:{os.environ['PORT_POSTGRES']}/{os.environ['POSTGRES_DB']}"
        # Création du moteur SQLAlchemy
        engine = create_engine(db_url)
    else:
        logger.info("Creating a SQLite connection...")
        db_path = os.path.join("data", "sqlite", "satisfactory.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        pass  # Connection successful
    logger.success("Connection to database established")
    return engine


def load_df(name_table: str) -> pd.DataFrame:
    """
    Load a table from the database into a pandas DataFrame.

    Parameters
    ----------
    name_table : str
        The name of the table to load from the database.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the data from the specified table.

    """
    conn = get_connexion()
    query = f"SELECT * FROM {name_table}"
    df = pd.read_sql(query, conn)
    return df


def save_df(name_table: str, table: pd.DataFrame) -> None:
    """
    Save a pandas DataFrame to the database as a table.

    Parameters
    ----------
    name_table : str
        The name of the table to save to the database.
    table : pd.DataFrame
        The DataFrame to save.

    Returns
    -------
    None

    """
    conn = get_connexion()
    table.to_sql(name_table, conn, if_exists="replace", index=False)


def get_list_tables() -> List[str]:
    """
    Retrieve a list of all table names in the database.

    Returns
    -------
    list of str
        A list containing the names of all tables in the database.

    """
    conn = get_connexion()
    metadata = MetaData()
    metadata.reflect(bind=conn)
    table_names = metadata.tables.keys()
    return list(table_names)


def delete_table(table_name: str) -> None:
    """
    Delete a table from the database.

    Parameters
    ----------
    table_name : str
        The name of the table to delete.

    Returns
    -------
    None

    """
    conn = get_connexion()
    metadata = MetaData()
    metadata.reflect(bind=conn)
    your_table = Table(table_name, metadata)
    your_table.drop(conn, checkfirst=True)
