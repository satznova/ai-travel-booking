#!/bin/bash

APP_NAME="customer-desk-agent"
USER_ID="test-user"
SESSION_ID="${USER_ID}-$(date +%s)" #Unique Session Id

# ##### Step 1: Create session manually - for adk web this is taken care internally #####
echo "----- Create New Session -----"
curl -X POST "http://localhost:8000/apps/$APP_NAME/users/$USER_ID/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d "{}" | jq .

# Response Body:
# {
#   "id": "test-user-1758628208",
#   "appName": "customer-desk-agent",
#   "userId": "test-user",
#   "state": {},
#   "events": [],
#   "lastUpdateTime": 1758628208.530218
# }

# ##### Step 2: Send Message to the Agent and Analyze the response #####
echo "----- Send message and Analyze the response -----"
RESPONSE=$(curl -s -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_name\": \"$APP_NAME\",
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"new_message\": {
      \"parts\": [{\"text\": \"Hello there...\"}],
      \"role\": \"user\"
    }
  }")

# Print the full response for reference
echo "Full response:"
echo "$RESPONSE" | jq .


