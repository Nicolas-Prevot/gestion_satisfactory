# Gestion Satisfactory

This project is a web application designed to help you manage and optimize production recipes in the game Satisfactory.

## Prerequisites

### For running with Docker

- Docker
- Docker compose

## Running the App with Docker

### Setup Instructions

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

3. Build and Run the Docker Containers

    ```bash
    docker compose up -d --build
    ```

4. Access the Application

   - Open your web browser and navigate to `http://localhost:<PORT_WEBAPP>` (the port you specified in the .env file).
