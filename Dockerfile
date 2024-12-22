FROM --platform=$BUILDPLATFORM rokadias/python-opencv:main

WORKDIR /xbot/alt/

COPY ./requirements.txt .

RUN pip install -r /xbot/alt/requirements.txt --no-cache-dir

COPY ./src ./src

CMD ["python", "/xbot/alt/src/centralMainProcessAsync.py"]
