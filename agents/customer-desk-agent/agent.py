import os
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search
from serpapi import GoogleSearch

# main.py
from fastapi import FastAPI
from pydantic import BaseModel


serp_api_key = os.getenv("SERP_API_KEY")

# ----- START: HOTEL SEARCH AGENT -----

def get_current_date() -> dict:
    """Returns today's date in YYYY-MM-DD format. Also returns what day of the week today is.
    This method can also be used to calculate what day of the week is.

    Returns:
        dict: status and result or error msg.
    """

    tz_identifier = "Asia/Kolkata"
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current date is {now.strftime("%Y-%m-%d")}, the day of the week today is {now.strftime("%A")}'
    return {"status": "success", "report": report}


def search_hotels(query: str, start_date: str, end_date: str) -> list:
    """Returns list of Hotels availablile for a range of specified days in a city for booking.
    Returns minimum rate per night, places that are nearer to the hotel, Review ratings of the hotels, class of the hotel like 2 or 3 or 4 or 5 stars, check-in and check-out time policy, etc.

    Args:
        city (str): The name of the city to get list of hotel availability
        start_date (str): Hotel check-in date in YYYY-MM-DD format
        end_date (str): Hotel check-out date in YYYY-MM-DD format

    Returns:
        list: List of dictionary. Each item in this list is a dict containing the hotel available information for the specified dates
    """

    # Define the search parameters
    params = {
        "api_key": serp_api_key,
        "engine": "google_hotels",  # Specify the search engine (e.g., google, google_maps, youtube)
        "q": query,  # The search query
        "check_in_date": start_date, # Required
        "check_out_date": end_date, # Required
        # "adults": "",
        # "children": "",

        "location": "India",  # Optional: Geolocation for localized results
        "hl": "en",  # Optional: Host language
        "gl": "in",  # Optional: Geolocation for country-specific results
        "currency": "INR" # Optional: Defaults to USD,
    }

    print(params)

    # Create a GoogleSearch object
    search = GoogleSearch(params)

    # Get the results as a JSON object
    hotels = search.get_json()
    results = []

    # Process and print the organic results
    if "properties" in hotels:
        print("Hotel Properties:")
        for hotel in hotels["properties"]:
            print(f"Name: {hotel.get('name')}")
            print(f"Link: {hotel.get('link')}")
            print(f"Check-In: {hotel.get('check_in_time')} - Check-Out Time: {hotel.get('check_out_time')}")
            print(f"Starting Rate Per Night: {hotel.get('rate_per_night').get('lowest')}")
            print(f"Hotel Class: {hotel.get('hotel_class')}")
            print(f"User Google Ratings: {hotel.get('overall_rating')}")
            print(f"Nearby Places: {hotel.get('nearby_places')}\n")
            results.append({
                "Name": hotel.get('name'),
                "Link": hotel.get('link'),
                "Check-In": hotel.get('check_in_time'),
                "Check-Out": hotel.get('check_out_time'),
                "HotelClass": hotel.get('hotel_class'),
                "StartingRatePerNight": hotel.get('rate_per_night').get('lowest'),
                "UserRatings": hotel.get('overall_rating'),
                "NearbyPlaces": hotel.get('nearby_places')
                })
    else:
        results.append("No Hotel Properties found.")

    return {"status": "success", "report": results}


# Date Tool
# Calendar Tool - to find holidays

hotel_booking_agent = Agent(
    #model=LiteLlm(model="ollama_chat/gpt-oss:20b"),
    model="gemini-2.5-flash",
    name="HotelBookingAgent",
    description=(
        "You are a smart Hotel Booking Agent. You will search and answer queries about availablity of hotels for the mentioned tourist city located within India"
        "Be very professional and polite while asking any follow-up queries with users"
    ),
    instruction="""
        Role: You are a Indian Hotel Booking Agent.
        - You take any hotel accomodation request and suggest only the top 3 best hotels to stay in that city.
        - Hotels should be located within the touris city mentioned by the user.
        - If the user has mentioned any preference to visit any specific places in the city, then give preference to hotels that are nearer to those places.
        - Summarise the Hotel recommendation in a markdown structure, includ check-in and check-out timings, user ratings and hotel booking link
        - Share only the hotels which has web links available for booking
        - If the user does not provide specific details, make reasonable assumptions and provide hotels suggestions with more than 4 star class Hotels
    """,
    tools=[get_current_date, search_hotels]
)

# ----- END: HOTEL SEARCH AGENT -----

# ----- START: ROUTE DESTINATION SUGGEST AGENT -----

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

route_finder_agent = Agent(
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


# ----- END: ROUTE DESTINATION SUGGEST AGENT -----


root_agent = Agent(
    #model=LiteLlm(model="ollama_chat/gpt-oss:20b"),
    model="gemini-2.5-flash",
    name="HelpDeskAgent",
    description=(
        "You are a smart Customer Help Desk Agent. You will help customer to plan a travel itenary for the customer for tarvel within India"
        "Be very professional and polite while asking any follow-up queries with users"
    ),
    instruction="""
        Role: You are a Customer Help Desk Agent.
        - You will help customer to plan a travel itenary for the customer for tarvel within India
        - Help customer with hotel suggestions for the city they are tarvelling and suggest hotels for stay. Use hotel_booking_agent to generate Hotel recommendations
        - Also, help customers to book round trip travel arrangements to reach their destination city. Use route_finder_agent to find the Travel recommednations
        - Share the summarised itenary of the travel by Summarising hotel stay recommendations and travel options for the customer.
        - Be very professional and polite while asking any follow-up queries with users"
    """,
    tools=[get_current_date],
    sub_agents = [
        route_finder_agent, hotel_booking_agent
    ],
)


print(f"Agent '{root_agent.name}'.")

session_service = InMemorySessionService() 

# Without this Agent it wasnt responding ????????

# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=root_agent, # The agent we want to run
    app_name="Help Desk Agent",   # Associates runs with our app
    session_service=session_service # Uses our session manager
)

# app = FastAPI()

# class AgentRunRequest(BaseModel):
#     input: str

# @app.post("/run_agent")
# async def run_agent(request: AgentRunRequest):
#     response = await root_agent.run(request.input)  # Assuming your agent has an async 'run' method
#     return {"response": response}


# TODO
# Create Testing in local before integrating with Streamlit https://google.github.io/adk-docs/get-started/testing/