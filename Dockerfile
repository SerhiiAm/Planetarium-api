FROM python:3.13-slim
LABEL maintainer="ambartsumov.work@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/files/media /app/files/static && \
    adduser --disabled-password --no-create-home my_user && \
    chown -R my_user:my_user /app/files && \
    chmod -R 755 /app/files

USER my_user
