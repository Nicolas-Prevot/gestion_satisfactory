
from utils.connect_bdd import get_configurable_parameters, get_connexion
import pandas as pd

from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base


config = get_configurable_parameters("configs/postgre.yaml")
conn = get_connexion(config)

query1 = '''SELECT
    table_schema || '.' || table_name
FROM
    information_schema.tables
WHERE
    table_type = 'BASE TABLE'
AND
    table_schema NOT IN ('pg_catalog', 'information_schema');'''

# Utilisation de la méthode `read_sql` de pandas pour exécuter la requête SQL et obtenir un DataFrame
df = pd.read_sql(query1, conn)
print(df)


# metadata = MetaData()
# metadata.reflect(bind=conn)

# table_name = 'employes'  # Replace with the name of the table you want to delete
# your_table = Table(table_name, metadata)
# 
# print(your_table)
# your_table.drop(conn, checkfirst=True)


metadata = MetaData()
metadata.reflect(bind=conn)

# Get a list of table names
table_names = metadata.tables.keys()

print(type(table_names))
# Print the list of table names
for table_name in table_names:
    print(table_name)