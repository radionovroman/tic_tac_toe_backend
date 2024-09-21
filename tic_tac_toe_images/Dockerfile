# Use the official Python image from the Docker Hub
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8000 to the outside world
EXPOSE 8000

# Run the application
CMD ["gunicorn", "tic_tac_toe_images.wsgi:application", "--bind", "0.0.0.0:8000"]
