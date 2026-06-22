FROM pm4py/pm4py-core:2.7.11 AS runtime

# Prevents Python from writing .pyc files to disc
# Forces the stdout and stderr streams to be unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV PATH="/usr/bin/python3:${PATH}"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade "openai==2.8.1"
RUN pip install --no-cache-dir -r /app/requirements.txt

USER root

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]

# ─── Test stage: production image + test-only dependencies ───
FROM runtime AS test
RUN pip install --no-cache-dir pytest httpx pytest-cov