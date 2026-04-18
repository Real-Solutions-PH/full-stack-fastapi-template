# Stage 0, "deps", install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install --legacy-peer-deps

# Stage 1, "build-stage", build the Next.js app
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY ./frontend /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2, runtime — Next.js standalone server
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=build-stage /app/public ./public
COPY --from=build-stage --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build-stage --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
