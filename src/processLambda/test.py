from app.app import main_handler


body = {
    "s3_uri": "s3://kb4rag/db-copilot/titanc_csv 1.csv",
    "query": "What is the average age of passengers in the Titanic dataset?",
}

event = {"body": body}
main_handler(event, None)