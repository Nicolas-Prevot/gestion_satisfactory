# How to setup the workspace

## Setup Docker + PostGre server

install Docker

```bash
docker pull postgres
```

create '.env' file and add the following parameters:

```yaml
HOST: <hostname>
PORT_POSTGRES: <postgres_port>
PORT_WEBAPP: <postgres_port>
DATABASE: <database_name>
USER: <database_user>
PASSWORD: <database_mdp>
```

```bash
docker compose up -d --build
```

## Setup Python env + init

```bash
python install -r requirements.txt
```

```bash
python update_bdd_from_web.py
```

```bash
# The server port 8501 can be choosen differently, it's up to you !
streamlit run .\streamlit.py --server.enableStaticServing true --server.port 8501
```
