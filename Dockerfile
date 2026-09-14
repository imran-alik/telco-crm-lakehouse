FROM python:3.12-slim

ARG ONPREM_DB_PATH=/app/data/sink/lakehouse.db
ARG ONPREM_SAMPLES_DIR=/app/data/source/samples
ARG DUCKDB_THREADS=4
ARG MEMORY_LIMIT=2GB

WORKDIR /app

COPY codebase/requirements.txt codebase/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r codebase/requirements.txt

COPY codebase/ codebase/
COPY packages/ packages/
COPY medallion/ medallion/
COPY scheduler/ scheduler/
COPY data/source/ data/source/

ENV PYTHONPATH=codebase:packages/lakehouse_core \
    LAKEHOUSE_DB_PATH=${ONPREM_DB_PATH} \
    LAKEHOUSE_SAMPLES_DIR=${ONPREM_SAMPLES_DIR} \
    DUCKDB_THREADS=${DUCKDB_THREADS} \
    MEMORY_LIMIT=${MEMORY_LIMIT}

RUN chmod +x scheduler/run_layers.sh

CMD ["python", "codebase/scripts/certify_public_run.py"]
