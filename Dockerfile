FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir ".[platform,postgresql,object-storage,identity]"

EXPOSE 8080

CMD ["sh", "-c", "python -m aevryn.cli api --host 0.0.0.0 --port ${PORT:-8080} --allowed-origin ${AEVRYN_API_ALLOWED_ORIGINS:-https://app.aevryn.ai}"]
