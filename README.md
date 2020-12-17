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

See READMEs in src directories for instructions on how to run individual services in this application.

## Scripts

| Name    | Description                                                 |
|---------|-------------------------------------------------------------|
| `console` | Open a shell in the `dev` container |
| `db-console` | Open a psql shell on the `database` container |
| `infra` | Execute Terraform subcommands with remote state management. |
| `migrate` | Run database migrations |
| `server` | Start application servers, including Franklin |
| `setup` | Run project setup after checkout |
| `update` | Update project dependencies and rebuild containers |
