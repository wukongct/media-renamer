FROM ubuntu:focal
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

RUN apt-get update && apt-get install -y exiv2 ffmpeg python3.8 python3.8-venv python3.8-distutils python3.8-dev pip libheif-examples
WORKDIR /usr/src/app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py main.py
COPY library.py library.py
COPY run_rename.sh run_rename.sh
ENV DATA_DIR=/data
ENV INPUT_DIR=input
ENV OUTPUT_DIR=originals
CMD ./run_rename.sh

# Using cron to schedule does not work yet
#COPY mr_cron /etc/cron.d/mr_cron
#RUN chmod 0644 /etc/cron.d/mr_cron
# RUN touch /data/mr_log.log && touch /data/mr_main.log
#ENTRYPOINT [ "cron", "-f" ]
