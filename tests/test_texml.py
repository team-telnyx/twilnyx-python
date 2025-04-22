"""Tests for TeXML functionality in Twilnyx."""

import pytest
import xml.etree.ElementTree as ET
from twilnyx import TelnyxProxy
from twilio.http.response import Response

def test_generate_texml_response():
    """Test that TeXML responses are generated correctly for media requests."""
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    # Test with a single media URL
    telnyx_data = {'media_urls': 'https://example.com/audio.mp3'}
    xml_str = proxy._generate_texml_response(telnyx_data)
    
    # Parse the XML string
    root = ET.fromstring(xml_str)
    
    # Verify structure
    assert root.tag == 'Response'
    play_elements = root.findall('Play')
    assert len(play_elements) == 1
    assert play_elements[0].text == 'https://example.com/audio.mp3'
    
    # Test with multiple media URLs
    telnyx_data = {'media_urls': [
        'https://example.com/audio1.mp3',
        'https://example.com/audio2.mp3'
    ]}
    xml_str = proxy._generate_texml_response(telnyx_data)
    
    # Parse the XML string
    root = ET.fromstring(xml_str)
    
    # Verify structure
    play_elements = root.findall('Play')
    assert len(play_elements) == 2
    assert play_elements[0].text == 'https://example.com/audio1.mp3'
    assert play_elements[1].text == 'https://example.com/audio2.mp3'

def test_media_request_handling():
    """Test that media requests are handled with TeXML responses."""
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    # Create a request with MediaUrl parameter
    response = proxy.request(
        'POST',
        'https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json',
        data={
            'To': '+1234567890',
            'From': '+1987654321',
            'MediaUrl': 'https://example.com/audio.mp3'
        }
    )
    
    # Verify response is XML
    assert response.status_code == 200
    
    # Parse the XML string
    root = ET.fromstring(response.text)
    
    # Verify structure
    assert root.tag == 'Response'
    play_elements = root.findall('Play')
    assert len(play_elements) == 1
    assert play_elements[0].text == 'https://example.com/audio.mp3'

def test_multiple_media_request_handling():
    """Test that requests with multiple media URLs are handled correctly."""
    proxy = TelnyxProxy('test_key', 'test_profile')
    
    # Create a request with multiple MediaUrl parameters
    # Note: In Twilio, multiple MediaUrls would be passed as MediaUrl0, MediaUrl1, etc.
    # For simplicity in this test, we're using a list directly
    response = proxy.request(
        'POST',
        'https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json',
        data={
            'To': '+1234567890',
            'From': '+1987654321',
            'MediaUrl': ['https://example.com/audio1.mp3', 'https://example.com/audio2.mp3']
        }
    )
    
    # Verify response is XML
    assert response.status_code == 200
    
    # Parse the XML string
    root = ET.fromstring(response.text)
    
    # Verify structure
    play_elements = root.findall('Play')
    assert len(play_elements) == 2