FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y curl && apt-get clean

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN mkdir -p /app/tmp

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

RUN chmod -R 777 /app/tmp

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]