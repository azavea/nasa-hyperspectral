FROM quay.io/azavea/openjdk-gdal:3.1-jdk8-slim

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

COPY ./target/scala-2.12/cog-clip-assembly.jar /var/lib/nasa-hyperspectral/

USER video-annotation
WORKDIR /var/lib/video-annotation

ENTRYPOINT ["java", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseCGroupMemoryLimitForHeap", "-jar", "cog-clip-assembly.jar"]
