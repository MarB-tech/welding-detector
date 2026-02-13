# --- Dockerfile for Frontend Vue ---
FROM node:20-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the code
COPY . .

# Set environment variable for host communication
ENV DOCKER_ENV=true

# Port for Vite dev server
EXPOSE 3000

# Run dev server (accessible from outside)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
