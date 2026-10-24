FROM apache/superset:4.1.2@sha256:15e110b8533d3cb6a0d529512ea71252b0ac62e3f72b1f7a5000f1361822ac26
USER root
RUN pip install --no-cache-dir psycopg2-binary==2.9.10 trino==0.335.0
COPY infra/superset/superset_config.py /app/config/superset_config.py
COPY infra/superset/boot.py /app/config/boot.py
USER superset
CMD ["python", "/app/config/boot.py"]
