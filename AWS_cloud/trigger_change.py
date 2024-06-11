import json
import boto3
import logging

iot_client = boto3.client('iot-data')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            event_name = record.get('eventName', '')  # Safely get eventName
            logger.info(f"Event Name: {event_name}")

            if event_name == 'MODIFY':
                new_image = record['dynamodb'].get('NewImage', {})
                old_image = record['dynamodb'].get('OldImage', {})
                if 'myState' in new_image and 'myState' in old_image and 'id' in new_image:
                    new_my_state = new_image['myState'].get('BOOL', None)
                    old_my_state = old_image['myState'].get('BOOL', None)
                    record_id = new_image['id'].get('S', None)
                    
                    if new_my_state is not None and old_my_state is not None and record_id:
                        if new_my_state != old_my_state:
                            message = f"myState changed from {old_my_state} to {new_my_state} for id {record_id}"
                            logger.info(message)
                            publish_to_iot_topic('responseBack', message)

        return f'Successfully processed {len(event["Records"])} records.'

    except Exception as e:
        logger.error(f"Error processing records: {e}")
        return f"Error processing records: {e}"

def publish_to_iot_topic(topic, message):
    try:
        response = iot_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps({"message": message})
        )
        logger.info(f"Published to topic {topic}: {message}")
        return response
    except Exception as e:
        logger.error(f"Failed to publish message to topic {topic}: {e}")
        return None
