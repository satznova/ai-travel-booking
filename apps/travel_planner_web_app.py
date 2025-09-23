import streamlit as st
import requests

# Assuming your ADK API server is running on localhost:8000
ADK_AGENT_API_URL = "http://localhost:8000"

st.title("🇮🇳 Smart Travel Planner Chatbot - Itinerary Generator 🌏 and Booking 🗓️")

# ----- Using Basic Question and Response Design -----

user_input = st.text_input("Enter your query for the agent:")

if st.button("Ask Agent"):
    if user_input:
        try:
            # Send request to the ADK API server's /run endpoint
            response = requests.post(f"{ADK_AGENT_API_URL}/run", json={"query": user_input})
            response.raise_for_status()  # Raise an exception for bad status codes

            agent_response = response.json()
            st.write("Agent Response:")
            st.json(agent_response) # Display the full JSON response

        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with ADK server: {e}")
    else:
        st.warning("Please enter a query.")


# ----- Using Chatbot like Design -----

# # st.session_state -> To store and manage the conversation history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# if prompt := st.chat_input("Say something to the agent..."):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Call your ADK agent here
#     # agent_response = my_agent.process_input(prompt) 


#     # For demonstration, a placeholder response:
#     agent_response = f"Agent received: {prompt}" 

#     st.session_state.messages.append({"role": "assistant", "content": agent_response})
#     with st.chat_message("assistant"):
#         st.markdown(agent_response)


# ----- Using Separate Inputs for Customer -----

# origin = st.text_input("From which place you want to start")
# destination = st.text_input("Which place you want to explore")
# start_date = st.date_input("When are you planning")
# end_date = st.date_input("Till which day are you planning")
# budget = st.number_input("Any budget preference in ₹")
# preference = st.text_area("For personalized customisation please share any prefereces you have...🙂")

# if st.button("🛫 Generate my Itinerary"):
#     if not all([origin, destination, start_date]):
#         st.warning("Please fill the plance name you want to explore and start date")
#     else:
#         payload = {
#             "origin": origin,
#             "destination": destination,
#             "start_date": str(start_date),
#             "end_date": str(end_date),
#             "budget": budget,
#             "preferences": preference
#         }
#         response = requests.post("http://localhost:8000/run", json=payload)

#         if response.ok:
#             data = response.json()
#             st.subheader("✈️ Flights")
#             st.markdown(data["flights"])
#             st.subheader("🏨 Stays")
#             st.markdown(data["stay"])
#             st.subheader("🗺️ Activities")
#             st.markdown(data["activities"])
#         else:
#             st.error("Failed to fetch travel plan. Please try again.")

