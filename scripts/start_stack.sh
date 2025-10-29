#!/usr/bin/env bash

# Simple helper to launch the full KeneyApp stack via Docker Compose.
# Usage:
#   ./scripts/start_stack.sh           # build + start services
#   ./scripts/start_stack.sh --logs    # start services and stream logs
#   ./scripts/start_stack.sh --down    # stop and remove services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "docker-compose.yml not found in ${PROJECT_ROOT}."
  exit 1
fi

# Detect docker compose command
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo "Docker Compose is required but was not found."
  exit 1
fi

ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
if [[ ! -f "${ENV_FILE}" && -f "${ENV_EXAMPLE}" ]]; then
  echo "No .env file detected. Copying from .env.example..."
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
fi

ACTION="${1:-up}"

case "${ACTION}" in
  up)
    shift || true
    echo "Starting KeneyApp stack (this may take a minute)..."
    ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" up -d --build "$@"

    echo "Waiting for backend service to accept connections..."
    ATTEMPTS=0
    MAX_ATTEMPTS=12
    until ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" exec -T backend curl -sf http://localhost:8000/health >/dev/null 2>&1; do
      ATTEMPTS=$((ATTEMPTS + 1))
      if [[ ${ATTEMPTS} -ge ${MAX_ATTEMPTS} ]]; then
        echo "Backend not responding after $((ATTEMPTS * 5)) seconds. Continuing anyway."
        break
      fi
      sleep 5
    done

    echo "Initializing database (idempotent)..."
    if ! ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" exec -T backend python -m scripts.init_db >/dev/null 2>&1; then
      echo "First initialization attempt failed, retrying shortly..."
      sleep 5
      ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" exec -T backend python -m scripts.init_db || true
    fi

    echo
    echo "Services are coming up. Useful endpoints once healthy:"
    echo "  Backend API:        http://localhost:8000"
    echo "  API docs (Swagger): http://localhost:8000/api/v1/docs"
    echo "  Frontend UI:        http://localhost:3000"
    echo "  Flower (Celery):    http://localhost:5555"
    echo
    echo "Run './scripts/start_stack.sh --logs' to follow container logs."
    ;;
  --logs)
    echo "Tailing Docker Compose logs (press Ctrl+C to stop)..."
    ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" logs -f
    ;;
  --down)
    echo "Stopping and removing KeneyApp services..."
    ${DOCKER_COMPOSE} -f "${COMPOSE_FILE}" down
    ;;
  *)
    echo "Unknown option: ${ACTION}"
    echo "Usage:"
    echo "  ./scripts/start_stack.sh           # build + start services"
    echo "  ./scripts/start_stack.sh --logs    # stream logs"
    echo "  ./scripts/start_stack.sh --down    # stop services"
    exit 1
    ;;
esac
