ARG TARGETPLATFORM
FROM xdash-alt-base-image

WORKDIR /xbot/Alt

COPY non-base-requirements.txt /xbot/Alt/non-base-requirements.txt

RUN mkdir src && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r non-base-requirements.txt && \
    pip install --no-cache-dir --prefer-binary XTablesClient

COPY ./src ./src


WORKDIR /xbot/Alt/src

RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install rknn-toolkit2==2.3.0 --no-cache-dir; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir; \
    fi

CMD ["python", "centralOrangePiProcess.py"]
