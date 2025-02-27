import json
import boto3
import uuid

lex_client = boto3.client("lexv2-runtime")

BOT_ID = "I2LTFEBXDL"
BOT_ALIAS_ID = "TSTALIASID"
LOCALE_ID = "en_US"
SESSION_ID = str(uuid.uuid4())


def lambda_handler(event, context):

    user_message = (
        event.get("messages", [{}])[0].get("unstructured", {}).get("text", "")
    )

    if not user_message:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "userMessage is required"}),
        }

    try:
        lex_response = lex_client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=SESSION_ID,
            text=user_message,
        )
        print(f"Lex response: {lex_response}")

        lex_messages = lex_response.get("messages", {})
        print(f"Lex messages: {lex_messages}")
        lex_reply = (
            [msg["content"] for msg in lex_messages]
            if lex_messages
            else "I didn't understand that."
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"botReply": lex_reply}),
        }

    except Exception as e:
        print(f"Error calling Lex: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
