#Build stage
FROM node:20-slim AS builder
WORKDIR /app

RUN npm install -g pnpm 

COPY package.json pnpm-lock.yaml /app/
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

#Runtime stage
FROM node:20-slim
WORKDIR /app
RUN npm install -g pnpm
COPY --from=builder /app/package.json /app/pnpm-lock.yaml /app/
RUN pnpm install --prod --frozen-lockfile
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["pnpm", "start"]