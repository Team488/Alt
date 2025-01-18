ARG TARGETPLATFORM
FROM kobeeeef/xdash-alt-base-image:today

WORKDIR /xbot/Alt

COPY non-base-requirements.txt /xbot/Alt/non-base-requirements.txt

RUN mkdir src && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r non-base-requirements.txt && \
    pip install --no-cache-dir --prefer-binary XTablesClient && \
    pip install pyflame

RUN pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir && \
    pip install pynetworktables


COPY ./src ./src


WORKDIR /xbot/Alt/src


COPY ./src/assets/librknnrt.so /usr/lib/librknnrt.so


CMD ["python", "centralOrangePiProcess.py"]
