FROM pm4py/pm4py-core:latest

RUN pip install pyarrow

# For integration with LLM
RUN pip install transformers requests

ENV PATH="/usr/bin/python3:${PATH}"

WORKDIR /pm4py_llm

CMD ["tail", "-f", "/dev/null"]