# Build stage
FROM node:20-slim as builder

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Set environment variables
ENV PORT=3000

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /usr/share/nginx/html

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT} || exit 1

# Expose port
EXPOSE ${PORT}

# Use non-root user for nginx
USER nginx

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 