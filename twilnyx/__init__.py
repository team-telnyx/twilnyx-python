"""
Twilnyx - A proxy that redirects Twilio SDK calls to Telnyx's API.
"""

import twilio.http.http_client
from twilio.http.response import Response
import requests
import logging
from typing import Dict, Any, Optional, List, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twilnyx')

class TelnyxProxy(twilio.http.http_client.HttpClient):
    """Proxy that redirects Twilio HTTP calls to Telnyx."""
    
    def __init__(self, api_key: str, voice_profile_id: str, connection_id: Optional[str] = None):
        """
        Initialize the proxy.
        
        Args:
            api_key: Your Telnyx API key
            voice_profile_id: Your Telnyx Voice API Profile ID
            connection_id: Your Telnyx Call Control App ID (required for calls)
        """
        self.api_key = api_key
        self.voice_profile_id = voice_profile_id
        self.connection_id = connection_id
        self.base_url = "https://api.telnyx.com/v2"
    
    def request(self, method: str, url: str, params: Dict[str, str] = None, 
                data: Dict[str, Any] = None, headers: Dict[str, str] = None, 
                auth: Any = None, timeout: Any = None, **kwargs) -> Response:
        """
        Intercept Twilio's HTTP requests and redirect them to Telnyx.
        The user's webhook server handles all TwiML/call flow.
        """
        # Log the incoming request for debugging
        logger.debug(f"Intercepted Twilio request: {method} {url}")
        logger.debug(f"Data: {data}")
        
        # Determine the endpoint based on the URL pattern
        if 'Calls.json' in url or 'Calls' in url:
            # This is a call-related request
            endpoint = 'calls'
        elif 'Messages.json' in url or 'Messages' in url:
            # This is a message-related request
            endpoint = 'messages'
        else:
            # Extract the endpoint path from Twilio's URL
            path = url.split('/v2/')[-1] if '/v2/' in url else url.split('.com/')[-1]
            endpoint = path
            
        logger.debug(f"Mapped to Telnyx endpoint: {endpoint}")
        
        # Map Twilio parameters to Telnyx format
        telnyx_data = self._map_parameters(data or {})
        
        # Add required Telnyx parameters
        telnyx_data['voice_profile_id'] = self.voice_profile_id
        
        # Add connection_id if available and this is a call request
        if self.connection_id and endpoint == 'calls':
            telnyx_data['connection_id'] = self.connection_id
        elif endpoint == 'calls':
            # If no connection_id is provided, log a warning
            logger.warning("No connection_id provided. This may cause the call to fail.")
        
        # Log the outgoing request
        logger.debug(f"Sending to Telnyx: {method} {self.base_url}/{endpoint}")
        logger.debug(f"Data: {telnyx_data}")
        
        # Make request to Telnyx
        response = requests.request(
            method=method,
            url=f"{self.base_url}/{endpoint}",
            params=params,
            json=telnyx_data,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        # Log the response
        logger.debug(f"Telnyx response status: {response.status_code}")
        try:
            response_json = response.json()
            logger.debug(f"Telnyx response: {response_json}")
        except ValueError:
            logger.debug(f"Telnyx response (not JSON): {response.text}")
            response_json = {}
            
        # Convert Telnyx response to Twilio format
        converted_response = self._convert_response(response_json)
        logger.debug(f"Converted response: {converted_response}")
        
        return Response(
            response.status_code,
            converted_response
        )
    
    def _map_parameters(self, twilio_params: Dict[str, Any]) -> Dict[str, Any]:
        """Map Twilio parameters to Telnyx format."""
        mapping = {
            # Basic call parameters
            'To': 'to',
            'From': 'from',
            'Url': 'webhook_url',
            'Method': 'webhook_method',
            'StatusCallback': 'status_callback_url',
            'StatusCallbackMethod': 'status_callback_method',
            
            # Call control parameters
            'MachineDetection': 'answering_machine_detection',
            'Record': 'record_audio',
            'Timeout': 'timeout_secs',
            'CallerId': 'from',
            
            # Recording parameters
            'RecordingChannels': 'channels',
            'RecordingStatusCallback': 'recording_webhook_url',
            'RecordingStatusCallbackMethod': 'recording_webhook_method',
            
            # SMS parameters
            'Body': 'text',
            'MediaUrl': 'media_urls',
            
            # Common parameters
            'ApplicationSid': 'client_state',
            'FallbackUrl': 'fallback_url',
            'FallbackMethod': 'fallback_method'
        }
        
        # Special handling for certain parameters
        special_handling = {
            'MachineDetection': lambda v: 'detect' if v.lower() == 'enable' else v.lower(),
            'Record': lambda v: True if v.lower() == 'true' else False if v.lower() == 'false' else v,
            'Timeout': lambda v: int(v) if v.isdigit() else v
        }
        
        telnyx_params = {}
        for twilio_key, value in twilio_params.items():
            if value is None:
                continue
                
            telnyx_key = mapping.get(twilio_key, twilio_key.lower())
            
            # Apply special handling if needed
            if twilio_key in special_handling:
                value = special_handling[twilio_key](value)
                
            telnyx_params[telnyx_key] = value
            
        # Log the mapped parameters
        logger.debug(f"Mapped parameters: {telnyx_params}")
            
        return telnyx_params
    
    def _convert_response(self, telnyx_response: Dict[str, Any]) -> str:
        """Convert Telnyx response to Twilio format."""
        # Handle list responses
        if isinstance(telnyx_response.get('data', {}), list):
            data_list = telnyx_response.get('data', [])
            twilio_data_list = []
            
            for item in data_list:
                twilio_item = self._convert_single_item(item)
                twilio_data_list.append(twilio_item)
                
            # Convert to JSON string for proper parsing
            import json
            return json.dumps(twilio_data_list)
        
        # Handle single item responses
        data = telnyx_response.get('data', {})
        twilio_data = self._convert_single_item(data)
        
        # Convert to JSON string for proper parsing
        import json
        return json.dumps(twilio_data)
        
    def _convert_single_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single Telnyx response item to Twilio format."""
        # Map Telnyx fields to Twilio format
        twilio_data = {
            'sid': data.get('call_control_id') or data.get('id'),
            'status': self._map_status(data.get('state')),
            'to': data.get('to'),
            'from': data.get('from'),
            'direction': data.get('direction'),
            'date_created': data.get('created_at'),
            'date_updated': data.get('updated_at'),
            'duration': data.get('duration'),
            'price': data.get('cost'),
            'price_unit': data.get('currency'),
            'answered_by': data.get('answering_machine_detection'),
            'recording_url': data.get('recording_urls', [None])[0],
            'recording_status': data.get('recording_state'),
            
            # Additional fields for SMS
            'body': data.get('text'),
            'num_media': len(data.get('media_urls', [])),
            'media_url': data.get('media_urls', [None])[0],
            
            # Additional fields for call control
            'queue_time': data.get('queue_time'),
            'trunk_name': data.get('trunk_name'),
            'client_state': data.get('client_state'),
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in twilio_data.items() if v is not None}
    
    def _map_status(self, telnyx_status: Optional[str]) -> str:
        """Map Telnyx call states to Twilio status values."""
        status_map = {
            # Call states
            'queued': 'queued',
            'ringing': 'ringing',
            'answered': 'in-progress',
            'bridging': 'in-progress',
            'bridged': 'in-progress',
            'completed': 'completed',
            'busy': 'busy',
            'failed': 'failed',
            'no-answer': 'no-answer',
            'canceled': 'canceled',
            'hangup': 'completed',
            'initiated': 'queued',
            'leaving-bridge': 'in-progress',
            'transferring': 'in-progress',
            
            # Message states
            'sent': 'sent',
            'delivered': 'delivered',
            'sending': 'queued',
            'queued': 'queued',
            'failed': 'failed',
            'received': 'received',
            'rejected': 'failed',
            'undelivered': 'undelivered'
        }
        
        # Log the status mapping
        mapped_status = status_map.get(telnyx_status or '', 'unknown')
        logger.debug(f"Mapped status: {telnyx_status} -> {mapped_status}")
        
        return mapped_status

def set_log_level(level: Union[int, str]):
    """
    Set the logging level for the Twilnyx package.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, 'DEBUG', 'INFO')
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)

