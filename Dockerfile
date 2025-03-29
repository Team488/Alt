FROM rokadias/488-alt-python-3.11
WORKDIR /xbot/Alt/src

RUN pip install --upgrade tensorflow
RUN pip install --upgrade XTablesClient
RUN pip install --upgrade ultralytics
RUN pip install --upgrade python-doctr[torch,viz,html,contrib]==0.11.0
