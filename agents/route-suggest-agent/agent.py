import os
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search
from serpapi import GoogleSearch

serp_api_key = os.getenv("SERP_API_KEY")

# Agents are only as effective as the tools we give them.
# https://www.anthropic.com/engineering/writing-tools-for-agents

# without returning day of the week, LLM doesmt know when 'weekend' is ?
# for Diwali, etc. need to integrate calendar 
def get_current_date() -> dict:
    """Returns today's date in YYYY-MM-DD format. Also returns what day of the week today is.

    Returns:
        dict: status and result or error msg.
    """

    tz_identifier = "Asia/Kolkata"
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current date is {now.strftime("%Y-%m-%d")}, the day of the week today is {now.strftime("%A")}'
    return {"status": "success", "report": report}


def search_map_directions(start_addr: str, dest_addr: str) -> list:
    """Returns list of best routes available between start and destination address for different mode of transport
    
    Args:
        start_addr (str): Start Address of travel
        dest_addr (str): Destination Address

    Returns:
        list: List of dictionary. Each item in this list is a dict containing the hotel available information for the specified dates
    """

    # Define the search parameters
    params = {
        "api_key": serp_api_key,
        "engine": "google_maps_directions",
        "start_addr": start_addr,
        "end_addr": dest_addr,  
        "gl": "in",
        "travel_mode": 4
    }
    
    print(params)

    # Create a GoogleSearch object
    search = GoogleSearch(params)
    directions = search.get_json()
    results = []
    
    print(directions)

    if "directions" in directions:
        print("Source to Destination Directions:")
        #print(directions)
        for direction in directions["directions"]:
            if(direction.get('travel_mode') != 'Flight'):
                # print(f"Distance: {direction.get('distance')}")
                # print(f"Duration: {direction.get('duration')}")
                print(f"Travel Mode: {direction.get('travel_mode')}")
                print(f"Distance: {direction.get('formatted_distance')}")
                print(f"Duration: {direction.get('formatted_duration')}")
                print(f"RouteDescription: {direction.get('extensions')}")
                results.append({
                    "TravelMode": direction.get('travel_mode'),
                    "Distance": direction.get('formatted_distance'),
                    "Duration": direction.get('formatted_duration'),
                    "RouteDescription": direction.get('extensions')
                    })
    else:
        results.append("No Directions found.")

    return {"status": "success", "report": results}


def search_directions_via_flight(start_addr: str, dest_addr: str) -> list:
    """Returns list of routes available between start and destination address for travelling via Flight
    
    Args:
        start_addr (str): Start Address of travel
        dest_addr (str): Destination Address

    Returns:
        list: List of dictionary. Each item in this list is a dict containing the Flight details and flight ticket price
    """

    # Define the search parameters
    params = {
        "api_key": serp_api_key,
        "engine": "google_maps_directions",
        "start_addr": start_addr,
        "end_addr": dest_addr,  
        "gl": "in",
        "travel_mode": 4
    }
    
    print(params)

    # Create a GoogleSearch object
    search = GoogleSearch(params)
    directions = search.get_json()
    results = []
    
    print(directions)

    if "directions" in directions:
        print("Source to Destination Directions:")

        for direction in directions["directions"]:
            # print(f"Distance: {direction.get('distance')}")
            # print(f"Duration: {direction.get('duration')}")
            print(f"Travel Mode: {direction.get('travel_mode')}")
            print(f"Airlines: {direction.get('flight').get('airlines')}")
            print(f"Departure: {direction.get('flight').get('departure')}")
            print(f"Arrival: {direction.get('flight').get('arrival')}")
            print(f"RoundTripPrice: {direction.get('flight').get('round_trip_price')}")
            print(f"TravelDuration: {direction.get('flight').get('formatted_nonstop_duration')}")
            print(f"FlightLink: {direction.get('flight').get('google_flights_link')}")
            results.append({
                "TravelMode": direction.get('travel_mode'),
                "Airlines": direction.get('flight').get('airlines'),
                "Departure": direction.get('flight').get('departure'),
                "Arrival": direction.get('flight').get('arrival'),
                "Currency": direction.get('flight').get('currency'),
                "RoundTripPrice": direction.get('flight').get('round_trip_price'),
                "TravelDuration": direction.get('flight').get('formatted_nonstop_duration'),
                "FlightLink": direction.get('flight').get('google_flights_link'),
                })
    else:
        results.append("No Directions found.")

    return {"status": "success", "report": results}


# Date Tool
# Calendar Tool - to find holidays

root_agent = Agent(
    #model=LiteLlm(model="ollama_chat/gpt-oss:20b"),
    model="gemini-2.5-flash",
    name="RouteFinderAndSuggestAgent",
    description=(
        "You are a smart Route suggestion Agent. Between source and destination cities you will suggest all modes of transportation available and how much time will it take to cover the distance."
        "Be very professional and polite while asking any follow-up queries with users if required"
    ),
    instruction="""
    Role: You are a smart Route suggestion Agent.
    - For a source and destination city you will suggest all modes of transportation available and how much time will it take to cover the distance.
    - Be very professional and polite while asking any follow-up queries with users if required
    - If the user does not provide specific transport preferences, make reasonable assumptions and provide fastest transport mode available
    - Display all available directions formatted and share it user 
    """,
    tools=[get_current_date, search_map_directions, search_directions_via_flight]
)

print(f"Agent '{root_agent.name}'.")

session_service = InMemorySessionService()
in_memory_service_py = InMemoryArtifactService()

# Without this Agent it wasnt responding ????????

# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=root_agent, # The agent we want to run
    app_name="Route Suggestion Agent",   # Associates runs with our app
    session_service=session_service, # Uses our session manager
    artifact_service=in_memory_service_py
)
