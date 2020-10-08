FROM continuumio/miniconda3

RUN conda create -n env python=3.7
COPY ./requirements-conda.txt /tmp/requirements-conda.txt
RUN conda install -n env --yes --channel conda-forge \
  --file /tmp/requirements-conda.txt

RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

WORKDIR /opt/aviris

COPY ./build_catalog.py build_catalog.py
COPY ./aviris-flight-lines.csv aviris-flight-lines.csv

ENTRYPOINT [ "python3", "build_catalog.py" ]
