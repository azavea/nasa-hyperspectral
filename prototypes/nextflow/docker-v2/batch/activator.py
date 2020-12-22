import json
import argparse
import os

parser = argparse.ArgumentParser(description='Activator input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

def handler(event, context):
    print(f"Activator received event: {event}")

    # record the job execution result into a file
    with open('activator_event.json', 'w') as f:
        json.dump(json.loads(event), f, ensure_ascii=False)
    
    return event

if __name__ == "__main__":
    args = parser.parse_args()
    event = args.event[0]
    handler(event, "context")
