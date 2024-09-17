FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nano \
    build-essential \
    make \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir poetry --verbose

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY .streamlit .streamlit
COPY conf conf
COPY src src

ENV PYTHONPATH="/app/src:${PYTHONPATH}"

HEALTHCHECK CMD curl --fail "http://localhost:${PORT_WEBAPP:-8501}/_stcore/health" || exit 1

CMD poetry run streamlit run src/gestion_satisfactory/main.py --server.enableStaticServing true --server.port ${PORT_WEBAPP:-8501}


# CMD ["poetry", "run", "streamlit", "run", "src/acc_pallm_web/main.py"]

# CMD streamlit run ❔_HowTo.py --server.enableStaticServing true --server.port ${PORT_WEBAPP}
