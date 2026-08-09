# Custom Airflow 3.3.0 image with VOXMETRIKS ELT runtime deps.
# Official practice: keep apache-airflow pinned to the image version while installing extras.
# https://airflow.apache.org/docs/docker-stack/build.html
# Constraints: https://raw.githubusercontent.com/apache/airflow/constraints-3.3.0/constraints-3.12.txt
FROM apache/airflow:3.3.0-python3.12

ARG AIRFLOW_CONSTRAINTS_URL=https://raw.githubusercontent.com/apache/airflow/constraints-3.3.0/constraints-3.12.txt

USER root
RUN mkdir -p /opt/voxmetriks/analytics /opt/voxmetriks/data \
    && chown -R airflow:root /opt/voxmetriks

USER airflow

# Copy only the analytics ELT package required by orchestrated stages.
COPY --chown=airflow:root analytics/elt /opt/voxmetriks/analytics/elt
COPY --chown=airflow:root infrastructure/airflow/requirements.txt /requirements.txt

RUN pip install --no-cache-dir \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /requirements.txt \
        --constraint "${AIRFLOW_CONSTRAINTS_URL}" \
    && pip check \
    && python -c "from airflow.sdk import DAG; \
from airflow.providers.standard.operators.bash import BashOperator; \
from airflow.providers.fab.auth_manager.fab_auth_manager import FabAuthManager; \
print('airflow_public_imports_ok')"

ENV PYTHONPATH="/opt/voxmetriks/analytics:${PYTHONPATH}" \
    VOXMETRIKS_DATA_DIR=/opt/voxmetriks/data \
    DB_PATH=/opt/voxmetriks/data/warehouse/voxmetrik.duckdb
