FROM python:3.12-slim

WORKDIR /app
COPY server.py .
COPY sites ./sites

ENV PORT=8080
EXPOSE 8080

USER nobody
CMD ["python", "-u", "server.py"]
