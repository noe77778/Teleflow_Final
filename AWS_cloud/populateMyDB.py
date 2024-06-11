import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Initialize DynamoDB client
    client = boto3.client('dynamodb')
    
    try:
        # Ensure powerConsumption is numeric and convert to string
        power_consumption = event.get('powerConsumption', '')
        if power_consumption and not isinstance(power_consumption, (int, float)):
            raise ValueError("powerConsumption must be a numeric value")
        
        # Prepare item with empty strings for missing values
        item = {
            'id': {'S': event.get('id', '')},
            'date': {'S': event.get('date', '')},
            'disconnectionDate': {'S': event.get('disconnectionDate', '')},
            'myState': {'S': event.get('myState', '')},
            'powerConsumption': {'N': str(power_consumption) if power_consumption else '0'},
            'reconnectionDate': {'S': event.get('reconnectionDate', '')}
        }

        # Put item into DynamoDB
        response = client.put_item(
            TableName='RaspiData',
            Item=item
        )
        logger.info(f"Successfully inserted item: {response}")
        return {
            'statusCode': 200,
            'body': 'Item successfully inserted'
        }
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return {
            'statusCode': 400,
            'body': str(ve)
        }
    except Exception as e:
        logger.error(f"Error inserting item: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error inserting item'
        }
