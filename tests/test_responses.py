"""Tests for canned responses."""
import pytest
from app.responses import get_canned_response


class TestCannedResponses:
    """Test canned response matching."""
    
    def test_greeting_hello(self):
        response = get_canned_response("Hello")
        assert response is not None
        assert "Hello" in response
    
    def test_greeting_hi(self):
        response = get_canned_response("Hi there!")
        assert response is not None
        assert "Hello" in response
    
    def test_order_status(self):
        response = get_canned_response("Where is my order?")
        assert response is not None
        assert "order" in response.lower()
    
    def test_shipping_time(self):
        response = get_canned_response("How long does shipping take?")
        assert response is not None
        assert "shipping" in response.lower() or "business days" in response.lower()
    
    def test_returns(self):
        response = get_canned_response("What is your return policy?")
        assert response is not None
        assert "return" in response.lower()
    
    def test_payment(self):
        response = get_canned_response("What payment methods do you accept?")
        assert response is not None
        assert "visa" in response.lower() or "payment" in response.lower()
    
    def test_recommendations(self):
        response = get_canned_response("Can you recommend a book?")
        assert response is not None
        assert "recommend" in response.lower() or "suggestion" in response.lower() or "genre" in response.lower()
    
    def test_no_match(self):
        response = get_canned_response("asdfjkl random gibberish xyz123")
        assert response is None
    
    def test_thanks(self):
        response = get_canned_response("Thanks!")
        assert response is not None
        assert "welcome" in response.lower()
    
    def test_goodbye(self):
        response = get_canned_response("Goodbye")
        assert response is not None
        assert "bye" in response.lower() or "happy reading" in response.lower()
