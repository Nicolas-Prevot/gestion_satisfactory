FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get -y upgrade && apt-get install -y curl wget nano build-essential make

COPY . .

RUN pip install -r requirements.txt

ARG PORT_WEBAPP

EXPOSE ${PORT_WEBAPP}

CMD streamlit run ❔_HowTo.py --server.enableStaticServing true --server.port ${PORT_WEBAPP}