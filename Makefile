AWS_PROFILE ?= kabadi-setu
export AWS_PROFILE

LAMBDA_SRC := .build/lambda
PYTHON := .venv/bin/python
SAM := $(if $(wildcard .tools-venv/bin/sam),.tools-venv/bin/sam,sam)
export SAM_CLI_TELEMETRY := 0
export __SAM_CLI_APP_DIR := $(CURDIR)/.local/sam

.PHONY: package build deploy preflight secret local-db test

# Copy only what the Lambda needs, keeping the backend/data/policies layout the code expects.
package:
	rm -rf $(LAMBDA_SRC) && mkdir -p $(LAMBDA_SRC)
	cp -R backend data policies $(LAMBDA_SRC)/
	cp backend/requirements.txt $(LAMBDA_SRC)/requirements.txt
	find $(LAMBDA_SRC) -name __pycache__ -prune -exec rm -rf {} +

build: package
	$(SAM) build

preflight:
	$(PYTHON) scripts/aws_identity.py

deploy: preflight build
	$(SAM) deploy

# One-time: store the pickup-link secret in SSM Parameter Store, never in the template or repo.
secret:
	$(PYTHON) scripts/create_secret.py

local-db:
	docker start kabadi-setu-dynamodb 2>/dev/null || docker run -d --name kabadi-setu-dynamodb -p 127.0.0.1:8000:8000 amazon/dynamodb-local:latest
	$(PYTHON) scripts/create_local_table.py

test:
	$(PYTHON) -m pytest -q
