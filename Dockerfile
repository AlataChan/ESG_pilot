# 1. Use an official Python runtime as a parent image (full version with build tools)
FROM python:3.12

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 4. Copy the entire backend application code into the container
COPY ./backend /app

# 5. Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. Define the command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]