FROM python:3.11-slim

WORKDIR /app

COPY echo_bot.py .

RUN pip install --no-cache-dir discord.py

CMD ["python", "echo_bot.py"]