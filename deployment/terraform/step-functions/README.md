## StepFunctions input message example

### Pipeline Choice

```json
{
    "tasks": ["jobActivatorAvirisL2", "jobCogClip"],
    "commands": {
        "jobActivatorAvirisL2": ["--pipeline-uri", "s3://aviris-data-dev-azavea/commands/aviris-l2/pipeline-test-s3.json"],
        "jobCogClip": ["clip-pipeline-uri", "--uri", "s3://aviris-data-dev-azavea/commands/cog-clip/pipeline-test-s3.json"]
    }
}
```