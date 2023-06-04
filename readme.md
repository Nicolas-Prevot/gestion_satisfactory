# How to setup the workspace

## Setup Docker + PostGre server

install Docker

```bash
docker pull postgres
```

create docker-compose.yaml

```yaml
version: "3.9"
services:
  postgres:
    image: postgres
    container_name: <mon-postgres>
    restart: always
    ports:
      - 5432:5432
    environment:
      POSTGRES_PASSWORD: <mypassword>
      POSTGRES_DB: satisfactory
    volumes:
      - ./pg_data:/var/lib/postgresql/data
```

```bash
docker-compose up -d
```

## Setup Python env + init

```bash
python install -r requirements.txt
```

create folder configs then 
create file postgre.yaml

```yaml
PostgreSQL:
  host: localhost
  port: 5432
  database: satisfactory
  user: postgres
  password: <mypassword>
```

```bash
python update_bdd_from_web.py
```

```bash
streamlit run .\streamlit.py --server.enableStaticServing true --server.port <8501>
```
