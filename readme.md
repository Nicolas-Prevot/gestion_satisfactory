# Gestion Satisfactory

This project is a web application designed to help you manage and optimize production recipes in the game Satisfactory.

## Prerequisites

### For running with Docker

- Docker
- Docker compose

### For running as standalone process

- conda

## Setup Instructions

1. Clone the Repository

    ```bash
    git clone https://github.com/Nicolas-Prevot/gestion_satisfactory.git
    cd gestion_satisfactory
    ```

2. Set Up Environment Variables

    - Copy the `default.env` file to `.env` if it doesn't exist:

        ```bash
        cp default.env .env
        ```

    - Update the `.env` file with your desired configuration.

3. Run the Webapp with/without Docker:

    - Option 1: Webapp with Docker & postgres database with Docker

        ```bash
        docker compose -f docker-compose.yaml -f docker-compose.postgres.yaml up -d --build
        ```

    - Option 2: Webapp with Docker & sqlite database

        ```bash
        docker compose up -d --build
        ```

    - Option 3: Webapp & sqlite database without Docker

        1. Start by instanciating your *Conda* environment by running the following command:

            ```bash
            conda env create -v -f environment.yml --force
            conda activate satisfactory
            ```

        2. Install project dependencies with *Poetry*:

            ```bash
            poetry install --without dev
            ```

        3. Run the Webapp

            ```bash
            poetry run app
            ```

4. Access the Application

   - Open your web browser and navigate to `http://localhost:<PORT_WEBAPP>` (the port you specified in the .env file).
