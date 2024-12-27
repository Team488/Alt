from xdash-alt-base-image
workdir /app
copy . .
# Install system dependencies
run apt-get update && apt-get install -y \
    libopencv-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    build-essential \
    gfortran \
    libssl-dev \
    libffi-dev \
    libhdf5-dev \
    libgrpc-dev \
    libprotobuf-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

run pip install -r aarch-requirements.txt

workdir /app/src

Cmd ["python","centralOrangePiProcess.py"]