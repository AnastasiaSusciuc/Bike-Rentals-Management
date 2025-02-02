# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the wait_for.sh script into the container
COPY wait_for.sh /wait_for.sh

# Make the wait_for.sh script executable
RUN chmod +x /wait_for.sh

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Flask will run on
EXPOSE 5000

# Set environment variables for Flask app
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the Flask app when the container starts
#CMD ["flask", "ru\n"]
CMD ["/wait_for.sh"]
