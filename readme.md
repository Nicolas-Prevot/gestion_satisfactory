# How to setup the workspace

## Setup Docker + PostGre server

install Docker

docker pull postgres

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

## Setup Python env + init

python install -r requirements.txt

python update_bdd_from_web.py
