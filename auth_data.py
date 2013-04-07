import os
if not os.path.exists('auth_data.json'):
    consumer_key = os.environ.get('consumer_key')
    consumer_secret = os.environ.get('consumer_secret')
else:
    with open('auth_data.json') as fh:
        import json
        data = json.load(fh)
        consumer_key = data['consumer_key']
        consumer_secret = data['consumer_secret']

