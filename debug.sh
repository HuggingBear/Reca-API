#!/usr/bin/env bash

export ENVIRONMENT=development

source ./.env
export REKA_TOKEN=$REKA_TOKEN
export REKA_USER=$REKA_USER
export REKA_PASS=$REKA_PASS

python ./src/main.py