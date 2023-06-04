import psycopg2

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="satisfactory",
    user="postgres",
    password="123mdp456"
)

# Connexion à la base de données PostgreSQL
#   conn = psycopg2.connect(
#       host=config.PostgreSQL.host,
#       port=config.PostgreSQL.port,
#       database=config.PostgreSQL.database,
#       user=config.PostgreSQL.user,
#       password=config.PostgreSQL.password
#   )

##################################### CREATION TABLE ######################################

# # Création d'un curseur pour exécuter des requêtes
# cur = conn.cursor()
# 
# # Exemple : Création d'une table
# cur.execute("""
#     CREATE TABLE employes (
#         id SERIAL PRIMARY KEY,
#         nom VARCHAR(100),
#         age INTEGER,
#         salaire REAL
#     )
# """)
# 
# # Validation de la transaction
# conn.commit()
# 
# # Fermeture du curseur et de la connexion à la base de données
# cur.close()


##################################### PRINT DATA ######################################

# Création d'un curseur pour exécuter des requêtes
cur = conn.cursor()

# Exemple : Sélection de toutes les lignes de la table employes
cur.execute("SELECT * FROM employes")
rows = cur.fetchall()

print("\nPrint data : ")
# Affichage des résultats
for row in rows:
    print(row)

# Fermeture du curseur et de la connexion à la base de données



##################################### INSERT DATA ######################################


# Exemple : Insertion de données
cur.execute("""
    INSERT INTO employes (nom, age, salaire)
    VALUES ('John Doe', 30, 5000.0)
""")

cur.execute("""
    INSERT INTO employes (nom, age, salaire)
    VALUES ('Jane Smith', 28, 4500.0)
""")

# Validation de la transaction
conn.commit()


# Exemple : Mise à jour d'une ligne dans la table employes
cur.execute("""
    UPDATE employes
    SET salaire = 6666.0
    WHERE id = 1
""")

# Validation de la transaction
conn.commit()


##################################### PRINT DATA ######################################


# Exemple : Sélection de toutes les lignes de la table employes
cur.execute("SELECT * FROM employes")
rows = cur.fetchall()

print("\nPrint data : ")
# Affichage des résultats
for row in rows:
    print(row)


# Fermeture du curseur et de la connexion à la base de données
cur.close()



conn.close()