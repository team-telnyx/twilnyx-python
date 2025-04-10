"""
Twilnyx - A proxy that redirects Twilio SDK calls to Telnyx's API.
"""

import twilio.http.http_client
from twilio.http.response import Response
import requests
from typing import Dict, Any, Optional

class TelnyxProxy(twilio.http.http_client.HttpClient):
    """Proxy that redirects Twilio HTTP calls to Telnyx."""
    
    def __init__(self, api_key: str, voice_profile_id: str):
        """
        Initialize the proxy.
        
        Args:
            api_key: Your Telnyx API key
            voice_profile_id: Your Telnyx Voice API Profile ID
        """
        self.api_key = api_key
        self.voice_profile_id = voice_profile_id
        self.base_url = "https://api.telnyx.com/v2"
    
    def request(self, method: str, url: str, params: Dict[str, str] = None, 
                data: Dict[str, Any] = None, headers: Dict[str, str] = None, 
                auth: Any = None, timeout: Any = None) -> Response:
        """
        Intercept Twilio's HTTP requests and redirect them to Telnyx.
        The user's webhook server handles all TwiML/call flow.
        """
        # Extract the endpoint path from Twilio's URL
        path = url.split('/v2/')[-1] if '/v2/' in url else url.split('.com/')[-1]
        
        # Map Twilio parameters to Telnyx format
        telnyx_data = self._map_parameters(data or {})
        
        # Add required Telnyx parameters
        telnyx_data['voice_profile_id'] = self.voice_profile_id
        
        # Make request to Telnyx
        response = requests.request(
            method=method,
            url=f"{self.base_url}/{path}",
            params=params,
            json=telnyx_data,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        # Convert Telnyx response to Twilio format
        return Response(
            response.status_code,
            self._convert_response(response.json())
        )
    
    def _map_parameters(self, twilio_params: Dict[str, Any]) -> Dict[str, Any]:
        """Map Twilio parameters to Telnyx format."""
        mapping = {
            'To': 'to',
            'From': 'from',
            'Url': 'webhook_url',
            'Method': 'webhook_method',
            'StatusCallback': 'status_callback_url',
            'StatusCallbackMethod': 'status_callback_method',
            'MachineDetection': 'answering_machine_detection',
            'Record': 'record_audio',
            'Timeout': 'timeout_secs',
            'CallerId': 'from',
            'RecordingChannels': 'channels',
            'RecordingStatusCallback': 'recording_webhook_url'
        }
        
        telnyx_params = {}
        for twilio_key, value in twilio_params.items():
            telnyx_key = mapping.get(twilio_key, twilio_key.lower())
            telnyx_params[telnyx_key] = value
            
        return telnyx_params
    
    def _convert_response(self, telnyx_response: Dict[str, Any]) -> str:
        """Convert Telnyx response to Twilio format."""
        data = telnyx_response.get('data', {})
        
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
        }
        
        return str(twilio_data)
    
    def _map_status(self, telnyx_status: Optional[str]) -> str:
        """Map Telnyx call states to Twilio status values."""
        status_map = {
            'queued': 'queued',
            'ringing': 'ringing',
            'answered': 'in-progress',
            'completed': 'completed',
            'busy': 'busy',
            'failed': 'failed',
            'no-answer': 'no-answer',
            'canceled': 'canceled'
        }
        return status_map.get(telnyx_status or '', 'unknown')

def use_telnyx(api_key: str, voice_profile_id: str):
    """
    Monkey-patch Twilio's SDK to use Telnyx instead.
    
    Args:
        api_key: Your Telnyx API key
        voice_profile_id: Your Telnyx Voice API Profile ID
    """
    # Replace Twilio's HTTP client with our proxy
    twilio.http.http_client.HttpClient = lambda: TelnyxProxy(api_key, voice_profile_id)

__all__ = ['use_telnyx']