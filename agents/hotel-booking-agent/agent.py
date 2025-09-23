import os
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

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
    tools=[get_current_date, search_hotels, google_search]
)

print(f"Agent '{hotel_booking_agent.name}'.")

session_service = InMemorySessionService() 

# Without this Agent it wasnt responding ????????

# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=hotel_booking_agent, # The agent we want to run
    app_name="Hotel Booking Agent",   # Associates runs with our app
    session_service=session_service # Uses our session manager
)



# Output from search_hotels should be summarised by the LLM and generate a summarised output

# root_agent = Agent(
#     model=LiteLlm(model="ollama_chat/mistral:7b"),
#     name="SightseeingAgent",
#     description=(
#         "You are a smart Travel Planner Agent. You will politely answer questions about hotel availablility for any  for booking for the users interested city in India"
#     ),
#     instruction=(
#         """You are a Indian sightseeing information agent.
#     - You take any sightseeing request and suggest only the top 2 best places to visit, timings, and any other relevant details.
#     - For sightseeing request take only places located within India 
#     - Always return a valid JSON with sightseeing information, including places to visit, timings, and any other relevant details based on user request.
#     - If the user does not provide specific details, make reasonable assumptions about the sightseeing options available.
#     """
#     ),
#     tools=[search_hotels],
# )



# @tool
# def greet_user(name: str) -> str:
#     """Greets the user by name."""
#     return f"Hello, {name}!"



# def get_weather(city: str) -> dict:
#     """Retrieves the current weather report for a specified city.

#     Args:
#         city (str): The name of the city for which to retrieve the weather report.

#     Returns:
#         dict: status and result or error msg.
#     """
#     if city.lower() == "new york":
#         return {
#             "status": "success",
#             "report": (
#                 "The weather in New York is sunny with a temperature of 25 degrees"
#                 " Celsius (77 degrees Fahrenheit)."
#             ),
#         }
#     else:
#         return {
#             "status": "error",
#             "error_message": f"Weather information for '{city}' is not available.",
#         }


# def get_current_time(city: str) -> dict:
#     """Returns the current time in a specified city.

#     Args:
#         city (str): The name of the city for which to retrieve the current time.

#     Returns:
#         dict: status and result or error msg.
#     """

#     if city.lower() == "new york":
#         tz_identifier = "America/New_York"
#     else:
#         return {
#             "status": "error",
#             "error_message": (
#                 f"Sorry, I don't have timezone information for {city}."
#             ),
#         }

#     tz = ZoneInfo(tz_identifier)
#     now = datetime.datetime.now(tz)
#     report = (
#         f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
#     )
#     return {"status": "success", "report": report}


# def get_top_tourist_places(query: str) -> dict:
#     """Return Top Tourist places and time to visit for a specified city

#     Args:
#         city (str): The name of the city for which to retrieve the current time.

#     Returns:
#         dict: Tourist spt and result or error msg.
#     """

#     params = {
#         "q": "python programming",
#         "api_key": "YOUR_API_KEY"
#     }

#     search = GoogleSearch(params)
#     results = search.get_dict()

#     # Process the structured results (e.g., print organic results titles)
#     for result in results.get("organic_results", []):
#         print(result.get("title"))