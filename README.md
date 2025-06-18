# Gerador GNRE Backend

This project is a backend application for handling GNRE (Guia Nacional de Recolhimento de Tributos Estaduais) related requests. It provides functionalities for generating XML documents for GNRE submissions and includes JWT authentication for secure access.

## Project Structure

```
gerador-gnre-backend/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── gnre.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── xml_generator.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── jwt.py
│   └── config.py
├── uploads/                   # Directory for storing A1 certificates
├── .env                       # Environment variables
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── run.py                     # Entry point for the application
└── requirements.txt           # Python dependencies
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd gerador-gnre-backend
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your configuration settings.

5. **Run the application:**
   ```
   python run.py
   ```

## Usage

- The application exposes routes for handling GNRE requests through the defined endpoints in `app/routes/gnre.py`.
- XML generation for GNRE submissions can be done using the functions provided in `app/services/xml_generator.py`.
- JWT authentication is managed in `app/auth/jwt.py`.

## Docker

To run the application using Docker, use the following command:

```
docker-compose up
```

This will build the Docker image and start the application in a containerized environment.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.