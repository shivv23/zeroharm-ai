ARG REACT_APP_WS_URL=ws://localhost:8000/ws
ARG REACT_APP_API_URL=http://localhost:8000/api

FROM node:20-alpine AS build
ARG REACT_APP_WS_URL
ARG REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
