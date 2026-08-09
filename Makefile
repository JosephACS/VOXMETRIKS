# Voxmetriks — root Makefile (delegates to infrastructure/)
.PHONY: help up down logs etl dev test install pipeline lint airflow-up airflow-down airflow-logs airflow-list airflow-trigger

help:
	@$(MAKE) -f infrastructure/Makefile help

up down logs etl dev test install pipeline lint airflow-up airflow-down airflow-logs airflow-list airflow-trigger:
	@$(MAKE) -f infrastructure/Makefile $@
