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
# you have to run the dockerfile with --device /dev/color_camera:/dev/video0
# this means the /dev/color_camera symlink has to have been created with udev rules, and then the user must be added to the docker group
# command for color camera: ATTRS{idProduct}=="6366",ATTRS{idVendor}=="0c45",SYMLINK+="color_camera",GROUP="docker", MODE="0660"