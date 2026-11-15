FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py pagemode.py embed.py insights.py wander.py graphwalk.py chat.py answers.py sections.py runsheet.py ./
COPY graph/graph_edges.json ./graph/
COPY thumbs/manifest.json ./thumbs/manifest.json
COPY static ./static
COPY templates ./templates
ENV HOST=0.0.0.0 PORT=8080
EXPOSE 8080
CMD ["python", "app.py"]
