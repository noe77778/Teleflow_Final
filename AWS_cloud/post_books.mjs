import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, UpdateCommand } from "@aws-sdk/lib-dynamodb";

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

export const handler = async (event) => {
  try {
    const body = JSON.parse(event.body);
    
    const command = new UpdateCommand({
      TableName: "RaspiData",
      Key: {
        id: body.id,
      },
      UpdateExpression: "set myState = :newState",
      ExpressionAttributeValues: {
        ":newState": body.state,
      }
    });
  
    const response = await docClient.send(command);
    console.log(response);
    return {
      statusCode: 200,
      body: JSON.stringify("Item updated successfully!")
    };
  } catch (error) {
    console.error(error);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: error.message }),
    };
  }
};