#!/bin/bash

cd ..

# Stop the container(s) using the following command:
docker-compose down

# Delete all containers using the following command:
docker rmi -f gestion_satisfactory_app
docker rmi -f postgres

# Delete all volumes using the following command:
#docker volume rm $(docker volume ls -q)

# Restart the containers using the following command:
docker-compose up -d --build

cd scripts