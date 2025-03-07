# Use an official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the project files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*
RUN apt update && apt install redis-tools -y


# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port for Django
EXPOSE 8000

# Start the Django server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ocpp_server.wsgi:application"]
