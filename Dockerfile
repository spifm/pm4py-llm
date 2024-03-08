FROM pm4py/pm4py-core:latest

RUN pip install pyarrow

ENV PATH="/usr/bin/python3:${PATH}"

WORKDIR /pm4py_app

CMD ["tail", "-f", "/dev/null"]