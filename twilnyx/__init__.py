"""
Twilnyx - A proxy that redirects Twilio SDK calls to TeXML.
"""

import twilio.http.http_client
from twilio.http.response import Response
import requests
import logging
import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twilnyx')

# Load mappings from JSON file
def load_mappings():
    """Load parameter and status mappings from the JSON file."""
    mappings_path = os.path.join(os.path.dirname(__file__), 'mappings.json')
    try:
        with open(mappings_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading mappings: {e}")
        # Provide default empty mappings as fallback
        return {
            "parameter_mappings": {},
            "special_handling": {},
            "status_mappings": {"call_states": {}, "message_states": {}},
            "texml_templates": {}
        }

# Global mappings
MAPPINGS = load_mappings()

class TelnyxProxy(twilio.http.http_client.HttpClient):
    """Proxy that redirects Twilio HTTP calls to TeXML."""
    
    def __init__(self, api_key: str = None, voice_profile_id: str = None, connection_id: Optional[str] = None):
        """
        Initialize the proxy.
        
        Args:
            api_key: Your Telnyx API key (not used with TeXML approach)
            voice_profile_id: Your Telnyx Voice API Profile ID (not used with TeXML approach)
            connection_id: Your Telnyx Call Control App ID (not used with TeXML approach)
        """
        # These parameters are kept for backward compatibility but are not used
        self.api_key = api_key
        self.voice_profile_id = voice_profile_id
        self.connection_id = connection_id
    
    def request(self, method: str, url: str, params: Dict[str, str] = None, 
                data: Dict[str, Any] = None, headers: Dict[str, str] = None, 
                auth: Any = None, timeout: Any = None, **kwargs) -> Response:
        """
        Intercept Twilio's HTTP requests and generate TeXML responses.
        All requests are handled via TeXML instead of Telnyx's call control API.
        """
        # Log the incoming request for debugging
        logger.debug(f"Intercepted Twilio request: {method} {url}")
        logger.debug(f"Data: {data}")
        
        # Map Twilio parameters to Telnyx format
        telnyx_data = self._map_parameters(data or {})
        
        # Handle 'Body' parameter for SMS
        if data and 'Body' in data:
            telnyx_data['text'] = data['Body']
        
        # Generate TeXML response based on the request type
        xml_response = self._generate_texml_response(telnyx_data)
        logger.debug(f"Generated TeXML response: {xml_response}")
        
        # Return the TeXML response
        return Response(200, xml_response)
        

    
    def _map_parameters(self, twilio_params: Dict[str, Any]) -> Dict[str, Any]:
        """Map Twilio parameters to Telnyx format using mappings from JSON file."""
        # Get parameter mappings from the loaded JSON
        mapping = MAPPINGS.get("parameter_mappings", {})
        
        telnyx_params = {}
        for twilio_key, value in twilio_params.items():
            if value is None:
                continue
                
            # Get the mapped key or use lowercase of original key as fallback
            telnyx_key = mapping.get(twilio_key, twilio_key.lower())
            
            # Apply special handling if defined in mappings
            special_handling_info = MAPPINGS.get("special_handling", {}).get(twilio_key)
            if special_handling_info:
                if special_handling_info.get("type") == "boolean":
                    # Convert string 'true'/'false' to boolean
                    if isinstance(value, str) and value.lower() == 'true':
                        value = True
                    elif isinstance(value, str) and value.lower() == 'false':
                        value = False
                elif special_handling_info.get("type") == "integer":
                    # Convert digit strings to integers
                    if isinstance(value, str) and value.isdigit():
                        value = int(value)
                elif special_handling_info.get("type") == "function":
                    # Apply specific transformations
                    if twilio_key == "MachineDetection" and isinstance(value, str):
                        value = 'detect' if value.lower() == 'enable' else value.lower()
            
            telnyx_params[telnyx_key] = value
            
        # Log the mapped parameters
        logger.debug(f"Mapped parameters: {telnyx_params}")
            
        return telnyx_params
    
    def _generate_texml_response(self, telnyx_data: Dict[str, Any]) -> str:
        """
        Generate a TeXML response based on the request parameters.
        Uses the templates defined in the mappings.json file.
        Supports all TwiML verbs through the mappings configuration.
        """
        # Create TeXML Response element
        response = ET.Element("Response")
        
        # Get templates from mappings
        templates = MAPPINGS.get("texml_templates", {})
        
        # Determine which template to use based on the data
        template_key = self._determine_template(telnyx_data)
        logger.debug(f"Using template: {template_key}")
        
        if template_key and template_key in templates:
            # Get the template for this type of request
            template = templates[template_key]
            
            # Create the main element
            element_name = template.get("element")
            if not element_name:
                logger.warning(f"No element name found in template {template_key}")
                return ET.tostring(response, encoding="utf-8").decode("utf-8")
                
            main_element = ET.SubElement(response, element_name)
            
            # Set attributes on the main element
            for attr in template.get("attributes", []):
                # Convert attribute names to their mapped parameter names
                attr_field = attr.lower().replace("url", "webhook_url").replace("method", "webhook_method")
                if attr_field in telnyx_data:
                    main_element.set(attr, str(telnyx_data[attr_field]))
            
            # Set content if specified
            content_field = template.get("content")
            if content_field and content_field in telnyx_data:
                # Handle lists (like media_urls)
                if isinstance(telnyx_data[content_field], list):
                    # For lists, we might need to create multiple elements or handle specially
                    if template_key == "media":
                        # For media, create multiple Play elements
                        for url in telnyx_data[content_field]:
                            play = ET.SubElement(response, element_name)
                            play.text = url
                            # Set attributes on each Play element
                            for attr in template.get("attributes", []):
                                attr_field = attr.lower().replace("url", "webhook_url").replace("method", "webhook_method")
                                if attr_field in telnyx_data:
                                    play.set(attr, str(telnyx_data[attr_field]))
                        # Remove the main element since we created individual ones
                        response.remove(main_element)
                    else:
                        # Default list handling - use first item
                        main_element.text = str(telnyx_data[content_field][0])
                else:
                    main_element.text = str(telnyx_data[content_field])
            
            # Add children elements from template
            for child in template.get("children", []):
                child_element_name = child.get("element")
                if not child_element_name:
                    continue
                    
                child_element = ET.SubElement(main_element, child_element_name)
                
                # Set content if specified
                child_content_field = child.get("content")
                if child_content_field and child_content_field in telnyx_data:
                    child_element.text = str(telnyx_data[child_content_field])
                
                # Set attributes on child element
                for attr in child.get("attributes", []):
                    attr_field = attr.lower().replace("url", "webhook_url").replace("method", "webhook_method")
                    if attr_field in telnyx_data:
                        child_element.set(attr, str(telnyx_data[attr_field]))
            
            logger.debug(f"Added {element_name} element with template {template_key}")
        else:
            logger.warning(f"No template found for data: {telnyx_data}")
        
        # Convert to XML string
        xml_str = ET.tostring(response, encoding="utf-8").decode("utf-8")
        return xml_str
        
    def _determine_template(self, telnyx_data: Dict[str, Any]) -> Optional[str]:
        """
        Determine which template to use based on the data.
        """
        # Check for specific verb indicators in the data
        if 'verb' in telnyx_data:
            # If a specific verb is requested, use that template
            verb = telnyx_data['verb'].lower()
            
            # Special handling for Connect verb which doesn't have a direct equivalent in Telnyx
            if verb == 'connect':
                # Check if we're connecting to a conference
                if 'room_name' in telnyx_data or 'conference_name' in telnyx_data:
                    return "conference"
                # Default to a basic call if we can't determine the specific Connect type
                return "call"
                
            return verb
            
        # Otherwise determine based on data patterns
        if 'media_urls' in telnyx_data and telnyx_data['media_urls']:
            return "media"
        elif 'to' in telnyx_data and 'from' in telnyx_data:
            if 'record_audio' in telnyx_data and telnyx_data['record_audio']:
                return "record"
            return "call"
        elif 'text' in telnyx_data:
            return "message"
        elif 'finish_on_key' in telnyx_data or 'num_digits' in telnyx_data:
            return "gather"
        elif 'queue_name' in telnyx_data:
            return "enqueue"
        elif 'redirect_url' in telnyx_data:
            return "redirect"
        elif 'reason' in telnyx_data:
            return "reject"
        elif 'length' in telnyx_data:
            return "pause"
        
        # Default to a basic response if no specific template can be determined
        return None
        
    def _create_twilio_response(self, call_id: str = None) -> Dict[str, Any]:
        """Create a simple Twilio-compatible response."""
        import uuid
        
        # Generate a random SID if none provided
        sid = call_id or f"TL{uuid.uuid4().hex[:18]}"
        
        # Create a basic response that mimics Twilio's format
        twilio_data = {
            'sid': sid,
            'status': 'queued',
            'date_created': self._get_iso_timestamp(),
            'date_updated': self._get_iso_timestamp(),
        }
        
        return twilio_data
    
    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def set_log_level(level: Union[int, str]):
    """
    Set the logging level for the Twilnyx package.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, 'DEBUG', 'INFO')
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)

def load_custom_mappings(mappings_file: str) -> Dict[str, Any]:
    """
    Load custom mappings from a JSON file.
    
    Args:
        mappings_file: Path to the JSON file containing custom mappings
        
    Returns:
        Dict containing the loaded mappings
    """
    global MAPPINGS
    try:
        with open(mappings_file, 'r') as f:
            custom_mappings = json.load(f)
            MAPPINGS = custom_mappings
            logger.info(f"Loaded custom mappings from {mappings_file}")
            return custom_mappings
    except Exception as e:
        logger.error(f"Error loading custom mappings: {e}")
        return MAPPINGS

def use_telnyx(api_key: str = None, voice_profile_id: str = None, connection_id: Optional[str] = None, 
               debug: bool = False, custom_mappings_file: Optional[str] = None):
    """
    Monkey-patch Twilio's SDK to use TeXML instead.
    
    Args:
        api_key: Your Telnyx API key (not used with TeXML approach)
        voice_profile_id: Your Telnyx Voice API Profile ID (not used with TeXML approach)
        connection_id: Your Telnyx Call Control App ID (not used with TeXML approach)
        debug: If True, enable debug logging
        custom_mappings_file: Optional path to a JSON file containing custom mappings
    """
    # Set debug logging if requested
    if debug:
        set_log_level(logging.DEBUG)
        logger.debug("Debug logging enabled")
        
    # Load custom mappings if provided
    if custom_mappings_file:
        load_custom_mappings(custom_mappings_file)
        
    # Log that we're using TeXML only
    logger.info("Using TeXML for all Twilio requests - Telnyx API credentials are not used")
    
    # Replace Twilio's HTTP client with our proxy
    original_client = twilio.http.http_client.HttpClient
    twilio.http.http_client.HttpClient = lambda: TelnyxProxy()
    
    # Also patch TwilioHttpClient since that's what the Client class uses
    from twilio.http.http_client import TwilioHttpClient
    
    # Save the original __init__ method
    original_init = TwilioHttpClient.__init__
    
    # Define a new __init__ method that uses our proxy
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Replace the internal http_client with our proxy
        self.proxy = TelnyxProxy()
        
    # Replace the request method to use our proxy
    def new_request(self, method, url, params=None, data=None, headers=None, auth=None, timeout=None, **kwargs):
        # Filter out any kwargs that our proxy doesn't support
        return self.proxy.request(method, url, params, data, headers, auth, timeout)
        
    # Apply the patches
    TwilioHttpClient.__init__ = new_init
    TwilioHttpClient.request = new_request

__all__ = ['use_telnyx', 'set_log_level', 'TelnyxProxy', 'load_custom_mappings', 'MAPPINGS']