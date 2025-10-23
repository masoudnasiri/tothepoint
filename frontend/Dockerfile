FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code (excluding node_modules via .dockerignore)
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
