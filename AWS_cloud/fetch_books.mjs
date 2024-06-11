import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand, ScanCommand } from "@aws-sdk/lib-dynamodb";
import { randomUUID } from "crypto";

const ddbDocClient = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler = async (event, context) => {
    try {
        const input = {
            TableName: "RaspiData",
            Select: "ALL_ATTRIBUTES"
        }
        
        const command = new ScanCommand(input);
        const response = await ddbDocClient.send(command);

        return {
            statusCode: 200,
            body: JSON.stringify(response.Items),
        };
    }
    catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: error.message }),
        };
    }
};