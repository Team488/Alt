ARG TARGETPLATFORM
FROM --platform=$BUILDPLATFORM rokadias/python-opencv:main

WORKDIR /xbot/alt/

COPY ./requirements.txt .

RUN pip install -r /xbot/alt/requirements.txt --no-cache-dir

COPY ./src ./src

RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install rknn-toolkit2==2.3.0 --no-cache-dir; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir; \
    fi

CMD ["python", "/xbot/alt/src/centralMainProcessAsync.py"]
