# Build
FROM node:22-alpine AS build
RUN corepack enable
WORKDIR /repo
COPY pnpm-workspace.yaml package.json ./
COPY shared/contracts ./shared/contracts
COPY frontend ./frontend
RUN pnpm install --filter @teg/frontend... && pnpm --filter @teg/frontend build

# Serve (estáticos; el reverse-proxy debe rutear /api y /ws al backend)
FROM nginx:alpine
COPY --from=build /repo/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
