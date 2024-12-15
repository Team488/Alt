FROM --platform=$BUILDPLATFORM python:3.9.21-slim-bookworm AS build

COPY ./requirements.txt /xbot/alt/

RUN apt-get update -yqq \
  && apt-get install -yqq build-essential openssl curl git \
  && rm -rf /var/lib/apt/lists/*

RUN pip install -r /xbot/alt/requirements.txt --no-cache-dir

# The real docker image below that doesn't take the gcc and g++ from build-essential.
FROM python:3.9.21-slim-bookworm

ENV PYTHONPATH=/xbot/alt/src

COPY --from=build /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=build /usr/local/bin/ /usr/local/bin/

COPY ./requirements.txt /xbot/alt/
COPY ./src /xbot/alt/src

CMD ["python", "/xbot/alt/src/centralMainProcessAsync.py"]
