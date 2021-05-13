FROM quay.io/azavea/openjdk-gdal:3.1-jdk11-slim

RUN set -ex \
      && addgroup --system nasa-hyperspectral \
      && adduser \
        --system \
        --disabled-login \
        --disabled-password \
        --home /var/lib/nasa-hyperspectral \
        --shell /sbin/nologin \
        --ingroup nasa-hyperspectral \
        nasa-hyperspectral

COPY ./target/scala-2.13/cog-clip-assembly.jar /var/lib/nasa-hyperspectral/

USER nasa-hyperspectral
WORKDIR /var/lib/nasa-hyperspectral

ENTRYPOINT ["java", "-XX:+UseG1GC", "-jar", "cog-clip-assembly.jar"]
