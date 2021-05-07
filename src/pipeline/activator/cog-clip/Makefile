postgres:
	docker-compose up -d

migrations:
	docker run --rm \
      --network cog-clip_default \
      quay.io/azavea/franklin:404f1c0 \
      migrate \
      --db-user franklin \
      --db-name franklin \
      --db-password franklin \
      --db-host database

# -e FRANKLIN_LOG_LEVEL=DEBUG
import-aviris-test-collection:
	docker run --rm \
      --network cog-clip_default \
      -e AWS_REGION=us-east-1 \
      -v ${PWD}/data/catalog:/opt/data/ \
      quay.io/azavea/franklin:404f1c0 \
      import-catalog \
      --db-user franklin \
      --db-name franklin \
      --db-password franklin \
      --db-host database \
      --catalog-root /opt/data/collection.json

run-franklin:
	docker run --rm \
      --network cog-clip_default \
      -p 9090:9090 \
      quay.io/azavea/franklin:404f1c0 \
      serve \
      --db-user franklin \
      --db-name franklin \
      --db-password franklin \
      --db-host database \
      --with-transactions \
      --with-tiles \
      --run-migrations

run-dev-env: postgres migrations import-aviris-test-collection run-franklin
