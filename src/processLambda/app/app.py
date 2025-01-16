import pandas as pd
import boto3
from io import StringIO, BytesIO
from pandasai import SmartDataframe
from pandasai.llm import BedrockClaude
import logging
from os import environ
import json

logger = logging.getLogger()
log_level = environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(log_level)

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
top_p = float("0.1")
temperature = float("0.1")
max_tokens = int("1024")
bedrock_llm = BedrockClaude(
    bedrock_runtime_client=bedrock_runtime,
    model=model_id,
    top_p=top_p,
    temperature=temperature,
    max_tokens=max_tokens,
)

config = {
    "save_logs": False,
    "open_charts": False,
    "save_charts": False,
    "save_charts_path": "/tmp",
    "direct_sql": False,
    "llm": bedrock_llm,
    "enable_cache": False
}


def main_handler(event, context):
    logger.info(f"Event: {event}")
    logger.info(f"Context: {context}")
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    s3_uri = body.get("s3_uri")
    query = body.get("query")
    dataframe = read_file(s3_uri)
    if not dataframe.empty:
        logger.info(f"Dataframe loaded from S3: {dataframe.head()}")
        response_text = run_smart_df(dataframe, query)
        print(response_text)
        return {
            "statusCode": 200,
            "body": json.dumps({"response": response_text}),
            "headers": {"Content-Type": "application/json"},
        }
    else:
        logger.error("No data found in the S3 file.")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No data found in the S3 file."}),
            "headers": {"Content-Type": "application/json"},
        }


def run_smart_df(dataframe, user_query):
    smart_dataframe = SmartDataframe(dataframe, config=config)
    response_text = smart_dataframe.chat(query=user_query, output_type="string")
    logger.info(f"Response from SmartDataframe: {response_text}")
    return response_text


def read_file(file_path):
    """
    Reads a CSV or Excel file from local or S3 URI and returns a Pandas DataFrame.

    Parameters:
        file_path (str): Path to the file to be read. The file can be in CSV or Excel format.
                         Supports S3 URIs (s3://bucket_name/file_path).

    Returns:
        pd.DataFrame: DataFrame containing the file's data.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist (for local files).
    """

    def read_from_s3(s3_uri):
        print(f"Reading file from S3 URI: {s3_uri}")
        s3 = boto3.client("s3")
        bucket_name, key = s3_uri.replace("s3://", "").split("/", 1)
        print(f"Extracted bucket name: {bucket_name}, key: {key}")
        response = s3.get_object(Bucket=bucket_name, Key=key)
        print("Successfully fetched object from S3")
        if s3_uri.endswith(".csv"):
            print("Detected file format: CSV")
            return pd.read_csv(StringIO(response["Body"].read().decode("utf-8")))
        elif s3_uri.endswith(".xlsx") or s3_uri.endswith(".xls"):
            print("Detected file format: Excel")
            return pd.read_excel(BytesIO(response["Body"].read()))
        else:
            print("Unsupported file format for S3 file")
            raise ValueError(
                "Unsupported file format. Please provide a .csv or .xlsx/.xls file."
            )

    try:
        print(f"Reading file from path: {file_path}")
        if file_path.startswith("s3://"):
            print("Detected S3 URI")
            return read_from_s3(file_path)
        elif file_path.endswith(".csv"):
            print("Detected file format: CSV")
            return pd.read_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            print("Detected file format: Excel")
            return pd.read_excel(file_path)
        else:
            print("Unsupported file format")
            raise ValueError(
                "Unsupported file format. Please provide a .csv or .xlsx/.xls file."
            )
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        raise FileNotFoundError(f"The file '{file_path}' was not found.") from e
    except Exception as e:
        print(f"An error occurred: {e}")
        raise Exception(f"An error occurred while reading the file: {e}") from e


# df = read_file('s3://kb4rag/db-copilot/titanc_csv 1.csv')
# print(df.head())
# input_text = "What is the average age of passengers in the Titanic dataset?"
# response_text = run_smart_df(df, input_text)
# print(response_text)