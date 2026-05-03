
FROM node:20-slim

WORKDIR /src

RUN npm install -g pnpm 

COPY package.json .
RUN pnpm install

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]