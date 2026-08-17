FROM python:3.12-slim

WORKDIR /app
COPY apps/teams/requirements.txt apps/teams/requirements.txt
RUN pip install --no-cache-dir -r apps/teams/requirements.txt
COPY apps/teams/src apps/teams/src
COPY packages/demo-data packages/demo-data
COPY services/api/providers.py services/api/providers.py

ENV HOST=0.0.0.0
ENV PORT=3978
EXPOSE 3978

CMD ["python", "apps/teams/src/bot_server.py"]
