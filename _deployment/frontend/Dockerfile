FROM node:26-slim

WORKDIR /app

COPY ./control_panel/frontend/package*.json ./control_panel/frontend/

RUN cd control_panel/frontend && npm install

COPY . /app

WORKDIR /app/control_panel/frontend

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "--port", "5173"]