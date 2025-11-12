.PHONY: help build up down restart logs clean test

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construye las imágenes Docker
	docker-compose build

up: ## Inicia los servicios
	docker-compose up -d

down: ## Detiene los servicios
	docker-compose down

restart: ## Reinicia los servicios
	docker-compose restart

logs: ## Muestra los logs
	docker-compose logs -f

logs-api: ## Muestra logs del API
	docker-compose logs -f backend

logs-worker: ## Muestra logs del worker
	docker-compose logs -f worker

logs-db: ## Muestra logs de la base de datos
	docker-compose logs -f db

shell-api: ## Abre shell en el contenedor del API
	docker-compose exec backend /bin/bash

shell-worker: ## Abre shell en el contenedor del worker
	docker-compose exec worker /bin/bash

shell-db: ## Abre shell en PostgreSQL
	docker-compose exec db psql -U pdfuser -d pdfdb

clean: ## Limpia contenedores, volúmenes e imágenes
	docker-compose down -v
	docker system prune -f

clean-storage: ## Limpia archivos de storage
	rm -rf storage/input/*
	rm -rf storage/output/*

dev: ## Inicia en modo desarrollo
	docker-compose up

prod: build up ## Inicia en modo producción

status: ## Muestra el estado de los servicios
	docker-compose ps

test: ## Ejecuta tests (implementar según necesidad)
	@echo "Tests no implementados aún"
