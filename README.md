# Indian Courier Tracking Hub

A comprehensive tracking system that integrates with multiple Indian courier services, providing unified tracking capabilities, automated status updates, and real-time notifications. The system periodically checks package statuses and sends updates via Telegram when changes are detected.

## Features

### Carrier Support

Currently integrated with major Indian logistics providers:

- Bluedart
- DTDC (with Selenium-based tracking)
- Delhivery
- ShadowFax
- Ecom Express

### Core Functionality

- **Automated Tracking**: Periodic status checks for all active packages
- **Real-time Notifications**: Instant Telegram updates on status changes
- **Status History**: Complete tracking history for each package
- **Delivery Detection**: Automatic package status management upon delivery
- **RESTful API**: Comprehensive endpoints for tracking management

## Technical Stack

- **Backend Framework**: FastAPI
- **Database**: SQLModel with SQLite
- **Task Scheduling**: AsyncIO Scheduler (APScheduler)
- **Web Scraping**:
  - Selenium with Chrome for Testing
  - BeautifulSoup4 for HTML parsing
- **Containerization**: Docker with multi-stage builds
- **Notifications**: Telegram Bot API

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
