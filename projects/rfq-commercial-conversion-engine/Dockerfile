FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system .
EXPOSE 8010
CMD ["uvicorn","rfq_cc.api:app","--host","0.0.0.0","--port","8010"]
