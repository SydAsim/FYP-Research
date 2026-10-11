FROM node:24.14.1-alpine
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile --fetch-timeout 600000 --fetch-retries 5
COPY apps/web ./apps/web
RUN pnpm --dir apps/web build
EXPOSE 3000
