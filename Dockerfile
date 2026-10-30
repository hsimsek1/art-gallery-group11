FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 'gunicorn>=22,<26'
COPY database ./database
COPY src ./src
COPY wsgi.py ./wsgi.py
RUN mkdir -p /app/instance
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "wsgi:app"]
