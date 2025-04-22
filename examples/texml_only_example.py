"""
Example showing how to use Twilnyx with TeXML only (no Telnyx API calls).
"""

import twilnyx
from twilio.rest import Client

# Initialize Twilnyx with TeXML mode
# Note: API credentials are no longer required but kept for backward compatibility
twilnyx.use_telnyx(debug=True)  # Enable debug logging

# Create a Twilio client (which will use TeXML under the hood)
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

# Example 1: Make a call
# This will generate TeXML with a Dial element
call = client.calls.create(
    url='https://your-server.com/voice',
    to='+1234567890',
    from_='+1987654321'
)
print(f"Call SID: {call.sid}")

# Example 2: Send a message
# This will generate TeXML with a Say element
message = client.messages.create(
    body="Hello from TeXML!",
    to='+1234567890',
    from_='+1987654321'
)
print(f"Message SID: {message.sid}")

# Example 3: Play media
# This will generate TeXML with Play elements
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    media_url='https://example.com/audio.mp3'
)
print(f"Media Call SID: {call.sid}")

# Example 4: Multiple media URLs
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    media_url=[
        'https://example.com/audio1.mp3',
        'https://example.com/audio2.mp3'
    ]
)
print(f"Multiple Media Call SID: {call.sid}")