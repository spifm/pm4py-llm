FROM python:3.10-slim

RUN apt update && apt install -y iputils-ping && apt install -y curl

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

USER root

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
