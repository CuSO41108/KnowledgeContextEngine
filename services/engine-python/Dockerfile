FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY services/engine-python/pyproject.toml /workspace/services/engine-python/pyproject.toml
COPY services/engine-python/app /workspace/services/engine-python/app
COPY scripts /workspace/scripts
COPY data /workspace/data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /workspace/services/engine-python

WORKDIR /workspace/services/engine-python

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
