FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir discord.py flask aiohttp

CMD ["python", "forgejo-discord-bot.py"]