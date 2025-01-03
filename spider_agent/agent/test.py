import os
import json
import pandas as pd
import snowflake.connector

# Load Snowflake credentials
snowflake_credential = json.load(open("../../snowflake_credential.json"))

# Connect to Snowflake
conn = snowflake.connector.connect(
    **snowflake_credential
)
cursor = conn.cursor()