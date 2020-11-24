import json
import argparse
import boto3
import os

sns = boto3.client('sns', region_name='us-east-1')
batch = boto3.client('batch', region_name='us-east-1')

def handler(event, context):
    topic = os.getenv('SNS_TOPIC')
    jobDefinition = os.getenv('JOB_DEFINITION')
    print("Activator received event: " + json.dumps(event, indent=2))
    print(f"Sending message to topic {topic}")
    
    # response = sns.publish(TopicArn=topic, Message=json.dumps(event))
    # print("response: " + json.dumps(response, indent=2))

    response_batch = batch.submit_job(
        jobName='ActivatorBatchJob',
        jobQueue='tf-test-batch-job-queue',
        jobDefinition='tf_test_activator_batch_job_definition:9',
        containerOverrides={'vcpus': 1},
        parameters={ "event": "{ 'msg': 'default-test' }" }
    )

    print("Job ID is {}.".format(response_batch['jobId']))

    return event
