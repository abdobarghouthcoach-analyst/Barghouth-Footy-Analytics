FROM node:lts

WORKDIR /usr/src/app

# Install dependencies first (cacheable)
COPY package*.json ./
RUN npm install

# Copy source (will be overridden by a bind mount in development)
COPY . .

ENV NODE_ENV=development
ENV VITE_API_BASE_URL=http://localhost:8000/api/v1

EXPOSE 5173

CMD ["npm", "run", "dev"]
