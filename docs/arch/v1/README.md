## Arch Draft v1

_The goal of this document is not to propose an architecture, but to describe an assumption that we can follow towards building it._

### Context

The goal of this project is to _develop hyperspectral imagery processing pipeline_ with the following requirements (Part 4. Phase II Work Plan, Develop Imagery Processing Pipeline):
* Develop Workflow Configuration (declarative workflow configuration)
* Develop New Scene Analysis (processing of new hyperspectral imagery as it becomes available in response to an external event)
* Develop On-Demand Analysis (on demand analysis of a desired type, analysis here is oil spill detection, tree mortality)
* Develop Publish Workflow (catalog with results)
* Record Data Provenance Metadata (record provenance metadata in the STAC items)

The intent is to have a reference architecture that is adaptable for new use cases involving imagery processing.

### Evaluation criteria / non-functional requirements

1. Input sources can vary
    - We should be able to work not only with a single source of data
2. Products can vary (oil spill, tree mortality) and can use different sources
    - We should not be attached to any single selected use case (no matter what it is), it is important to build up the system a way that it is not attached to single product
3. Processing of large volumes of data
    - Should be able to work with relatively large inputs (each AVIRIS input is more than of 8Gb size)
4. Scalability
    - We don't expect that system would be in a constant use and the static cost (cost of a system that does not function) should be minimized
5. Flexible asynchronous ad-hoc components invocation that doesn't necessarily mean scheduling (i.e. it should be possible to re-use individual components), components independence
    - Components independence reduces complexity of development and should allow to recombine components in somewhat order that increases the reusability of the system
6. There should be mechanisms to introspect and debug failures within the pipeline
    - In addition to low start times, there should be a set of tools to start investigating possible issues
7. Low startup times
    - Should be easy enough to start diagnosing the issue and to have a simple development cycle
8. Heterogeneous execution environment
    - Implementation of components is not limited to a single language

#### Background

Originally, GeoTrellis (v1.0.0+) was mostly designed 
towards batch processing and towards large jobs on scale. Scaling was achieved via Spark and its inbuilt functionality to distribute 
data and tasks across the allocated cluster. Unfortunately, such an approach required maintaining an allocated cluster or raising an on demand cluster to process the entire (large) dataset as a single batch. It turns out that a more regular use case for companies (Planet, Sentinel Hub) is an on demand preprocessing and processing.

[Back in 2016](https://github.com/locationtech/geotrellis/pull/1936) we have already tried to refactor the GeoTrellis ingest process and make it more iterative, since there was a client interest in ingesting large datasets by portions. That was not a successful experience though.

The current FFDA project also represents an on demand processing flow where the processing (imagery download + predictions) happens  based on the input task grid. With the help of the Raster Vision Command it is possible to schedule and launch such jobs on AWS Batch. It addresses Spark issues related to on demand processing and made it easier to maintain, however it adds some extra complexities to deploy, launch and debugging of such jobs - the project has long startup times and it only complicates debugging.

We had a Farmers Edge contract where they experienced issues with maintaining the (AWS) Batch like environment, experiencing issues with throughput, and difficulties during the new features development and deployment (development requires quick enough feedback from jobs, which is not possible with Batch). The task was to implement a Spark streaming consumer that would process rasters basing on the input messages on demand, and deliver results into STAC and AzureFS. That was _a successful_ integration into their system that processes now 9000 Orthotiles a day and were over 800k products per hour created (products here is a cropped / resampled input + cloud removal (ML) + the actual product computation (i.e. NDVI, PCA)). However, this architecture had issues with scalability and required to have a constantly launched cluster. It is unknown would this case fit our needs or not.

### Use case diagrams

Given the background above it is possible to describe a general use case that would cover it.

<img width="400" alt="Arch Streams" src="img/arch_streams.dot.png">

#### Legend

* STAC API: rest service that implements STAC Api Spec (in this case it would be Franklin).
* Module: messages consumer
* Stream: a "stream" of messages that modules would consume (in other words modules are stream consumers); it can be not a "stream", but some service that produces messages
* Activator: module that preprocesses data
* Processor: module that produces _products_ (i.e. oil spill, tree mortality) from the preprocessed data

### A flow diagram

<img width="600" alt="Arch No Supervisor" src="img/arch_no_supervisor.dot.png">

#### STAC API

During the pipeline execution there would be a need to store input and output metadata. At this point, it is already a selected option and is one of the proposal requirements. Franklin implements STAC API Spec that fully covers our usecase.

#### Activator

Activator is a module that is responsible for preprocessing of the input raw (i.e. AVRIS, Planet) files. AVRIS is stored on FTP encoded into archives and definitely of these purposes there is a need in a preprocessing step.

1. It accepts the activation message (that can be i.e. AVRIS STAC item id with some extra metadata).
2. Queries STAC API and retrieves RAW Items from the catalog based on the message parameters. It can also skip doing anything in case the preprocessed result is already in the catalog.
3. Runs preprocessing which can be downloading of necessary assets from the AVRIS FTP, converting it into an appropriate format (i.e. TIFF) if necessary.
4. Uploads the "Preprocessed output" on S3.
5. Generates the corresponding metadata that would be added into the STAC Catalog through the STAC API.
6. Sends the result message back into the stream. This can be only an alert message or it can send message directly to the next (product) module.

#### Processor

Processor is a module that is responsible for the actual product generation. Product here is the result of applying HSI tooling and is any derivative that is build from the input Activated data.

1. It accepts the product processing message (i.e. product name, input preprocessed scene ids).
2. Queries STAC API and retrieves PreProcessed Items from the catalog basing on the message parameters. It can also skip doing anything in case the result product is already in the catalog.
3. Applies necessary transformations to the corresponding preprocessed data (i.e. AVRIS preprocessed scenes).
4. Uploads all results on S3.
5. Generates the corresponding metadata that would be added into the STAC Catalog through the STAC API.
6. Sends the result message back into the stream. This can be only an alert message or it can send a message directly to the next (product) module.

#### A flow diagram with supervisor

<img width="800" alt="Arch No Supervisor" src="img/arch_supervisor.dot.png">

The reasonable question is should there be some supervisor that schedules the input user messages and sends messages into an appropriate queue. Supervisor is intentionally moved out of this diagram and it is probably on the application level and not a first citizen of this streaming application itself.

### Conclusion

We are not clear yet what technologies to use and what architecture to implement. The next step would be to map the architecture assumption to the existing set of tools to prevent us from the unnecessary wheel reinvention within the given set of constraints.

### Next steps

* **Mock up the architecture and the pipeline execution**
  * Using [AWS Step functions](https://github.com/azavea/nasa-hyperspectral/issues/28) and [Nextflow](https://github.com/azavea/nasa-hyperspectral/issues/17)
* **MVP**
  * Build some working prototype with activator and processor
  * The goal is to look at how viable the proposed architecture would be, what are the issues
  * Determine how modules can interact or should they interact with each other
