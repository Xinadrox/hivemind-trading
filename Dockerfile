FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
COPY schemas ./schemas
COPY migrations ./migrations
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/src
USER nobody
CMD ["sh", "-c", "python -m hivemind.migrate && exec uvicorn hivemind.app:app --host 0.0.0.0 --port 8000"]
