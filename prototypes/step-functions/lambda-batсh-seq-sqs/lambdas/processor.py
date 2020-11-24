import json
import boto3

sqs = boto3.client('sqs', region_name='us-east-1')

def handler(event, context):
    print("Processor received event: " + json.dumps(event, indent=2))

    queue_url = f'https://sqs.us-east-1.amazonaws.com/513167130603/processor-queue'

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['SentTimestamp'],
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    print('Response: ' + json.dumps(response, indent=2))

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print('Received and deleted message: %s' % message)

    return message
