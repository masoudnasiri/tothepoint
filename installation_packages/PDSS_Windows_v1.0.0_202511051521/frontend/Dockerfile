FROM node:18-alpine

WORKDIR /app

# Build-time API URL (used by CRA when building)
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code (excluding node_modules via .dockerignore)
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
