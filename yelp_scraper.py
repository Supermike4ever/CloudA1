from decimal import Decimal
import requests
import boto3
import time

# Yelp API Key (replace with your actual API key)
YELP_API_KEY = "V7JgI5thwU_3uwBOO_GoZQagxRNpvzBIB85sIlmDAVti912WQUEU7g57hZ3iXFiVjYqojBbqoT5pnSOn5hOhlFr8XL84BLqsSRUEm0yd3gToZUT6cYOtOPzz7lC-Z3Yx"
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

# Define search parameters
LOCATION = "Manhattan, NY"
CUISINE_TYPES = ["chinese", "korean", "japanese"]
LIMIT = 50  # Max per request
MAX_RESULTS_PER_CUISINE = 50  # Ensure we get ~50 per cuisine
DYNAMODB_TABLE = "yelp-restaurants"

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)

def fetch_restaurants(cuisine):
    all_restaurants = []
    offset = 0  # Pagination offset

    while offset < MAX_RESULTS_PER_CUISINE:
        url = "https://api.yelp.com/v3/businesses/search"
        params = {
            "location": LOCATION,
            "categories": cuisine,
            "limit": LIMIT,
            "offset": offset
        }

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            break

        data = response.json()
        businesses = data.get("businesses", [])

        if not businesses:
            break  # No more results to fetch

        all_restaurants.extend(businesses)
        offset += LIMIT  # Move to next set

        # Avoid hitting rate limits
        time.sleep(1)  

    return all_restaurants

def store_in_dynamodb(restaurants, cuisine):
    for restaurant in restaurants:
        item = {
            "Cuisine": cuisine,
            "BusinessID": restaurant["id"],
            "Name": restaurant["name"],
            "Address": ", ".join(restaurant["location"]["display_address"]),
            "Coordinates": str(restaurant["coordinates"]),
            "NumberOfReviews": Decimal(str(restaurant["review_count"])),
            "Rating": Decimal(str(restaurant["rating"])),
            "ZipCode": restaurant["location"].get("zip_code", "N/A"),
            "InsertedAtTimestamp": int(time.time())  # Current timestamp
        }

        table.put_item(Item=item)
        print(f"Inserted: {restaurant['name']}")

if __name__ == "__main__":
    for cuisine in CUISINE_TYPES:
        print(f"Fetching {cuisine} restaurants...")
        restaurants = fetch_restaurants(cuisine)
        store_in_dynamodb(restaurants, cuisine)