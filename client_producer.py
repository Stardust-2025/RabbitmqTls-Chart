import datetime
import time
import pika
import requests
import sys
import json
import ssl

client_id = "rabbitmq"
client_secret = "lxBLCs6z8nDsHwrnferx7uYXZ28wQo4w"

print('Using client ID:', client_id, flush=True)

# Fetch OAuth2 token from Keycloak
def get_access_token():
    response = requests.post(
        "https://aa2e5455e8e9c4dfca016e71cedc50c5-789763159.il-central-1.elb.amazonaws.com/realms/rabbitmq2/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=False  # only for self-signed certs!
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Create a new pika connection using bearer token
class OAuth2PlainCredentials(pika.credentials.PlainCredentials):
    def __init__(self, token):
        # Use token as password, username is ignored (empty string)
        super().__init__('token', token)

# --- Connect with SSL ---
def connect():
    token = get_access_token()
    creds = OAuth2PlainCredentials(token)

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    ssl_options = pika.SSLOptions(context, "a462f468f5a3b46648e4174273c54c54-232980629.il-central-1.elb.amazonaws.com")
    print('creds', creds)

    parameters = pika.ConnectionParameters(
        host="a462f468f5a3b46648e4174273c54c54-232980629.il-central-1.elb.amazonaws.com",
        port=5671,
        virtual_host="/",
        credentials=creds,
        ssl_options=ssl_options
    )
    return pika.BlockingConnection(parameters)

connection = connect()
channel = connection.channel()

queue_name = "keycloak-1"
channel.queue_declare(queue=queue_name, durable=True, arguments={"x-queue-type": "quorum"})

_COUNT_ = 10
last_update = datetime.datetime.now()

for i in range(_COUNT_):
    message = f"MyMessage {i}"
    print("Sending:", message, flush=True)

    # Refresh token every ~55 seconds if needed
    if (datetime.datetime.now() - last_update).total_seconds() > 55:
        print("Refreshing token...", flush=True)
        last_update = datetime.datetime.now()
        connection = connect()
        channel = connection.channel()

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps({"msg": message}),
        properties=pika.BasicProperties(content_type="application/json")
    )
    time.sleep(2)

connection.close()
