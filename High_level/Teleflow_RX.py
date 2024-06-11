###### INTENDED FOR RECEIVING MESSAGES ON TOPIC "resposeBack". WILL PERFORM ACTIONS (SEND SMS) BASED ON RECIEVED MSG

from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
import random
from utils.command_line_utils import CommandLineUtils
import subprocess

# Define the path to the script you want to call
script_path = './SMSv3.py'

# Define the arguments
phone_number = '5546930459' 
#text_message = 'Hello, this is a test message.'

cmdData = CommandLineUtils.parse_sample_input_pubsub()

received_count = 0

def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    
    # Parse the received message
    message = json.loads(payload)
    if "message" in message:
        message_content = message["message"]
        print(f"Received message content: {message_content}")
        
        if "myState changed from True to False" in message_content:
            id_value = extract_id_from_message(message_content)
            handle_state_change(id_value, "false")
        elif "myState changed from False to True" in message_content:
            id_value = extract_id_from_message(message_content)
            handle_state_change(id_value, "true")
            
def extract_id_from_message(message_content):
    # Extract the id from the message content
    parts = message_content.split(" ")
    return parts[-1]

def handle_state_change(id_value, new_state):
    print(f"Handling state change for id {id_value} to {new_state}")
    if new_state == "false":
        perform_false_state_action(id_value)
    elif new_state == "true":
        perform_true_state_action(id_value)

def perform_false_state_action(id_value):
    print(f"Performing action for id {id_value} when state changed to false")
    text_message = f"{id_value[-1]}_OFF"
    try:
        result = subprocess.run(
            ['python', script_path, '--phone_number', phone_number, '--text_message', text_message],
            check=True,
            capture_output=True,
            text=True
        )
        print("SMS script output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to execute SMS script:", e)
        print("Error output:", e.stderr)

def perform_true_state_action(id_value):
    print(f"Performing action for id {id_value} when state changed to true")
    text_message = f"{id_value[-1]}_ON"
    try:
        result = subprocess.run(
            ['python', script_path, '--phone_number', phone_number, '--text_message', text_message],
            check=True,
            capture_output=True,
            text=True
        )
        print("SMS script output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to execute SMS script:", e)
        print("Error output:", e.stderr)



def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

def on_connection_closed(connection, callback_data):
    print("Connection closed")

# def publish_messages(mqtt_connection, topic, message_count):
#     ids = ["4000", "5000", "6000", "7000"]
#     publish_count = 1
#     while True:
#         message = {
#             "id": ids[(publish_count - 1) % len(ids)],
#             "date": "",
#             "disconnectionDate": "",
#             "myState": "",
#             "powerConsumption": str(random.randint(100, 1000)),  # Random value for powerConsumption
#             "reconnectionDate": ""
#         }
#         print("Publishing message to topic '{}': {}".format(topic, message))
#         message_json = json.dumps(message)
#         mqtt_connection.publish(
#             topic=topic,
#             payload=message_json,
#             qos=mqtt.QoS.AT_LEAST_ONCE)
#         time.sleep(1)
#         if message_count != 0:
#             if publish_count >= message_count:
#                 break
#             publish_count += 1
            
# def get_json_results():
#     try:
#         result = subprocess.run(['python3', 'data_analysis.py'], capture_output=True, text=True)
#         if result.returncode == 0:
#             json_results = result.stdout
#             logger.info("Raw output from data_analysis.py: %s", json_results)
#             try:
#                 data = json.loads(json_results)
#                 return data
#             except json.JSONDecodeError as e:
#                 logger.error("Failed to decode JSON: %s", e)
#                 logger.error("Problematic JSON output: %s", json_results)
#                 return None
#         else:
#             logger.error("data_analysis.py script failed with return code %d", result.returncode)
#             logger.error("Error output: %s", result.stderr)
#             return None
#     except Exception as e:
#         logger.error("An error occurred while running data_analysis.py: %s", e)
#         return None



if __name__ == '__main__':
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)

    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    subscribe_topic = "responseBack"
    #publish_topic = cmdData.input_topic
    #message_count = cmdData.input_count

    print("Subscribing to topic '{}'...".format(subscribe_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=subscribe_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Start a thread to publish messages
    #publish_thread = threading.Thread(target=publish_messages, args=(mqtt_connection, publish_topic, message_count))
    #publish_thread.start()

    
    # json_data = get_json_results()
    # if json_data:
    #     print("Captured JSON Results:")
    #     print(json.dumps(json_data, indent=4))


    try:
        print("Waiting for messages on topic '{}'...".format(subscribe_topic))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")

# RX V3
