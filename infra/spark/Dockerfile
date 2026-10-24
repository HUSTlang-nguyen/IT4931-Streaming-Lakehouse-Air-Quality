FROM python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_LOCAL_IP=127.0.0.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless=17.0.20.1+1-1~deb12u1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/container.in /tmp/container.in
COPY requirements/runtime-py311.lock /tmp/runtime.lock
RUN pip install --no-cache-dir -r /tmp/runtime.lock -r /tmp/container.in
COPY infra/spark/download_jars.py /tmp/download_jars.py
COPY requirements/java-artifacts.lock.json /tmp/java-artifacts.lock.json
RUN python /tmp/download_jars.py
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps . && pip check \
    && pip freeze --exclude air-quality-lakehouse > /opt/runtime-requirements.lock
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark
CMD ["python", "-m", "air_quality.processing.jobs", "smoke"]
