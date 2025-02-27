import json
import boto3
import random
import ast
import urllib3
import base64
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError

http = urllib3.PoolManager()
USERNAME = "supermike"
PASSWORD = "Supermike-4ever"
auth_header = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()

# AWS Clients
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses", region_name="us-east-1")

# Configurations
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/135808949521/Q1"
DYNAMODB_TABLE_NAME = "yelp-restaurants"
ELASTICSEARCH_URL = "https://search-restaurant-search-mbmfcgc37olm4qznaf66gvpitq.aos.us-east-1.on.aws/restaurants"
SES_SENDER_EMAIL = "kp2653@nyu.edu"


def fetch_restaurant_from_elasticsearch(cuisine):
    """Fetch a random restaurant matching the cuisine from ElasticSearch."""
    print(f"Fetching restaurant for cuisine: {cuisine}")

    try:
        url = f"{ELASTICSEARCH_URL}/_search"
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
        }
        body = {"query": {"match": {"Cuisine": cuisine}}, "size": 1}
        print(f"Requesting URL: {url}")  # Debugging

        response = http.request(
            "GET", url, headers=headers, body=json.dumps(body).encode("utf-8")
        )
        response_text = response.data.decode("utf-8").strip()  # Trim whitespace
        print(f"Response status: {response.status}")  # Debugging
        print(f"Response text: {response_text}")  # Debugging

        if not response_text:  # If response is empty
            print("Error: Empty response from Elasticsearch")
            return None

        data = json.loads(response_text)  # Parse JSON

        if "hits" in data and "hits" in data["hits"]:
            restaurants = data["hits"]["hits"]
            if restaurants:
                return random.choice(restaurants)["_source"]
            else:
                print(
                    f"No restaurants found for {cuisine} in Elasticsearch response: {data}"
                )
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
    except Exception as e:
        print(f"Error fetching from Elasticsearch: {e}")

    return None


def fetch_details_from_dynamodb(restaurant_id):
    """Fetch restaurant details from DynamoDB."""
    print(f"Fetching details for restaurant ID: {restaurant_id}")
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        response = table.get_item(Key={"BusinessID": restaurant_id})
        print(f"DynamoDB response: {response}")
        return response.get("Item", {})
    except (BotoCoreError, NoCredentialsError) as e:
        print(f"Error fetching from DynamoDB: {e}")
        return {}


def send_email(to_email, subject, message):
    """Send email using AWS SES."""
    CHARSET = "UTF-8"
    print(f"Sending email to: {to_email}")

    try:
        response = ses.send_email(
            Destination={"ToAddresses": [to_email]},
            Message={
                "Body": {"Text": {"Charset": CHARSET, "Data": message}},
                "Subject": {"Charset": CHARSET, "Data": subject},
            },
            Source=SES_SENDER_EMAIL,
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")


def process_sqs_message(message):
    """Process an SQS message by fetching restaurant details and sending an email."""
    print("Processing SQS message")
    try:
        message_body = ast.literal_eval(message["body"])
        cuisine = message_body.get("cuisine", "").lower()
        recipient_email = message_body.get("email", "")

        if not cuisine or not recipient_email:
            print("Missing required fields: cuisine or email.")
            return

        restaurant = fetch_restaurant_from_elasticsearch(cuisine)
        if not restaurant:
            print(f"No matching restaurant found for cuisine: {cuisine}.")
            return

        restaurant_id = restaurant.get("RestaurantId")
        details = fetch_details_from_dynamodb(restaurant_id)
        print(f"Restaurant details: {details}")

        email_subject = f"Recommended {cuisine.capitalize()} Restaurant for You!"
        email_body = (
            f"Hello,\n\n"
            f"We found a great {cuisine.capitalize()} restaurant for you!\n"
            f"Name: {details.get('Name', 'Unknown')}\n"
            f"Address: {details.get('Address', 'Not Available')}\n"
            f"Rating: {details.get('Rating', 'Not Available')}\n"
            f"NumberOfReviews: {details.get('NumberOfReviews', 'Not Available')}\n\n"
            f"Enjoy your meal!"
        )

        send_email(recipient_email, email_subject, email_body)

    except Exception as e:
        print(f"Error processing SQS message: {e}")


def lambda_handler(event, context):
    """Lambda handler function that polls messages from SQS."""
    try:
        print("Lambda function is running")
        print(event)
        if "Records" not in event:
            print("No messages received from SQS.")
            return

        messages = event["Records"]
        for message in messages:
            process_sqs_message(message)

    except Exception as e:
        print(f"Error in Lambda handler: {e}")
