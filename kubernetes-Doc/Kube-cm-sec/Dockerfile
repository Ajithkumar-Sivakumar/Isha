# Use a lightweight Python base image for the container.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy the dependency list into the image.
COPY requirements.txt ./

# Install the Python packages required by the app.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the image.
COPY app.py ./

# Expose port 8080 for the Flask service.
EXPOSE 8080

# Start the app when the container launches.
CMD ["python", "app.py"]
