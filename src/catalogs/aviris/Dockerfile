FROM continuumio/miniconda3:4.8.2 AS app

RUN conda install --yes --channel conda-forge python=3.8
COPY ./requirements-conda.txt /tmp/requirements-conda.txt
RUN conda install --yes --channel conda-forge \
  --file /tmp/requirements-conda.txt

RUN pip install git+https://github.com/azavea/stacframes.git@dd7959d1a9fee7227624aa185f797402209b0ad0

WORKDIR /workspace

ENTRYPOINT [ "python", "build_catalog.py" ]
