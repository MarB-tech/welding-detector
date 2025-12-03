# --- Dockerfile dla Frontend Vue ---
FROM node:20-alpine

WORKDIR /app

# Kopiuj package.json i zainstaluj dependencies
COPY package*.json ./
RUN npm install

# Kopiuj resztę kodu
COPY . .

# Port dla Vite dev server
EXPOSE 3000

# Uruchom dev server (dostępny z zewnątrz)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
