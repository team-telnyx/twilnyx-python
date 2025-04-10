"""
Example showing how to use Twilnyx to redirect Twilio calls to Telnyx.
Your webhook server handles all the call flow logic.
"""

# First, import and use your normal Twilio code
from twilio.rest import Client

# Then add Twilnyx to redirect to Telnyx
import twilnyx
twilnyx.use_telnyx(
    api_key='YOUR_TELNYX_API_KEY',
    voice_profile_id='YOUR_VOICE_PROFILE_ID'  # From Telnyx Portal > Voice > API Profiles
)

# Now just use Twilio's SDK normally!
# All calls will automatically go to Telnyx instead
client = Client('dummy', 'dummy')  # Credentials don't matter

# Make a call - it uses your webhook server for TwiML
call = client.calls.create(
    url='https://your-server.com/voice',  # Your webhook that returns TwiML
    to='+1234567890',
    from_='+1987654321'
)

print(f"Call initiated!")
print(f"SID: {call.sid}")  # This is Telnyx's call_control_id
print(f"To: {call.to}")
print(f"Status: {call.status}")

# All other Twilio operations work too
calls = client.calls.list(limit=20)
for call in calls:
    print(f"Call from {call.from_} to {call.to}: {call.status}")

# Advanced features work as well
call = client.calls.get('some_call_sid')
call.update(status='completed')  # Hangup