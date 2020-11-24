import json
import argparse
import boto3
import os

sns = boto3.client('sns', region_name='us-east-1')

parser = argparse.ArgumentParser(description='Activator input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

def handler(event, context):
    print("Activator received event: " + json.dumps(event, indent=2))
    return { 
        'message' : 'activation msg result'
    }  

if __name__ == "__main__":
    args = parser.parse_args()
    event = args.event[0]
    topic = os.getenv('SNS_TOPIC')

    # Publish a simple message to the specified SNS topic
    response = sns.publish(TopicArn=topic, Message=event)

    print("response: " + json.dumps(response, indent=2))

    handler(event, "context")