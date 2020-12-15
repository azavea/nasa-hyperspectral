# NASA SBIR - Hyperspectral Imagery Processing

An event-driven image processing pipeline for developing our foundational capability to work with HSI data sources.

- [STAC Catalogs](#stac-catalogs)
- [Scripts](#scripts)

## Requirements

- Docker
- Docker Compose

## Setup

Run `./scripts/setup`.

## Development

Run the local Franklin instance with `./scripts/server`. It is available at http://localhost:9090.

Build and ingest the AVIRIS catalog into Franklin with `./scripts/catalogs-aviris`. The [catalogs README](./catalogs/README.md) has more information.

Run the AVIRIS L2 activator in dev mode with `./scripts/run-activiator-l2-aviris`

## Scripts

| Name    | Description                                                 |
|---------|-------------------------------------------------------------|
| `catalogs-aviris` | Generate a STAC Catalog for AVIRIS data |
| `console` | Open a shell in the `dev` container |
| `db-console` | Open a psql shell on the `database` container |
| `infra` | Execute Terraform subcommands with remote state management. |
| `migrate` | Run database migrations |
| `run-activator-aviris-l2` | Run the AVIRIS L2 Activator in the development environment |
| `server` | Start application servers, including Franklin |
| `setup` | Run project setup after checkout |
| `update` | Update project dependencies and rebuild containers |
