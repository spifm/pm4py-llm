FROM pm4py/pm4py-core:2.7.11

RUN pip install pyarrow

# For integration with LLM
RUN pip install transformers requests

# For serving the code
RUN pip install fastapi uvicorn


ENV PATH="/usr/bin/python3:${PATH}"

# Create a non-root user to run the application
RUN useradd -ms /bin/bash appuser
RUN mkdir -p /app && chown -R appuser:appuser /app

USER appuser

WORKDIR /app

CMD ["uvicorn", "api_app:app", "--host", "0.0.0.0", "--port", "8001"]