FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p input logs reports archive
ENV BOT_DB_PATH=/app/data/bot.db
EXPOSE 8000
# Default: start the monitoring API. Run the bot with:
#   docker run -v $(pwd)/input:/app/input invoice-bot python main.py run input/invoices.xlsx
CMD ["python", "-c", "import uvicorn; from bot.api import create_app; uvicorn.run(create_app(), host='0.0.0.0', port=8000)"]
