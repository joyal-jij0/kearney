# Frontend Dockerfile using Bun
FROM oven/bun:1-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Development stage
FROM base AS development
EXPOSE 3000
CMD ["bun", "--hot", "src/index.tsx"]

# Build stage
FROM base AS builder
RUN bun run build

# Production stage
FROM oven/bun:1-alpine AS production
WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

EXPOSE 3000
CMD ["bun", "run", "start"]
