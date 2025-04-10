# Twilnyx

A proxy that redirects Twilio SDK calls to use Telnyx's API. Keep using your existing Twilio code and webhook server - just add two lines to use Telnyx instead!

## Installation

```bash
pip install twilnyx
```

## Usage

Your existing Twilio code:
```python
from twilio.rest import Client

client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

call = client.calls.create(
    url='https://your-server.com/voice',  # Your webhook server
    to='+1234567890',
    from_='+1987654321'
)
```

To use Telnyx instead, just add:
```python
# Add these two lines at the start of your code
import twilnyx
twilnyx.use_telnyx(
    api_key='YOUR_TELNYX_API_KEY',
    voice_profile_id='YOUR_VOICE_PROFILE_ID'  # From Telnyx Portal > Voice > API Profiles
)

# Then use your existing Twilio code as-is!
from twilio.rest import Client
...
```

## How It Works

1. **Basic Flow**:
   ```
   Your Code -> Twilio SDK -> Twilnyx Proxy -> Telnyx API
                                    |
                                    v
                             Parameter Mapping
                             Add Voice Profile
                             Convert Response
   ```

2. **Complete Flow**:
   ```
   +-------------+    +------------+    +-------------+    +-----------+
   |  Your Code  |    |Twilio SDK |    |Twilnyx Proxy|    |Telnyx API |
   |             |--->|           |--->|             |--->|           |
   +-------------+    +------------+    +-------------+    +-----------+
                                            |
                                            v
                                    +---------------+
                                    | Map Params    |
                                    | Add Profile   |
                                    | Map Response  |
                                    +---------------+
   ```

3. **Webhook Flow**:
   ```
   +-------------+    +------------+    +------------+
   |  Your App   |    |Telnyx API |    |Your Server |
   |client.calls |    |           |    |  /voice    |
   |             |--->|           |--->|            |
   |             |    |           |    |            |
   |             |    |           |<---|   TwiML    |
   +-------------+    +------------+    +------------+
   ```

4. **Parameter Mapping**:
   ```python
   # Twilio format
   {
       'To': '+1234567890',
       'From': '+1987654321',
       'Url': 'https://your-server.com/voice'
   }
   
   # Converted to Telnyx format
   {
       'to': '+1234567890',
       'from': '+1987654321',
       'webhook_url': 'https://your-server.com/voice',
       'voice_profile_id': 'your_profile_id'  # Added automatically
   }
   ```

5. **Response Conversion**:
   ```python
   # Telnyx response
   {
       'call_control_id': 'xyz',
       'state': 'ringing'
   }
   
   # Converted to Twilio format
   {
       'sid': 'xyz',
       'status': 'ringing'
   }
   ```

## Required Setup

1. **Telnyx Voice Profile** (Required):
   - Create in Telnyx Portal > Voice > API Profiles
   - Used for outbound calling configuration
   - Pass the ID to `use_telnyx()`

2. **Your Webhook Server**:
   - Keep using your existing webhook server
   - It should return TwiML just like with Twilio
   - No changes needed to your webhooks

## Features

- Uses your existing Twilio code
- Uses your existing webhook server
- No code changes needed
- Automatic parameter mapping
- Proper response conversion

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License