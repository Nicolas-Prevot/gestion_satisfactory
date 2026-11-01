FROM node:22-slim

WORKDIR /app/apps/frontend

COPY apps/frontend/package*.json ./
RUN npm ci

COPY apps/frontend ./

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
