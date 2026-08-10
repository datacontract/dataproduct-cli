FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/entropy-data/dataproduct-cli"
LABEL org.opencontainers.image.description="CLI for data products following the Open Data Product Standard (ODPS)"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

WORKDIR /work

ENTRYPOINT ["dataproduct"]
CMD ["--help"]
