FROM python:3.12-slim AS runtime

# Prevents Python from writing .pyc files to disc
# Forces the stdout and stderr streams to be unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./source /app/source

WORKDIR /app/source

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8004"]

# ─── Test stage: production image + test-only dependencies ───
FROM runtime AS test
RUN pip install --no-cache-dir pytest httpx pytest-cov
