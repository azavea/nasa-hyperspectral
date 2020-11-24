import json

def handler(event, context):
    print("Activator received event: " + json.dumps(event, indent=2))
    return { 
        'message' : 'activation msg result'
    }  