import json
import base64
import urllib.request
import urllib.error
from urllib.parse import urljoin
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

# Constants
BATCH_SIZE = 50
ES_USERNAME = "supermike"
ES_PASSWORD = "Supermike-4ever"
ES_INDEX_URL = "https://search-restaurant-search-mbmfcgc37olm4qznaf66gvpitq.aos.us-east-1.on.aws/restaurants/_doc"


def index_document(restaurant_id, cuisine):
    """Indexes a single document in OpenSearch."""
    doc = {
        "RestaurantId": restaurant_id,
        "Cuisine": cuisine.lower() if cuisine else "unknown",
    }

    # Encode authentication credentials
    credentials = f"{ES_USERNAME}:{ES_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    data = json.dumps(doc).encode("utf-8")
    request = urllib.request.Request(
        ES_INDEX_URL, data=data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            print("Document Indexed Successfully:", response_data)
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.reason)
    except urllib.error.URLError as e:
        print("URL Error:", e.reason)
    except Exception as ex:
        print("Unexpected Error:", str(ex))


def convert_float_to_decimal(obj):
    """Recursively converts float values to Decimal."""
    if isinstance(obj, list):
        return [convert_float_to_decimal(x) for x in obj]
    if isinstance(obj, dict):
        return {k: convert_float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def lambda_handler(event, context):
    """Lambda function entry point."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("yelp-restaurants")

    # Retrieve all records from the DynamoDB table
    response = table.scan()
    items = response.get("Items", [])
    print("Total items retrieved:", len(items))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    count = 0
    for item in items:
        item = convert_float_to_decimal(item)
        business_id = item.get("BusinessID")
        cuisine = item.get("Cuisine")

        if not business_id or not cuisine:
            continue

        index_document(business_id, cuisine)
        count += 1

        if count % BATCH_SIZE == 0:
            pass
