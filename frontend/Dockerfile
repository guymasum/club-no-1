FROM node:20-slim AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Baked into the JS bundle at build time (Vite inlines import.meta.env.*).
# Railway forwards service variables as build args when declared with ARG.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM node:20-slim
WORKDIR /app
RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 4173

# `-s` serves index.html for unknown paths, required for client-side
# (react-router) routing. Railway assigns the listen port via $PORT.
CMD ["sh", "-c", "serve -s dist -l ${PORT:-4173}"]
