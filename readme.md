# How to setup the workspace

## Setup Docker + PostGre server

install Docker

```bash
docker pull postgres
```

create '.env' file and add the following parameters:

```properties
HOST=postgres
PORT_POSTGRES=<postgres_port>
PORT_WEBAPP=<webapp_port>
POSTGRES_DB=satisfactory
USER=postgres
POSTGRES_PASSWORD=<database_mdp>
```

```bash
docker compose up -d --build
```

## Setup Python env + init (development purpose)

```bash
python install -r ./app/requirements.txt
```

To update database from terminal:
```bash
python update_bdd_from_web.py
```

To execute app from terminal:
```bash
cd ./app
Streamlit run ./❔_HowTo.py __setEnv --server.port <server_port> --server.enableStaticServing true
```
