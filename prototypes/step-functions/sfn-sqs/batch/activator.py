import json
import argparse
import boto3

parser = argparse.ArgumentParser(description='Activator input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/513167130603/processor-queue'

def handler(event, context):
    print("Activator received event: " + event)
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=event)
    print(f'response: {response}')
    return event

if __name__ == "__main__":
    args = parser.parse_args()
    event = args.event[0]
    handler(event, "context")
