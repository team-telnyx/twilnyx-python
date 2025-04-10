"""Tests for the Twilnyx proxy."""

import pytest
from twilnyx import use_telnyx
from unittest.mock import patch, MagicMock

def test_parameter_mapping():
    """Test that Twilio parameters are correctly mapped to Telnyx format."""
    from twilnyx import TelnyxProxy
    
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    twilio_params = {
        'To': '+1234567890',
        'From': '+1987654321',
        'Url': 'https://example.com/voice'
    }
    
    telnyx_params = proxy._map_parameters(twilio_params)
    
    assert telnyx_params['to'] == '+1234567890'
    assert telnyx_params['from'] == '+1987654321'
    assert telnyx_params['webhook_url'] == 'https://example.com/voice'

def test_response_mapping():
    """Test that Telnyx responses are correctly mapped to Twilio format."""
    from twilnyx import TelnyxProxy
    
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    telnyx_response = {
        'data': {
            'call_control_id': 'test_id',
            'state': 'ringing',
            'to': '+1234567890',
            'from': '+1987654321'
        }
    }
    
    twilio_response = proxy._convert_response(telnyx_response)
    response_dict = eval(twilio_response)  # Convert string back to dict
    
    assert response_dict['sid'] == 'test_id'
    assert response_dict['status'] == 'ringing'
    assert response_dict['to'] == '+1234567890'
    assert response_dict['from'] == '+1987654321'

@patch('requests.request')
def test_proxy_request(mock_request):
    """Test that requests are properly proxied to Telnyx."""
    from twilnyx import TelnyxProxy
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': {
            'call_control_id': 'test_id',
            'state': 'ringing'
        }
    }
    mock_request.return_value = mock_response
    
    # Create proxy and make request
    proxy = TelnyxProxy('test_key', 'test_profile')
    response = proxy.request(
        'POST',
        'https://api.twilio.com/2010-04-01/Accounts/AC123/Calls.json',
        data={
            'To': '+1234567890',
            'From': '+1987654321',
            'Url': 'https://example.com/voice'
        }
    )
    
    # Verify request was made correctly
    mock_request.assert_called_once()
    args = mock_request.call_args
    
    assert args[1]['headers']['Authorization'] == 'Bearer test_key'
    assert args[1]['json']['voice_profile_id'] == 'test_profile'
    assert args[1]['json']['to'] == '+1234567890'

def test_use_telnyx():
    """Test the use_telnyx function properly sets up the proxy."""
    from twilnyx import use_telnyx, TelnyxProxy
    import twilio.http.http_client
    
    # Use the proxy
    use_telnyx('test_key', 'test_profile')
    
    # Create a client instance
    client = twilio.http.http_client.HttpClient()
    
    # Verify it's our proxy
    assert isinstance(client, TelnyxProxy)
    assert client.api_key == 'test_key'
    assert client.voice_profile_id == 'test_profile'

def test_empty_response():
    """Test handling of empty responses."""
    from twilnyx import TelnyxProxy
    
    proxy = TelnyxProxy('test_key', 'test_profile')
    response = proxy._convert_response({})
    response_dict = eval(response)  # Convert string back to dict
    
    # Empty response should still have all fields with None values
    assert response_dict['sid'] is None
    assert response_dict['status'] == 'unknown'
    assert response_dict['to'] is None
    assert response_dict['from'] is None

def test_status_mapping():
    """Test all status mappings."""
    from twilnyx import TelnyxProxy
    
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    # Test all defined statuses
    assert proxy._map_status('queued') == 'queued'
    assert proxy._map_status('ringing') == 'ringing'
    assert proxy._map_status('answered') == 'in-progress'
    assert proxy._map_status('completed') == 'completed'
    assert proxy._map_status('busy') == 'busy'
    assert proxy._map_status('failed') == 'failed'
    assert proxy._map_status('no-answer') == 'no-answer'
    assert proxy._map_status('canceled') == 'canceled'
    
    # Test unknown status
    assert proxy._map_status('unknown_status') == 'unknown'
    assert proxy._map_status(None) == 'unknown'