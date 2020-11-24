import json
import argparse

parser = argparse.ArgumentParser(description='Processor input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

def handler(event, context):
    print("Processor received event: " + json.dumps(event, indent=2))
    return event

if __name__ == "__main__":
    args = parser.parse_args()
    event = args.event[0]
    handler(event, "context")
