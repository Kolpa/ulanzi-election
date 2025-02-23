# Ulanzi Election Display

This project is designed to display election data on a Ulanzi TC001 Smart Pixel Clock running awtrix3. It fetches data from the DPA electionsdata API and displays it on the device.

![awtrix](https://github.com/user-attachments/assets/bdab140b-5f00-40f1-8355-b666dcefc6e8)

## Prerequisites

- Python 3.x
- MQTT broker
- Ulanzi TC001 Smart Pixel Clock running [awtrix3](https://blueforcer.github.io/awtrix3)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Kolpa/ulanzi-election
    cd ulanzi-election
    ```

2. Copy the `env.example` file to `.env` and update the environment variables with your configuration:
    ```bash
    cp env.example .env
    ```

3. Run via `uv`
    ```bash
    uv run python ulanzi_election_display.py
    ```


## Environment Variables

The following environment variables need to be set in the `.env` file:

- `API_URL`: Replace with the API URL from [DPA Newslab API](https://api-portal.dpa-newslab.com/api/electionsdata)
- `ELECTION_ID`: The ID of the election (e.g., `de-2025`)
- `ELECTION_STAGE`: The stage of the election (e.g., `live`)
- `MQTT_BROKER`: The MQTT broker address
- `MQTT_PORT`: The MQTT broker port (default is `1883`)
- `MQTT_TOPIC`: The MQTT topic that the ulanzi view is published under

## Usage

Run the script to start fetching and displaying the election data:
```bash
python ulanzi_election_display.py
```

## License

This project is licensed under the MIT License.
