import asyncio
import ssl
import requests
import json
import re
from rstream import Producer, AMQPMessage

async def fetch_access_token():
    url = "https://aa2e5455e8e9c4dfca016e71cedc50c5-789763159.il-central-1.elb.amazonaws.com/realms/rabbitmq2/protocol/openid-connect/token"
    client_id = "rabbitmq"
    client_secret = "ZRkOBbFqFIQL38Zkrhtf3hWqiWCweAod"

    post_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(
        url,
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        verify=False  # Accept self-signed certs
    )
    response.raise_for_status()

    match = re.search(r'"access_token"\s*:\s*"([^"]+)"', response.text)
    if match:
        return match.group(1)
    else:
        raise RuntimeError(f"Access token not found in response: {response.text}")

async def publish():
    token = await fetch_access_token()
    print(token)
    # Correct way to create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with Producer(
        host="a462f468f5a3b46648e4174273c54c54-232980629.il-central-1.elb.amazonaws.com",
        port=5551,
        ssl_context=ssl_context,
        username="service-account-rabbitmq",
        password=token,
    ) as producer:
        stream_name = "oauth-rstream-o"


        # create a stream if it doesn't already exist
        await producer.create_stream(stream_name, exists_ok=True)

        for i in range(10):
            amqp_message = AMQPMessage(
                body=f"Hello {i}".encode()
            )
            await producer.send(stream=stream_name, message=amqp_message)
            print(f"✅ Sent message {i}")

asyncio.run(publish())
