FROM quay.io/jmcclain/raster-vision-pytorch:Sat_Jan_8_05_00_23_UTC_2022

COPY catalog_*.zip /workdir/
COPY catalogs.json /workdir/catalogs.json
COPY pipeline.py /workdir/pipeline.py

WORKDIR /workdir

CMD ["bash"]

# docker build -f Dockerfile -t algae-model .
