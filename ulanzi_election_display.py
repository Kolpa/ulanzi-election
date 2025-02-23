import datetime
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from typing import List

import paho.mqtt.client as mqtt
import requests
from dateutil import parser
from dotenv import load_dotenv

# API endpoint
API_URL = os.getenv("API_URL")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class PartyResult:
    name: str
    percentage: float
    color: str


@dataclass
class ProcessedElectionData:
    timestamp: datetime.datetime
    parties: List[PartyResult]


def fetch_election_data():
    """Fetch election data from the DPA Elections Data API"""
    endpoint = f"{API_URL}/results"
    params = {
        "election": os.getenv("ELECTION_ID"),
        "stage": os.getenv("ELECTION_STAGE"),
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch data: {str(e)}")


def process_election_data(data) -> ProcessedElectionData | None:
    """Process the election data and extract relevant information"""
    parties = []

    election_data = data.get("election", {})
    contest = election_data.get("contest", [{}])[0]
    latest = contest.get("results_overall", {}).get("latest", {})
    results = latest.get("results", [])
    status_date = latest.get("status_date", "")
    timestamp = datetime.datetime.now()
    if status_date:
        timestamp = parser.parse(status_date)
    else:
        return None

    for result in results:
        if result.get("target") == "parties":
            party_id = result.get("target_id")
            party = next(
                (p for p in data.get("parties", []) if p.get("id") == party_id), None
            )
            if result.get("percent"):
                if party:
                    parties.append(
                        PartyResult(
                            name=party.get("abbreviation", ""),
                            percentage=result.get("percent", [{}])[0]
                            .get("value", {})
                            .get("absolute", 0),
                            color=party.get("color", "000000"),
                        )
                    )

    # Sort parties by percentage in descending order
    parties.sort(key=lambda x: x.percentage, reverse=True)

    # parse the timestamp to only show the time in HH:MM format with current timezone

    return ProcessedElectionData(timestamp=timestamp, parties=parties)


def generate_bar_chart(party_data: List[PartyResult], threshold: float):
    """
    Generates a bar chart for the 8x32 RGB pixel display.

    :param party_data: List of PartyResult containing party percentage and color in hex format.
    :param threshold: The percentage threshold to determine the color of the indicator.
    :return: List of rectangle objects to draw on the display.
    """
    if len(party_data) == 0:
        return []

    display_width = 20
    display_height = 8
    bar_height = display_height // len(party_data)
    rectangles = [{"df": [0, 0, display_width, display_height, "000000"]}]

    max_percentage = max(party_data, key=lambda x: x.percentage).percentage
    for i, result in enumerate(party_data):
        bar_width = math.ceil((result.percentage / max_percentage) * display_width)
        top_left_x = 0
        top_left_y = i * bar_height
        rectangles.append(
            {"df": [top_left_x, top_left_y, bar_width, bar_height, result.color]}
        )

        # Add red/green indicator
        indicator_color = "00FF00" if result.percentage > threshold else "FF0000"
        rectangles.append(
            {"df": [bar_width, top_left_y, 1, bar_height, indicator_color]}
        )

    return rectangles


def generate_text_message(election_data: ProcessedElectionData):
    """Generate the text message containing the timestamp and the party names in the same color as the bars"""
    text_fragments = []

    start = election_data.timestamp.astimezone().strftime("%H:%M")

    text_fragments.append({"t": f"{start} ", "c": "FFFFFF"})

    for party in election_data.parties:
        text_fragment = {"t": f"{party.name} ", "c": party.color}
        text_fragments.append(text_fragment)

    return text_fragments


def generate_ulanzi_packet(election_data: ProcessedElectionData):
    """Generate the Ulanzi packet containing the bar chart and text message"""
    # Create the JSON object according to the schema

    # create bar chart data for the parties
    bar_chart = generate_bar_chart(election_data.parties, 5)
    text_message = generate_text_message(election_data)

    awtrix_message = {
        "draw": bar_chart,
        "text": text_message,
        "textOffset": 8,
    }

    return awtrix_message


def send_to_ulanzi(message: object):
    """Send the formatted data to the Ulanzi pixel clock"""

    # Convert the message to JSON
    message_json = json.dumps(message)

    # MQTT configuration
    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    mqtt_topic = os.getenv("MQTT_TOPIC")

    # Initialize MQTT client
    conn = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        client.publish(mqtt_topic, message_json)
        client.disconnect()

    conn.on_connect = on_connect
    conn.connect(mqtt_broker, mqtt_port, 60)
    conn.loop_forever()


def main():
    while True:
        try:
            logging.info("Fetching election data...")
            election_data = fetch_election_data()
            logging.info("Processing election data...")
            processed_data = process_election_data(election_data)
            message = {"text": [{"t": "No data", "c": "FF0000"}]}
            if processed_data:
                message = generate_ulanzi_packet(processed_data)
            else:
                logging.error("No election data available")
            logging.info("Sending data to Ulanzi pixel clock...")
            send_to_ulanzi(message)
            logging.info("data successfully sent to Ulanzi pixel clock")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

        logging.info("Waiting for 5 minutes before next update...")
        time.sleep(300)


if __name__ == "__main__":
    load_dotenv()
    logging.info("Starting Ulanzi election display script...")
    main()
