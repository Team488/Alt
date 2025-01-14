ARG TARGETPLATFORM
FROM rokadias/python-opencv:main

WORKDIR /xbot/Alt

RUN apt-get update -yqq && \
    apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev libffi-dev liblzma-dev libhdf5-dev \
        python3-numpy python3-distutils \
        python3-setuptools python3-pyqt5 python3-opencv python3-zeroconf \
        libboost-python-dev libboost-thread-dev libatlas-base-dev libavcodec-dev \
        libavformat-dev libavutil-dev libcanberra-gtk3-module libeigen3-dev \
        libglew-dev libgl1-mesa-dev libgl1-mesa-glx libglib2.0-0 libgtk2.0-dev \
        libgtk-3-dev libjpeg-dev liblapack-dev \
        liblapacke-dev libopenblas-dev libopencv-dev libpng-dev libpostproc-dev \
        libpq-dev libsm6 libswscale-dev libtbb-dev libtesseract-dev \
        libtiff-dev libtiff5-dev libv4l-dev libx11-dev libxext6 libxine2-dev \
        libxrender-dev libxvidcore-dev libx264-dev libgtkglext1 libgtkglext1-dev \
        libvtk9-dev libdc1394-dev libgstreamer-plugins-base1.0-dev \
        libgstreamer1.0-dev libopenexr-dev \
        openexr \
        qv4l2 \
        v4l-utils \
        zlib1g-dev \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean

COPY ./requirements.txt .

# Install Python packages globally from requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install XTablesClient==5.2.4

COPY ./src ./src

WORKDIR /xbot/Alt/src

RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install rknn-toolkit2==2.3.0 --no-cache-dir; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        pip install rknn-toolkit-lite2==2.3.0 --no-cache-dir; \
    fi

CMD ["python", "centralOrangePiProcess.py"]
