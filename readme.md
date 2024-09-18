# Slack Channel Export Lambda Function

This AWS Lambda function exports messages from a specified Slack channel within a given date range.

## Features

- Exports messages from a specified Slack channel
- Filters messages by date range
- Includes threaded replies
- Formats output for easy reading
- Handles file attachments

## Prerequisites

- AWS account with Lambda access
- Slack workspace with bot token
- Python 3.8+

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (see Configuration section)
4. Deploy the function to AWS Lambda

## Configuration

Set the following environment variables:

- `SLACK_API_TOKEN`: Your Slack bot token
- `SLACK_CHANNEL`: URL of the Slack channel to export
- `START_DATE`: Start date for message export (format: YYYY-MM-DD)
- `END_DATE`: End date for message export (format: YYYY-MM-DD)

## Usage

The Lambda function can be triggered via AWS Lambda console or API Gateway. It doesn't require any input parameters as it uses environment variables for configuration.

## Output

The function prints the exported messages to the console and returns a JSON response indicating success or failure.

## Local Testing

To test the function locally:

1. Set up environment variables in a `.env` file
2. Run:
   ```
   python lambda_function.py
   ```

## License

[MIT License](LICENSE)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Support

For support, please open an issue in the GitHub repository.