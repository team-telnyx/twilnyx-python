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

To use TeXML, just add:
```python
# Add these two lines at the start of your code
import twilnyx
twilnyx.use_telnyx(debug=True)  # Set to True for detailed logging

# Then use your existing Twilio code as-is!
from twilio.rest import Client
...
```

### TeXML Mode

This package uses TeXML exclusively for all requests. No Telnyx API credentials are required, as all requests are handled via TeXML responses.

```python
# Simple usage with TeXML - loads full mappings by default
import twilnyx
twilnyx.use_telnyx()  # No credentials needed, supports all TwiML verbs

# Your existing Twilio code works as-is
from twilio.rest import Client
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')
```

### Custom Mappings

You can customize the parameter mappings and TeXML templates by providing your own JSON file:

```python
import twilnyx

# Option 1: Load custom mappings at initialization
twilnyx.use_telnyx(custom_mappings_file='my_mappings.json')

# Option 2: Load custom mappings at any time
twilnyx.load_custom_mappings('my_mappings.json')

# View current mappings
print(twilnyx.MAPPINGS)
```

Example custom mappings file:
```json
{
  "parameter_mappings": {
    "To": "destination",
    "From": "source",
    "Body": "message_content"
  },
  "texml_templates": {
    "call": {
      "element": "CustomDial",
      "attributes": ["callerId"],
      "children": [
        {
          "element": "Number",
          "content": "destination"
        }
      ]
    }
  }
}
```

### Using All TwiML Verbs

The package includes a full mapping for all TwiML verbs and loads it by default. You can use any TwiML verb by specifying it in the 'verb' parameter:

```python
import twilnyx

# Initialize Twilnyx - full mappings are loaded by default
twilnyx.use_telnyx(debug=True)

# Now you can use any TwiML verb by specifying it in the 'verb' parameter
from twilio.rest import Client
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

# Example: Gather DTMF input
call = client.calls.create(
    to='+1234567890',
    from_='+1987654321',
    verb='gather',  # Explicitly request Gather verb
    finish_on_key='#',
    num_digits=4,
    prompt_text='Please enter your PIN'
)
```

See the `examples/all_verbs_example.py` file for examples of using all supported TwiML verbs, including:
- `<Connect>`, `<Dial>`, `<Enqueue>`, `<Gather>`, `<Hangup>`, `<Leave>`
- `<Pause>`, `<Play>`, `<Record>`, `<Redirect>`, `<Refer>`
- `<Reject>`, `<Say>`, `<Siprec>`, `<Stream>`, `<Transcription>`

## How It Works

1. **Basic Flow**:
   ```
   Your Code -> Twilio SDK -> Twilnyx Proxy -> TeXML Response
                                    |
                                    v
                             Parameter Mapping
                             TeXML Generation
   ```

2. **Complete Flow**:
   ```
   +-------------+    +------------+    +-------------+    +-----------+
   |  Your Code  |    |Twilio SDK |    |Twilnyx Proxy|    |   TeXML   |
   |             |--->|           |--->|             |--->| <Response>|
   +-------------+    +------------+    +-------------+    +-----------+
                                            |
                                            v
                                    +---------------+
                                    | Map Params    |
                                    | Generate XML  |
                                    +---------------+
   ```

3. **TeXML Flow**:
   ```
   +-------------+    +------------+    +-------------+    +-----------+
   |  Your App   |    |Twilio SDK |    |Twilnyx Proxy|    |   TeXML   |
   |client.calls |    |           |    |             |    | <Response>|
   |             |--->|           |--->|             |--->|  <Dial>   |
   |             |    |           |    |             |    |  <Number> |
   |             |    |           |    |             |    |  <Play>   |
   +-------------+    +------------+    +-------------+    +-----------+
   ```

4. **SMS Flow with TeXML**:
   ```
   +-------------+    +------------+    +-------------+    +-----------+
   |  Your Code  |    |Twilio SDK |    |Twilnyx Proxy|    |   TeXML   |
   |client.msgs  |--->|           |--->|             |--->| <Response>|
   +-------------+    +------------+    +-------------+    |   <Say>  |
                                                           +-----------+
   ```

5. **Parameter Mapping**:
   ```python
   # Twilio format
   {
       'To': '+1234567890',
       'From': '+1987654321',
       'Url': 'https://your-server.com/voice',
       'MediaUrl': 'https://example.com/audio.mp3'  # Media URL for TeXML
   }
   
   # Converted to Telnyx format
   {
       'to': '+1234567890',
       'from': '+1987654321',
       'webhook_url': 'https://your-server.com/voice',
       'voice_profile_id': 'your_profile_id',  # Added automatically
       'media_urls': 'https://example.com/audio.mp3'  # Used for TeXML generation
   }
   ```

6. **Response Conversion**:
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

1. **No Telnyx API Credentials Required**:
   - This version uses TeXML exclusively
   - No API keys or credentials needed
   - Just import and use

2. **TeXML Support**:
   - All requests are converted to TeXML responses
   - Supports calls, messages, and media playback
   - Compatible with Telnyx's XML format

3. **Usage with Existing Code**:
   - Keep using your existing Twilio code
   - No changes needed to your application logic
   - Just add the `twilnyx.use_telnyx()` call

## Features

- Uses your existing Twilio code
- Uses your existing webhook server
- No code changes needed
- Automatic parameter mapping
- Proper response conversion
- Detailed logging for debugging
- Support for calls and messages
- Error handling and reporting
- Complete TeXML support for all TwiML verbs:
  - `<Connect>`, `<Dial>`, `<Enqueue>`, `<Gather>`, `<Hangup>`, `<Leave>`
  - `<Pause>`, `<Pay>`, `<Play>`, `<Record>`, `<Redirect>`, `<Refer>`
  - `<Reject>`, `<Say>`, `<Siprec>`, `<Stream>`, `<Transcription>`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License