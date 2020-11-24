import json
import boto3
import os

sfn = boto3.client('stepfunctions', region_name='us-east-1')

def handler(event, context):
    state_machine_arn = os.getenv('STATE_MACHINE_ARN')

    print(f'SFN Trigger received event' + json.dumps(event, indent=2))

    # for the test case assume only a single message here
    msg = event['Records'][0]

    new_event = {
        'parameters': {
            'event': msg['body']
        },
        'eventSourceARN': msg['eventSourceARN']
    }

    response = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(new_event)
    )
    print(f"SFN Execution ARN {response.get('executionArn')}")
    print(f"SFN Execution Message {json.dumps(new_event, indent=2)}")
    return event
