#!/bin/bash
set -euo pipefail

SECRET_NAME="watchdog/prod/env"
REGION="af-south-1"
OUTPUT_PATH="/home/ubuntu/app/.env"

aws secretsmanager get-secret-value \
	--secret-id "$SECRET_NAME" \
	--region "$REGION" \
	--query SecretString \
	--output text \
| jq -r 'to_entries[] | "\(.key)=\(.value)"' \
> "$OUTPUT_PATH"

echo "Wrote $(wc -l < "$OUTPUT_PATH") variables to $OUTPUT_PATH"