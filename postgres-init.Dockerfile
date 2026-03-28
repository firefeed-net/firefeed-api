# PostgreSQL initialization Dockerfile
# This Dockerfile creates a custom PostgreSQL image with extensions and initial data

FROM postgres:17-alpine

# Install additional packages if needed
RUN apk add --no-cache \
    postgresql-contrib

# Copy initialization scripts
COPY database/init.sql /docker-entrypoint-initdb.d/
COPY database/migrations.sql /docker-entrypoint-initdb.d/

# Set permissions
RUN chmod +r /docker-entrypoint-initdb.d/*.sql

# Switch to postgres user for security
USER postgres

# Expose PostgreSQL port
EXPOSE 5432

# Start PostgreSQL
CMD ["postgres"]