# Voxmetriks — root Makefile (delegates to infrastructure/)
.PHONY: help up down logs etl dev test install pipeline lint

help:
	@$(MAKE) -f infrastructure/Makefile help

up down logs etl dev test install pipeline lint:
	@$(MAKE) -f infrastructure/Makefile $@
