#Build stage
# node:20-slim
FROM node@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS builder
WORKDIR /app

RUN npm install -g pnpm@10.30.3

COPY package.json pnpm-lock.yaml /app/
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

#Development stage
# node:20-slim
FROM node@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS development
WORKDIR /app
RUN npm install -g pnpm@10.30.3
COPY package.json pnpm-lock.yaml /app/
RUN pnpm install --frozen-lockfile
EXPOSE 3000
CMD ["pnpm", "dev"]

#Runtime stage
# node:20-slim
FROM node@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS production
WORKDIR /app
RUN npm install -g pnpm@10.30.3 \
    && addgroup --system usergroup && adduser --system --no-create-home --ingroup usergroup appuser 

COPY --from=builder /app/package.json /app/pnpm-lock.yaml /app/
RUN pnpm install --prod --frozen-lockfile
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

RUN chown -R appuser:usergroup /app
USER appuser

EXPOSE 3000
CMD ["pnpm", "start"]