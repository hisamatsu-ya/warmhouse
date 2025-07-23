FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/temperature_api.py .

EXPOSE 8081

CMD ["python", "temperature_api.py"]
