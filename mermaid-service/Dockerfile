FROM node:20-bookworm

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv chromium && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @mermaid-js/mermaid-cli

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

COPY ./source /app/source

WORKDIR /app/source

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003"]