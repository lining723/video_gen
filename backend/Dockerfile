FROM python:3.13-slim
WORKDIR /app
COPY backend /app/backend
COPY .env.example /app/.env.example
EXPOSE 8100
CMD ["python", "-m", "backend.src.api.app"]
