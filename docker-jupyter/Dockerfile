# Use the specific Jupyter scipy-notebook image as the base
FROM jupyter/scipy-notebook:2023-08-03

# Dependencies
USER root

RUN apt-get update && \
    apt-get install -y libpcap-dev libpcap0.8

USER jovyan

# If you have additional steps such as installing more packages or copying files, you can add them here.
# Example: 
# COPY ./some_local_directory_or_file /path/in/container/
# RUN pip install some_additional_package
RUN pip install scapy
#RUN pip install influxdb-client
RUN pip install python-dotenv
RUN pip install elasticsearch
