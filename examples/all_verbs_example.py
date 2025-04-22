"""
Example showing how to use Twilnyx with all TwiML verbs.
"""

import twilnyx
import json
import os
from twilio.rest import Client

# Initialize Twilnyx with TeXML mode and use the full mappings
twilnyx.use_telnyx(debug=True)

# Load the full mappings with all TwiML verbs
full_mappings_path = os.path.join(os.path.dirname(twilnyx.__file__), 'mappings_full.json')
twilnyx.load_custom_mappings(full_mappings_path)

# Create a Twilio client
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

# Example 1: Basic Call with Dial
print("\n1. Basic Call with Dial")
call = client.calls.create(
    url='https://your-server.com/voice',
    to='+1234567890',
    from_='+1987654321'
)
print(f"Call SID: {call.sid}")

# Example 2: Play Media
print("\n2. Play Media")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    media_url='https://example.com/audio.mp3'
)
print(f"Media Call SID: {call.sid}")

# Example 3: Say Text
print("\n3. Say Text")
# We can use the verb parameter to explicitly request a specific verb
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='say',  # Explicitly request Say verb
    text='Hello, this is a text-to-speech message'
)
print(f"Say Call SID: {call.sid}")

# Example 4: Gather DTMF Input
print("\n4. Gather DTMF Input")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='gather',
    finish_on_key='#',
    num_digits=4,
    prompt_text='Please enter your 4-digit PIN followed by the pound key'
)
print(f"Gather Call SID: {call.sid}")

# Example 5: Record
print("\n5. Record")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='record',
    max_length=30,
    play_beep=True,
    timeout_secs=5,
    finish_on_key='#',
    transcribe=True
)
print(f"Record Call SID: {call.sid}")

# Example 6: Hangup
print("\n6. Hangup")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='hangup'
)
print(f"Hangup Call SID: {call.sid}")

# Example 7: Redirect
print("\n7. Redirect")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='redirect',
    redirect_url='https://example.com/new-instructions'
)
print(f"Redirect Call SID: {call.sid}")

# Example 8: Reject
print("\n8. Reject")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='reject',
    reason='busy'
)
print(f"Reject Call SID: {call.sid}")

# Example 9: Pause
print("\n9. Pause")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='pause',
    length=5
)
print(f"Pause Call SID: {call.sid}")

# Example 10: Enqueue
print("\n10. Enqueue")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='enqueue',
    queue_name='support'
)
print(f"Enqueue Call SID: {call.sid}")

# Example 11: Leave Queue
print("\n11. Leave Queue")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='leave'
)
print(f"Leave Call SID: {call.sid}")

# Example 12: Connect to Room
print("\n12. Connect to Room")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='connect',
    room_name='my-conference-room'
)
print(f"Connect Call SID: {call.sid}")

# Example 13: Stream
print("\n13. Stream")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='stream',
    webhook_url='wss://example.com/stream',
    track='both'
)
print(f"Stream Call SID: {call.sid}")

# Example 14: Transcription
print("\n14. Transcription")
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='transcription',
    transcription_type='auto',
    transcription_language='en',
    transcription_callback_url='https://example.com/transcription-callback'
)
print(f"Transcription Call SID: {call.sid}")

print("\nAll examples completed. Check the debug logs for the generated TeXML.")