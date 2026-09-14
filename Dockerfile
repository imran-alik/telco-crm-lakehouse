FROM python:3.12-slim

WORKDIR /app

COPY codebase/requirements.txt codebase/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r codebase/requirements.txt

COPY codebase/ codebase/
COPY scheduler/ scheduler/
COPY data/source/ data/source/

ENV PYTHONPATH=codebase

RUN chmod +x scheduler/run_layers.sh

CMD ["python", "codebase/scripts/certify_public_run.py"]
