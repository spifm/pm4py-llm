FROM python:3.12-slim

# Prevents Python from writing .pyc files to disc
# Forces the stdout and stderr streams to be unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt update && apt install -y iputils-ping && apt install -y curl

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./source /app/source

WORKDIR /app/source

USER root

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

