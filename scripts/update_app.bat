@echo off

set PROJECT_PATH=%~dp0..\
set CURRENT_PATH=%~dp0

cd /d %PROJECT_PATH%

@REM Stop the container(s) using the following command:
start /WAIT /B docker-compose down

@REM Delete all containers using the following command:
start /WAIT /B docker rmi -f gestion_satisfactory_app
start /WAIT /B docker rmi -f postgres

@REM Delete all volumes using the following command:
@REM docker volume rm $(docker volume ls -q)

@REM Restart the containers using the following command:
start /WAIT /B docker compose up -d --build

cd /d %CURRENT_PATH%