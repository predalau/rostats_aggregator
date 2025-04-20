# Start from a base image
FROM python:3.10-slim

# Set working directory
WORKDIR ~/preda_apps/rostats_aggregator/

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set python path
ENV PYTHONPATH="${PYTHONPATH}:~/preda_apps/rostats_aggregator/src"

# Command to run the application
CMD ["python", "src/run.py"]





