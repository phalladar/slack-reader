from snowflake.snowpark import Session

connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "role": os.getenv("SNOWFLAKE_ROLE")
}

def get_snowflake_session():
    return Session.builder.configs(connection_params).create()
