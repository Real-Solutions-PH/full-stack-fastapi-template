# Stage 0, "build-stage", install deps and build the Next.js app with bun
FROM oven/bun:1-alpine AS build-stage
WORKDIR /app

COPY package.json bun.lock /app/
COPY frontend/package.json /app/frontend/
RUN bun install --frozen-lockfile

COPY ./frontend /app/frontend

WORKDIR /app/frontend
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

# Stage 1, runtime — Next.js standalone server
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=build-stage /app/frontend/public ./frontend/public
COPY --from=build-stage --chown=nextjs:nodejs /app/frontend/.next/standalone ./
COPY --from=build-stage --chown=nextjs:nodejs /app/frontend/.next/static ./frontend/.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "frontend/server.js"]
