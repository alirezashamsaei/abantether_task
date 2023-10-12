# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE abanex.settings 
# Create and set the working directory in the container
RUN mkdir /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Install Gunicorn
RUN pip install gunicorn

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Start Gunicorn to run the Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "abanex.wsgi:application"]
