# Define global args
ARG FUNCTION_DIR="/home/app/"
ARG RUNTIME_VERSION="3.10"

# Stage 1 - bundle base image + runtime
FROM python:${RUNTIME_VERSION}-slim AS python-slim

# Update to latest version of pip
RUN pip install --upgrade pip

# Stage 2 - build function and dependencies
FROM python-slim AS build-image

# Include global args in this stage of the build
ARG FUNCTION_DIR
ARG RUNTIME_VERSION

# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Copy handler function
COPY app/* ${FUNCTION_DIR}

# Optional – Install the function's dependencies
RUN python${RUNTIME_VERSION} -m pip install -r ${FUNCTION_DIR}requirements.txt --target ${FUNCTION_DIR}

# Install Lambda Runtime Interface Client for Python
RUN python${RUNTIME_VERSION} -m pip install awslambdaric --target ${FUNCTION_DIR}

# Stage 3 - final runtime image
FROM python-slim

# Include global args in this stage of the build
ARG FUNCTION_DIR

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Add Lambda Runtime Interface Emulator
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie

# Make the necessary scripts executable
RUN chmod 755 /usr/bin/aws-lambda-rie

# Copy the entry script
COPY entry.sh /
RUN chmod 755 /entry.sh

# Create the symbolic link from /home/app/exports to /tmp/exports
RUN ln -s /tmp/exports /home/app/exports

# Create /tmp/exports directory
RUN mkdir -p /tmp/exports && chmod -R 777 /tmp/exports

# Entry point and default command
ENTRYPOINT [ "/entry.sh" ]
CMD [ "app.main_handler" ]