## Arch Draft v1

This document is not attached to any existing technologies

### The general view, streams, modules, metadata

<img width="400" alt="Arch Streams" src="img/arch_streams.dot.png">

#### Legend
* STAC API: rest service that implements stac api spec (in this case it would be Franklin).
* Stream: a stream of messages that modules would consume (in other words modules are stream consumers)
* Activator: module that preprocesses data
* Processor: module that produces _products_ (i.e. oil spill, tree mortality) from the preprocessed data

##### Description

The general idea is to build a composable and simple at the same time system that would consist of independent (or weakly dependent) modules. Modules itself can be written in any languages and communication between modules is provided only through the messages stream. Each module can only process the input message if possible and in this model there is no "branching". Each module listens to its own topic and processes or tries to process all messages.

### A more detailed view, a flow diagram

<img width="600" alt="Arch No Supervisor" src="img/arch_no_supervisor.dot.png">

#### Activator

Activator is a module that is responsible for preprocessing of the input raw (i.e. AVRIS) files.

1. It accepts the activation message (that can be i.e. AVRIS STAC item id with some extra metadata).
2. Queries STAC API and retrieves RAW Items from the catalog basing on the message parameters. It can also skip doing anything in case the preprocessed result is already in the catalog.
3. Runs preprocessing which can be downloading of neccesary assets from the AVRIS FTP, converting it into an appropriate format (i.e. TIFF) if neccesary.
4. Uploads the "Preprocessed output" on S3.
5. Generates the corresponding metadata that would be added into the STAC Catalog through the STAC API.
6. Sends the result message back into the stream. This can be only an alert message or it can send message directly into the next (product) module queue.

#### Processor

Processor is a module that is responsible for the actual product generation. Product here is the result of applying HSI tooling and is any derivative that is build from the input Activated data.

1. It accepts the product processing message (i.e. product name, input preprocessed scene ids).
2. Queries STAC API and retrieves PreProcessed Items from the catalog basing on the message parameters. It can also skip doing anything in case the result product is already in the catalog.
3. Applies neccesary transofrmations to the corresponding preprocessed data (i.e. AVRIS preprocessed scenes).
4. Uploads all result on S3.
5. Generates the corresponding metadata that would be added into the STAC Catalog through the STAC API.
6. Sends the result message back into the stream. This can be only an alert message or it can send message directly into the next (product) module queue.

#### A more detailed view, a flow diagram (with supervisor)

<img width="800" alt="Arch No Supervisor" src="img/arch_supervisor.dot.png">

The reasonable question is should there be some supervisor that schedules the input user messages and sends messages into an appropriate queue. Supervisor is intentionally moved out of this diagram and it is probably on the application level and not a first citizen of this streaming application itself.

### Next steps

The next step would be to map the described high level diagram to the exsiting set of tools.

* Architecture and execution, what tools should be used to describe the diagram and to execute it
  * AWS Step function, airflow, nextflow
  * AWS Batch or K8S
* Stream selection
  * Kafka, SQS, Pulsar
* MVP
  * Build some working prototype with activator and processor
  * The goal is to look at how viable the proposed architure would be, what are the issues
  * Determine how modules can interact or should they interact with each other
* Consumers abstraction
  * In the proposed architecture it is not clea how the processor should be implemented
  * It is possible to implement a generic consumer that would be responsible for the application
