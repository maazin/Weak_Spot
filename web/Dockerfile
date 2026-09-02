# Two targets. `dev` is what docker compose runs locally and keeps hot reload.
# `production` builds the static bundle and serves it, which is what a container
# deploy needs. The default target is production, so a plain `docker build` here
# cannot accidentally ship a Vite dev server to the internet.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# --------------------------------------------------------------------- dev
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --------------------------------------------------------- production build
FROM deps AS build
COPY . .
# Baked in at build time, because Vite inlines it into the bundle. The deploy has
# to pass it as a build argument rather than a runtime variable.
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
