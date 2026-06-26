FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN python -m pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv install

COPY . .

EXPOSE 8000
CMD ["uv", "run", "start"]
