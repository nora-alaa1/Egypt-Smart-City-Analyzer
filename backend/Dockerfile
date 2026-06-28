FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir scikit-learn==1.8.0

COPY . .

EXPOSE 7860

CMD ["uvicorn", "smartcity_api:app", "--host", "0.0.0.0", "--port", "7860"]
