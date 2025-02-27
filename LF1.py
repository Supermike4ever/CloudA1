from datetime import datetime
import dateutil.tz

cuisines = ["chinese", "japanese", "korean"]
eastern = dateutil.tz.gettz("US/Eastern")


def validate_slots(slots):
    if not slots["Cuisine"]:
        print("Cuisine slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "Cuisine",
        }

    if slots["Cuisine"]["value"]["originalValue"].lower() not in cuisines:
        print("Cuisine slot is invalid")

        return {
            "isValid": False,
            "invalidSlot": "Cuisine",
            "message": "Please select a valid cuisine from the list: chinese, japanese, korean.",
        }

    if not slots["Location"]:
        print("Location slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "Location",
        }

    if slots["Location"]["value"]["originalValue"].lower() != "manhattan":
        print("Location slot is invalid")

        return {
            "isValid": False,
            "invalidSlot": "Location",
            "message": "Please select a valid location from the list: manhattan.",
        }

    if not slots["NumberOfPeople"]:
        print("NumberOfPeople slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "NumberOfPeople",
        }

    if (
        not slots["NumberOfPeople"]["value"]["originalValue"].isdigit()
        or int(slots["NumberOfPeople"]["value"]["originalValue"]) <= 0
    ):
        # Check if the value is a positive integer
        print("NumberOfPeople slot is invalid")

        return {
            "isValid": False,
            "invalidSlot": "NumberOfPeople",
            "message": "Please enter a valid number of people.",
        }

    if not slots["DiningDate"]:
        print("DiningDate slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "DiningDate",
        }

    date_format = "%Y-%m-%d"
    input_date = datetime.strptime(
        slots["DiningDate"]["value"]["interpretedValue"], date_format
    ).date()

    if input_date < datetime.now(tz=eastern).date():
        print("DiningDate slot is invalid")

        return {
            "isValid": False,
            "invalidSlot": "DiningDate",
            "message": "Please enter a valid date.",
        }

    if not slots["DiningTime"]:
        print("DiningTime slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "DiningTime",
        }

    time_format = "%H:%M"
    input_time = datetime.strptime(
        slots["DiningTime"]["value"]["interpretedValue"], time_format
    ).time()
    input_datetime = datetime.combine(input_date, input_time).replace(tzinfo=eastern)

    if input_datetime < datetime.now(tz=eastern):

        return {
            "isValid": False,
            "invalidSlot": "DiningTime",
            "message": "Please enter a valid time.",
        }

    if not slots["Email"]:
        print("Email slot is empty")

        return {
            "isValid": False,
            "invalidSlot": "Email",
        }

    return {"isValid": True}


def send_to_sqs(slots):
    import boto3

    print("enter send_to_sqs")

    try:
        sqs = boto3.client("sqs")
        queue_url = "https://sqs.us-east-1.amazonaws.com/135808949521/Q1"

        message_body = {
            "cuisine": slots["Cuisine"]["value"]["originalValue"],
            "location": slots["Location"]["value"]["originalValue"],
            "date": slots["DiningDate"]["value"]["interpretedValue"],
            "time": slots["DiningTime"]["value"]["interpretedValue"],
            "number_of_people": slots["NumberOfPeople"]["value"]["originalValue"],
            "email": slots["Email"]["value"]["originalValue"],
        }

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=str(message_body),
        )
        print("SQS Response:", response)
    except Exception as e:
        print("Error sending to SQS:", str(e))


def lambda_handler(event, context):

    intent = event["sessionState"]["intent"]["name"]
    slots = event["sessionState"]["intent"]["slots"]

    input_validation_result = validate_slots(slots)

    if event["invocationSource"] == "DialogCodeHook":
        if not input_validation_result["isValid"]:
            if "message" in input_validation_result:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": input_validation_result["invalidSlot"],
                            "type": "ElicitSlot",
                        },
                        "intent": {"name": intent, "slots": slots},
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": input_validation_result["message"],
                        }
                    ],
                }
            else:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": input_validation_result["invalidSlot"],
                            "type": "ElicitSlot",
                        },
                        "intent": {"name": intent, "slots": slots},
                    }
                }
        else:
            response = {
                "sessionState": {
                    "dialogAction": {"type": "Delegate"},
                    "intent": {"name": intent, "slots": slots},
                }
            }

    if event["invocationSource"] == "FulfillmentCodeHook":
        print("send to Q1: ", str(slots))
        send_to_sqs(slots)

        response = {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": intent, "slots": slots, "state": "Fulfilled"},
            },
            "messages": [
                {"contentType": "PlainText", "content": "Expect my suggestion shortly!"}
            ],
        }

    print(response)
    return response
