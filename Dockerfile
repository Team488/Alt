ARG TARGETPLATFORM
FROM arm64v8/python:3.10.16-slim-bookworm

# Install basic dependencies, Python-related packages, and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ca-certificates curl wget \
    openssl git ffmpeg tar lsb-release \
    procps manpages-dev unzip zip xauth swig \
    python3-numpy python3-distutils python3-setuptools python3-pyqt5 python3-opencv \
    libboost-python-dev libboost-thread-dev libatlas-base-dev libavcodec-dev \
    libavformat-dev libavutil-dev libcanberra-gtk3-module libeigen3-dev \
    libglew-dev libgl1-mesa-dev libgl1-mesa-glx libglib2.0-0 libgtk2.0-dev \
    libgtk-3-dev libjpeg-dev liblapack-dev liblapacke-dev libopenblas-dev \
    libopencv-dev libpng-dev libpostproc-dev libpq-dev libsm6 libswscale-dev \
    libtbb-dev libtesseract-dev libtiff-dev libtiff5-dev libv4l-dev libx11-dev \
    libxext6 libxine2-dev libxrender-dev libxvidcore-dev libx264-dev \
    libgtkglext1 libgtkglext1-dev libvtk9-dev libdc1394-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev libopenexr-dev \
    openexr qv4l2 v4l-utils zlib1g-dev && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Set work directory in the container
WORKDIR /app

# Copy the local base-requirements.txt to the container
COPY docker-base/base-requirements.txt /app/base-requirements.txt

# Install Python packages globally from base-requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r /app/base-requirements.txt && \
    pip install --no-cache-dir --prefer-binary h5py

# Step 2
WORKDIR /xbot/Alt/src

COPY non-base-requirements.txt /xbot/Alt/non-base-requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev
    # rm -rf /var/lib/apt/lists/* && apt-get clean

# this dependency allows cmake to install
RUN apt-get install -y python3-launchpadlib

# Install cmake from the official repository
RUN apt-get install -y software-properties-common && \
    add-apt-repository ppa:george-edison55/cmake-3.x && \
    apt-get update && \
    apt-get install -y cmake


RUN apt-get update && \
    apt-get install -y python3-pip

# installing robotpy__apriltag (currenntly this installs all of robotpy)
WORKDIR /xbot/Alt
RUN git clone https://github.com/robotpy/mostrobotpy.git
# into repo
WORKDIR /xbot/Alt/mostrobotpy
# keep deterministic for mostrobotpy
RUN git fetch origin
RUN git checkout f16ab492127e01f8db152ecfd0de47acbce5674a

RUN pip install pybind11
RUN pip install --upgrade pip
RUN pip install -r rdev_requirements.txt  # Install project-specific dependencies
RUN pip install numpy  # Install numpy separately, as instructed
RUN pip install devtools
# Step 5: Make the rdev.sh script executable
RUN chmod +x rdev.sh

# Step 6: Run the build command to generate the wheels
RUN ./rdev.sh ci run

# Step 7: Install the resulting wheels
RUN pip install dist/*.whl
# to make this only install apriltag we can find that whl only, but it might break it


# go back to regular workdir
WORKDIR /xbot/Alt



RUN pip install --no-cache-dir --prefer-binary XTablesClient&& \
    apt-get install -y build-essential python3-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install build && \
    pip install scikit-fmm && \
    pip install pyflame && \
    pip install grpcio-tools && \
    pip install grpcio

RUN pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir && \
    pip install pynetworktables

RUN pip install --no-cache-dir --prefer-binary -r non-base-requirements.txt


COPY ./src/assets/librknnrt.so /usr/lib/librknnrt.so

WORKDIR /xbot/Alt/src
