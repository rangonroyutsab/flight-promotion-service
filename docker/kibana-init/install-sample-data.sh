#!/bin/sh
set -e

echo "Waiting for Kibana to be available..."
until curl -s -f http://kibana:5601/api/status > /dev/null; do
  sleep 5
done

echo "Installing Kibana sample flight data..."
curl -X POST "http://kibana:5601/api/sample_data/flights" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json"

echo "Sample data initialization complete."
