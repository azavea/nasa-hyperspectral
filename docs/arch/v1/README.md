## Arch Draft v1

_The goal of this document is not to propose an architecture, but to describe an assumption that we can follow towards bulding it. In the end of this document you can find a bit premature diagram that we can try to achieve. It may be the case that it is not viable._

### Context

The goal of this project is to _develop hyperspectral imagery processing pipeline_ with the following requirements (Part 4. Phase II Work Plan, Develop Imagery Processing Pipeline):
* Develop Workflow Configuration (declarative workflow configuration)
* Develop New Scene Analysis (processing of new hyperspectral imagery as it becomes available in response to an external event)
* Develop On-Demand Analysis (on demand analysis of a desired type, analysis here is oil spill detetion, tree mortality)
* Develop Publish Workflow (catalog with results)
* Record Data Provenance Metadata (record provenance metadata in the STAC items)

#### Assumptions

1. Input sources can vary (the system should not be tight to a single source)
2. Products can vary (oil spill, tree mortality) and can use different sources
3. Modules should be scalable on demand
4. Target both constant messages stream and non constant messages stream
5. Flexible ad-hoc modules invocation that doesn't neccesarily mean scheduling (i.e. it should be possible to re-use individual modules)
6. Developer receives feedback that new job types have started successfully within a few minutes

##### Modules and sources assumptions

* At least preprocessing (activation) and processing modules should exist
* AVIRIS Source is the only available dataset at this point

#### More Context

Originally, GeoTrellis (v1.0.0+) was mostly designed 
towards batch processing and towards large jobs on scale. Scaling was achieved via Spark and its inbuilt functionality to distribute 
data and tasks across the allocated cluster. Unfortunately, such approach required maintaining an allocated cluster or rising an on demand cluster to process the entire (large) dataset as a single batch. It turned out, that a more regular usecase for companies (Planet, Sentinel Hub) is an on demand preprocessing and processing.

[Back in 2016](https://github.com/locationtech/geotrellis/pull/1936) we have already tried to refactor the GeoTrellis ingest process and make it more iterative, since there was a client interset in ingesting large datasets by portions. That was a not succesfull experience though.

The current FFDA project also represents an on demand processing flow where the processing (imagery download + predictions) happens basing on the input task grid. With the help of the Raster Vision Command it is possible to schedule and lunch such jobs on AWS Batch. It addresses Spark issues related to on demand processing and made it easier to maintain, however it adds some extra complexities to deploy, submit and lunch of such jobs.

We had a Farmers Edge contract where they experienced issues with maintaining the (AWS) Batch like environment, experiencing issues with throughput, and difficulties during the new features development and deployment (development requires a quick enough feedback from the jobs, which is not possible with Batch). The task was to implement a Spark streaming consumer that would process rasters basing on the input messages on demand, and deliver results into STAC and AzureFS. That was _a succesfull_ integration into their system that processes now 9000 Orthotiles a day and were over 800k products per hour created (products here is a cropped / resampled input + cloud removal (ML) + the actual peoduct computation (i.e. NDVI, PCA)).

#### Options

1. To follow the known path, and to build a system similar to FFDA (not in terms of the raster vision usage but in terms of using known stack of technologies). That would require non trivial, but exsiting instruments interaction and it would be another but similar to existing projects with its benefits and issues. However, it can be challenging to satisfy assumptions 4, 5, 6.

2. To build an event driven processing pipeline which does not exsit yet. All the usecases above can be generalized and consolidated. The general idea is to build a composable and simple at the same time system that would consist of independent (or weakly dependent) modules. Modules itself can be written in any languages and communication between modules can be provided only through the messages stream. Each module can only process the input message if possible and in this model there is no "branching". Each module listens to its own topic and processes or tries to process all messages.

The second option is described in more details in the sections below.

### Decision and evaluation criteria

* There should be mechanisms to introspect and debug failures within the pipeline
* The messages exchange between the execution steps should be robust enough

### Next steps

The next step would be to map the architecture assumption to the exsiting set of tools and to prevent us from unnecessary wheel reinvention within the given set of constraints.

* **Mock up the architecture and the pipeline execution**
  * AWS Step functions, airflow, nextflow
  * AWS Batch or K8S
* **Stream selection (if necessary)**
  * Kafka, SQS, Pulsar
* **MVP**
  * Build some working prototype with activator and processor
  * The goal is to look at how viable the proposed architure would be, what are the issues
  * Determine how modules can interact or should they interact with each other
* **Consumers abstraction**
  * In the proposed architecture it is not clea how the processor should be implemented
  * It is possible to implement a generic consumer that would be responsible for the application



### The general view, streams, modules, metadata

Even though this diagram may seem to align more with option 2, it doesn't necessarily mean that.

<img width="400" alt="Arch Streams" src="img/arch_streams.dot.png">

#### Legend
* STAC API: rest service that implements stac api spec (in this case it would be Franklin).
* Module: messages consumer
* Stream: a stream of messages that modules would consume (in other words modules are stream consumers)
* Activator: module that preprocesses data
* Processor: module that produces _products_ (i.e. oil spill, tree mortality) from the preprocessed data

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
