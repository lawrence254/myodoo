# Makefile for Odoo 18.0 (Community) Development

# Ensure the PYTHONPATH is set to the Odoo directory for module imports
export PYTHONPATH := odoo

# Variables
PYTHON = ./bin/python
PIP = ./bin/pip
ODOO = $(PYTHON) odoo/odoo-bin
CONFIG = odoo.conf
ADDONS_PATH = odoo/addons,custom_addons
MODULE_NAME ?= 
DB_NAME ?= odoo_test_access

# Targets
.PHONY: help start stop restart install-requirements shell create-module

help:
	@echo "Odoo Makefile commands:"
	@echo "  make start               - Start Odoo server"
	@echo "  make stop                - Stop Odoo server (if running in background)"
	@echo "  make restart             - Restart Odoo"
	@echo "  make install-requirements - Install Python dependencies"
	@echo "  make shell               - Open Python shell with Odoo env"
	@echo "  make create-module MODULE_NAME=your_module - Create a new module"
	@echo "  make update              - Update all modules in DB ($(DB_NAME))"
	@echo "  make help                - Show this help"

install-requirements:
	$(PIP) install -r requirements.txt

start:
	@echo "Starting Odoo..."
	@( $(ODOO) -c $(CONFIG) --addons-path=$(ADDONS_PATH) > log/odoo.log 2>&1 & echo $$! > odoo.pid )
	@echo "Odoo started. Check log/odoo.log for output."

stop:
	@echo "Stopping Odoo..."
	@if [ -f odoo.pid ]; then \
		kill `cat odoo.pid` && echo "Odoo stopped." || echo "Failed to stop Odoo."; \
		rm -f odoo.pid; \
	else \
		echo "No PID file found. Odoo may not be running."; \
	fi

restart:
	@make stop
	@make start

shell:
	$(ODOO) shell -c $(CONFIG)

create-module:
	$(ODOO) scaffold $(MODULE_NAME) custom_addons/

update:
	$(ODOO) -c $(CONFIG) -d $(DB_NAME) -u all --stop-after-init

# Relic Lice key: ae6a2b7998fe25cb3b8e614d5a13b21bFFFFNRAL
#  user: NRAK-2IF5V4DA82G1NVC4YNQQHY18L6T