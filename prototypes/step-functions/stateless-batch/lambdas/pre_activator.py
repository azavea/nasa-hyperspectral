import json
import argparse
import boto3
import os

sns = boto3.client('sns', region_name='us-east-1')

def handler(event, context):
    topic = os.getenv('SNS_TOPIC')
    print("Activator received event: " + json.dumps(event, indent=2))
    
    response = sns.publish(TopicArn=topic, Message=json.dumps(event))
    print("response: " + json.dumps(response, indent=2))

    return event
