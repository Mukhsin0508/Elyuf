FROM python:3.12.0

# Set the working directory in the container
WORKDIR /app

# Define environment variables to prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Update pip to the latest version
RUN pip install --upgrade pip

# Keep the system up-to-date  the build tools and Clean up the apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential g++ && \
    apt-get clean \

ENV CFLAGS="-std=c++14"
ENV CXXFLAGS="-std=c++14"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --verbose

# Copy the current directory contents into the container at /app
COPY . /app

