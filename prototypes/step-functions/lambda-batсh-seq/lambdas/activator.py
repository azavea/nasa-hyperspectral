import json
import argparse

parser = argparse.ArgumentParser(description='Activator input parse.')
parser.add_argument('event', metavar='event', type=str, nargs='+', help='passed event')

def handler(event, context):
    print("Activator received event: " + json.dumps(event, indent=2))
    return { 
        'message' : 'activation msg result'
    }  

if __name__ == "__main__":
    args = parser.parse_args()
    handler(args.event[0], "context")