def use_telnyx(api_key: str, voice_profile_id: str, connection_id: Optional[str] = None, debug: bool = False):
    """
    Monkey-patch Twilio's SDK to use Telnyx instead.
    
    Args:
        api_key: Your Telnyx API key
        voice_profile_id: Your Telnyx Voice API Profile ID
        connection_id: Your Telnyx Call Control App ID (required for calls)
        debug: If True, enable debug logging
    """
    # Set debug logging if requested
    if debug:
        set_log_level(logging.DEBUG)
        logger.debug("Debug logging enabled")
    # Replace Twilio's HTTP client with our proxy
    original_client = twilio.http.http_client.HttpClient
    twilio.http.http_client.HttpClient = lambda: TelnyxProxy(api_key, voice_profile_id, connection_id)
    
    # Also patch TwilioHttpClient since that's what the Client class uses
    from twilio.http.http_client import TwilioHttpClient
    
    # Save the original __init__ method
    original_init = TwilioHttpClient.__init__
    
    # Define a new __init__ method that uses our proxy
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Replace the internal http_client with our proxy
        self.proxy = TelnyxProxy(api_key, voice_profile_id, connection_id)
        
    # Replace the request method to use our proxy
    def new_request(self, method, url, params=None, data=None, headers=None, auth=None, timeout=None, **kwargs):
        # Filter out any kwargs that our proxy doesn't support
        return self.proxy.request(method, url, params, data, headers, auth, timeout)
        
    # Apply the patches
    TwilioHttpClient.__init__ = new_init
    TwilioHttpClient.request = new_request

__all__ = ['use_telnyx', 'set_log_level', 'TelnyxProxy']