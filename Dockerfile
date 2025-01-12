ARG TARGETPLATFORM
FROM xdash-alt-base-image

WORKDIR /xbot/Alt

RUN mkdir src

RUN pip install --prefer-binary XTablesClient

COPY ./src ./src

WORKDIR /xbot/Alt/src

RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install rknn-toolkit2==2.3.0 --no-cache-dir; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir; \
    fi

CMD ["python", "centralOrangePiProcess.py"]
