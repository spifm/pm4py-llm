FROM python:3.10-slim

RUN apt update && apt install -y iputils-ping && apt install -y curl

WORKDIR /api

COPY requirements.txt .

RUN pip install --no-cache-dir -r /api/requirements.txt

RUN useradd -ms /bin/bash appuser
RUN chown -R appuser:appuser /api

USER appuser

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
