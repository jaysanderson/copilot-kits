FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py arag.py ./
COPY static ./static
COPY corpus/index.json ./corpus/index.json
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
