# Use a Python 3.11 base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application and HTML template
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the Flask application
CMD ["python", "app.py"]