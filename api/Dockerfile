FROM python:3.10-slim

RUN apt update && apt install -y iputils-ping && apt install -y curl

WORKDIR /api

COPY requirements.txt .

RUN pip install --no-cache-dir -r /api/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
