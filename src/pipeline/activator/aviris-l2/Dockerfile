FROM continuumio/miniconda3:4.10.3

RUN mkdir -p /usr/local/src
WORKDIR /usr/local/src

COPY requirements-conda.txt /usr/local/src/requirements-conda.txt

RUN set -ex \
  && conda install --yes --channel conda-forge python=3.8 \
  && conda install --yes --channel conda-forge --file /usr/local/src/requirements-conda.txt

COPY . /usr/local/src

ENTRYPOINT [ "python", "main.py" ]
