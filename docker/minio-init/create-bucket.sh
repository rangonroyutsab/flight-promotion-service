#!/bin/sh
set -e

echo "Waiting for MinIO..."
until mc alias set myminio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}; do
  sleep 5
done

echo "Creating bucket ${MINIO_BUCKET} if it does not exist..."
if ! mc ls myminio/${MINIO_BUCKET} > /dev/null 2>&1; then
  mc mb myminio/${MINIO_BUCKET}
  echo "Bucket ${MINIO_BUCKET} created."
else
  echo "Bucket ${MINIO_BUCKET} already exists."
fi

echo "MinIO initialization complete."
