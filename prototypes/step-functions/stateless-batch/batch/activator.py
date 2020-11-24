import json
import argparse
import boto3
import os

parser = argparse.ArgumentParser(description='Activator input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

sns = boto3.client('sns', region_name='us-east-1')

topic = os.getenv('SNS_TOPIC')

def handler(event, context):
    print("Activator received event: " + json.dumps(event, indent=2))
    response = sns.publish(TopicArn=topic, Message=json.dumps(event))
    print(f'response: {response}')
    return event

if __name__ == "__main__":
    args = parser.parse_args()
    event = args.event[0]
    handler(event, "context")
