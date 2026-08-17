FROM python:3.12-slim

WORKDIR /app
COPY apps/web apps/web
COPY apps/teams/appPackage apps/teams/appPackage
COPY packages/demo-data packages/demo-data
COPY packages/fabric-data/generated packages/fabric-data/generated
COPY services/api services/api

ENV HOST=0.0.0.0
ENV PORT=8080
EXPOSE 8080

CMD ["python", "services/api/server.py"]
