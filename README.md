# Bluedart Package Tracking API

This project is a FastAPI-based application designed to track Bluedart packages and send Telegram messages when the package details are updated. The application periodically checks the status of packages and updates the database with the latest information. If there are any changes in the package status, a notification is sent to a specified Telegram channel.

## Features

- **Track Bluedart Packages**: Fetch and store the status of Bluedart packages.
- **Periodic Status Updates**: Automatically update package statuses at regular intervals.
- **Telegram Notifications**: Send notifications to a Telegram channel when package details are updated.
- **CRUD Operations**: Create, read, update, and delete package tracking information via API endpoints.

## Environment Variables

The application uses the following environment variables, which should be defined in a `.env` file:

- `TELEGRAM_TOKEN`: The token for the Telegram bot.
- `CHANNEL_ID`: The ID of the Telegram channel to send notifications to.
- `SLEEP_INTERVAL`: The interval (in seconds) between status checks.

## Installation

1. Clone the repository.
2. Create a virtual environment and activate it.
3. Install the required dependencies using `pip install -r requirements.txt`.
4. Set up the environment variables in a `.env` file.
5. Run the application using Docker or directly with FastAPI.

## Usage

### Start the Application

Use Docker or run the FastAPI application directly.

### API Endpoints

- `GET /health`: Check the health of the application.
- `GET /track/{num}`: Track a specific package by its number.
- `GET /track`: List all tracked packages with pagination.
- `POST /track`: Create a new package tracking entry.
- `DELETE /track/{num}`: Delete a package tracking entry by its number.

## Docker

The application can be containerized using Docker. Use the provided Dockerfile and docker-compose files to build and run the application in a development or production environment.

## Scheduler

The application uses APScheduler to periodically check and update the package statuses. The scheduler is configured to run every minute and can be adjusted as needed.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.
