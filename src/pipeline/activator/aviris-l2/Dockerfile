FROM continuumio/miniconda3:4.8.2 AS app

RUN conda install --yes python=3.8
COPY ./requirements-conda.txt /tmp/requirements-conda.txt
RUN conda install --yes --channel conda-forge \
  --file /tmp/requirements-conda.txt

WORKDIR /workspace

ENTRYPOINT [ "python", "main.py" ]
