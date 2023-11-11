# Use an official Python runtime as a parent image
FROM python:3.10.3

# Set the working directory to /app
WORKDIR /app

# Copy just the requirements.txt first to leverage Docker cache
COPY requirements.txt ./requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ ./
COPY gunicorn.conf.py ./gunicorn.conf.py

# Command to run on container start
CMD ["gunicorn", "--config", "gunicorn.conf.py", "FreewifiBot:app"]
