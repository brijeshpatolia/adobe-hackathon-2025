# Stage 1: Use an official Python runtime as a parent image
# Using python:3.9-slim is a good balance of size and functionality.
# --platform=linux/amd64 ensures it's built for the required architecture.
FROM --platform=linux/amd64 python:3.9-slim

# Stage 2: Set the working directory in the container
WORKDIR /app

# Stage 3: Copy the requirements file and install dependencies
# This is done in a separate step to leverage Docker's layer caching.
# Dependencies won't be reinstalled unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 4: Copy the rest of your application's code
# This copies main.py and the entire src folder into the container.
COPY . .

# Stage 5: Specify the command to run on container startup
# This executes your main script.
CMD ["python", "main.py"]