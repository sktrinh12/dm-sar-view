ARG PYTHON_VERSION=3.9

FROM debian:buster AS client

ARG ORACLE_VERSION=19.18.0.0.0
ARG OR_SHORT_VER=1918000

WORKDIR /root
ARG ORACLE_ZIP_INTERNAL_FOLDER=instantclient_19_18
ENV CLIENT_ZIP=instantclient-basiclite-linux.x64-${ORACLE_VERSION}dbru.zip
ENV SDK_ZIP=instantclient-sdk-linux.x64-${ORACLE_VERSION}dbru.zip
ENV DEBIAN_FRONTEND=noninteractive

# https://download.oracle.com/otn_software/linux/instantclient/1917000/instantclient-sdk-linux.x64-19.17.0.0.0dbru.zip
# https://download.oracle.com/otn_software/linux/instantclient/1917000/instantclient-basiclite-linux.x64-19.17.0.0.0dbru.zip

RUN apt-get update \
    && apt-get -yq install unzip curl

RUN curl -LJO "https://download.oracle.com/otn_software/linux/instantclient/${OR_SHORT_VER}/${CLIENT_ZIP}"\
	&& curl -LJO "https://download.oracle.com/otn_software/linux/instantclient/${OR_SHORT_VER}/${SDK_ZIP}"

# ADD insta* .
RUN unzip ${CLIENT_ZIP} && unzip ${SDK_ZIP}
RUN mv ${ORACLE_ZIP_INTERNAL_FOLDER} oracle

FROM python:${PYTHON_VERSION}

ARG USERNAME=backend
ARG ORACLE_HOST
ARG ORACLE_USER
ARG ORACLE_PASS
ARG ORACLE_PORT
ARG ORACLE_SID
ARG DB_TYPE=PROD
ARG ENV
ARG REDIS_HOST
ARG REDIS_PASSWD

ENV REDIS_HOST=${REDIS_HOST}
ENV REDIS_PASSWD=${REDIS_PASSWD}
ENV DB_TYPE=${DB_TYPE}
ENV ENV=${ENV}
ENV ORACLE_HOST=${ORACLE_HOST}
ENV ORACLE_PORT=${ORACLE_PORT}
ENV ORACLE_SID=${ORACLE_SID}
ENV ORACLE_PASS=${ORACLE_PASS}
ENV ORACLE_USER=${ORACLE_USER}
ENV HOME "/home/${USERNAME}"
ENV ORACLE_HOME /opt/oracle
ENV TNS_ADMIN ${ORACLE_HOME}/network/admin

VOLUME ["${TNS_ADMIN}"]

RUN mkdir -p ${HOME}/app
ADD main.py requirements.txt ${HOME} 
ADD app ${HOME}/app
RUN pip install -r ${HOME}/requirements.txt
COPY --from=client /root/oracle ${ORACLE_HOME}
RUN apt-get update \
	&& apt-get -yq install libaio1 sudo \
	&& apt-get -yq autoremove \
	&& apt-get clean \
	&& adduser --home ${HOME} --shell /bin/bash ${USERNAME} \
	# Install Oracle Instant Client
	&& echo ${ORACLE_HOME} > /etc/ld.so.conf.d/oracle.conf \
	&& mkdir -p ${TNS_ADMIN} \
	&& ldconfig \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR ${HOME}
USER ${USERNAME}
EXPOSE 80
CMD ["python", "main.py"]
