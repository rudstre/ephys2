# Docker image for Ephys2

# We use Mamba rather than conda since it's faster and uses the newer `conda-forge` channel.
FROM condaforge/mambaforge
SHELL ["/bin/bash", "--login", "-c"]

# Disable interactive prompts when installing packages
ARG DEBIAN_FRONTEND=noninteractive 

# Install system libraries
RUN apt-get update && \
		apt-get install -y git \
												build-essential \
												cmake \
												openmpi-bin \
												libgl1-mesa-dev libgl1-mesa-glx \
												libxkbcommon-x11-0 \
												x11-utils \
												libyaml-dev \
												libegl1-mesa \
												libxcb-icccm4 \
												libxcb-image0 \
												libxcb-keysyms1 \
												libxcb-randr0 \
												libxcb-render-util0 \
												libxcb-xinerama0 \
												libopengl0 \
												libdbus-1-dev \
												pkg-config

# Install in the base environment for simplicity
RUN mamba install python=3.10
RUN pip install --upgrade pip

# Build CVXOPT (requires many system libraries, so we build separately)
# See http://cvxopt.org/install/index.html
RUN mamba install -c conda-forge osqp cvxopt -y

# Build source (ensure project root is working directory)
COPY ephys2 /ephys2 
WORKDIR /ephys2
RUN pip install -r setup-requirements.txt
RUN pip install -U .

# Build Qt 
RUN pip install PyQT6 pyqtgraph 

# Start GUI
COPY docker/GUI/entrypoint.sh /usr/bin 
RUN chmod a+rx /usr/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
