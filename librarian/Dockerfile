# Stage 1: Build the Knowledge Hub UI
FROM node:20-slim AS ui-build
WORKDIR /ui
COPY knowledge-hub-ui/package*.json ./
RUN npm install
COPY knowledge-hub-ui/ .
RUN npm run build

# Stage 2: Final image with Python/FastAPI
FROM python:3.11-slim
WORKDIR /app

# Install aiofiles explicitly if not in pyproject.toml
RUN pip install --no-cache-dir aiofiles

COPY librarian/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy Librarian backend
COPY librarian/ .

# Copy UI dist into the location Librarian expects (relative to its main.py)
# librarian/main.py looks for ../knowledge-hub-ui/dist
RUN mkdir -p /knowledge-hub-ui/dist
COPY --from=ui-build /ui/dist /knowledge-hub-ui/dist

# Adjust main.py to find the UI in the container path if needed, 
# or ensure the paths match the relative structure.
# In main.py: os.path.join(os.getcwd(), "..", "knowledge-hub-ui", "dist")
# If CWD is /app, then .. is /, so /knowledge-hub-ui/dist exists.

EXPOSE 8001

CMD ["python", "main.py"]
