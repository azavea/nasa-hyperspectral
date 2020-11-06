import json

def handler(event, context):
    print("Processor received event: " + json.dumps(event, indent=2))
    return event
