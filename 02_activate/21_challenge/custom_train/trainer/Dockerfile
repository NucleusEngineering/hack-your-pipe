FROM gcr.io/deeplearning-platform-release/sklearn-cpu.0-23
WORKDIR /

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copies the trainer code to the docker image.
COPY / /trainer
COPY . ./

# Install production dependencies.
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Sets up the entry point to invoke the trainer.
CMD ["python", "trainer/main.py"]