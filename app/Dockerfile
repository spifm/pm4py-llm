FROM pm4py/pm4py-core:2.7.11

ENV PATH="/usr/bin/python3:${PATH}"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

USER root

CMD ["uvicorn", "api_app:app", "--host", "0.0.0.0", "--port", "8001"]