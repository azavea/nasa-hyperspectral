# NASA SBIR — Hyperspectral Imagery Processing

An event-driven image processing pipeline for developing our foundational
capability to work with HSI data sources.

- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Scripts](#scripts)

## Requirements

- [Docker Engine](https://docs.docker.com/install/) 19.03+
- [Docker Compose](https://docs.docker.com/compose/install/) 1.27+

## Getting Started

The following script will provision the development environment.

```bash
$ ./scripts/setup
```

Then, you can bring up the local Franklin instance, which will be accessible at
http://localhost:9090.


```bash
$ ./scripts/server
```

See READMEs in the `src/` directories for instructions on how to run individual
services in this application.

## Scripts

| Name         | Description                                                                        |
|--------------|------------------------------------------------------------------------------------|
| `cibuild`    | Build application for staging or a release.                                        |
| `cipublish`  | Publish container images to Elastic Container Registry (ECR).                      |
| `console`    | Run an interactive shell or command inside an application container.               |
| `db-console` | Enter a database shell.                                                            |
| `infra`      | Execute Terraform subcommands with remote state management.                        |
| `migrate`    | Run database migrations.                                                           |
| `server`     | Start application servers, including Franklin.                                     |
| `setup`      | Set up the project's development environment.                                      |
| `update`     | Update project runtime dependencies (e.g. run migrations, build container images). |
