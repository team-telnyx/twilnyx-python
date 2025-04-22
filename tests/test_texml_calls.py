"""Tests for TeXML call functionality in Twilnyx."""

import pytest
import xml.etree.ElementTree as ET
from twilnyx import TelnyxProxy
from twilio.http.response import Response

def test_call_texml_generation():
    """Test that TeXML responses are generated correctly for call requests."""
    proxy = TelnyxProxy()
    
    # Test with basic call parameters
    telnyx_data = {
        'to': '+1234567890',
        'from': '+1987654321',
        'webhook_url': 'https://example.com/voice'
    }
    xml_str = proxy._generate_texml_response(telnyx_data)
    
    # Parse the XML string
    root = ET.fromstring(xml_str)
    
    # Verify structure
    assert root.tag == 'Response'
    dial_elements = root.findall('Dial')
    assert len(dial_elements) == 1
    
    # Check Dial attributes
    dial = dial_elements[0]
    assert dial.get('callerId') == '+1987654321'
    
    # Check Number element
    number_elements = dial.findall('Number')
    assert len(number_elements) == 1
    assert number_elements[0].text == '+1234567890'
    assert number_elements[0].get('url') == 'https://example.com/voice'

def test_call_request_handling():
    """Test that call requests are handled with TeXML responses."""
    proxy = TelnyxProxy()
    
    # Create a request with call parameters
    response = proxy.request(
        'POST',
        'https://api.twilio.com/2010-04-01/Accounts/AC123/Calls.json',
        data={
            'To': '+1234567890',
            'From': '+1987654321',
            'Url': 'https://example.com/voice'
        }
    )
    
    # Verify response is XML
    assert response.status_code == 200
    
    # Parse the XML string
    root = ET.fromstring(response.text)
    
    # Verify structure
    assert root.tag == 'Response'
    dial_elements = root.findall('Dial')
    assert len(dial_elements) == 1
    
    # Check Number element
    number_elements = dial_elements[0].findall('Number')
    assert len(number_elements) == 1
    assert number_elements[0].text == '+1234567890'

def test_sms_texml_generation():
    """Test that TeXML responses are generated correctly for SMS requests."""
    proxy = TelnyxProxy()
    
    # Test with SMS parameters
    telnyx_data = {
        'to': '+1234567890',
        'from': '+1987654321',
        'text': 'Hello from TeXML!'
    }
    xml_str = proxy._generate_texml_response(telnyx_data)
    
    # Parse the XML string
    root = ET.fromstring(xml_str)
    
    # Verify structure
    assert root.tag == 'Response'
    say_elements = root.findall('Say')
    assert len(say_elements) == 1
    assert say_elements[0].text == 'Hello from TeXML!'

def test_sms_request_handling():
    """Test that SMS requests are handled with TeXML responses."""
    proxy = TelnyxProxy()
    
    # Create a request with SMS parameters
    response = proxy.request(
        'POST',
        'https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json',
        data={
            'To': '+1234567890',
            'From': '+1987654321',
            'Body': 'Hello from TeXML!'
        }
    )
    
    # Verify response is XML
    assert response.status_code == 200
    
    # Parse the XML string
    root = ET.fromstring(response.text)
    
    # Verify structure
    assert root.tag == 'Response'
    say_elements = root.findall('Say')
    assert len(say_elements) == 1
    assert say_elements[0].text == 'Hello from TeXML!'