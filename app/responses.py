"""Canned responses for common queries."""
import re
from typing import Optional

# Response patterns - order matters (first match wins)
RESPONSE_PATTERNS = [
    # Greetings
    {
        "patterns": [r"\b(hi|hello|hey|howdy|greetings)\b"],
        "response": "Hello! I'm here to help with any questions about your orders, books, or our bookstore. What can I assist you with today?"
    },
    
    # Order status
    {
        "patterns": [
            r"\b(where|track|status).*(order|package|shipment)\b",
            r"\border.*(status|track|where)\b",
            r"\b(tracking|shipped)\b"
        ],
        "response": "I can help you track your order! Please provide your order number (starts with #), and I'll look up the status for you. You can also find tracking information in the confirmation email sent when your order shipped."
    },
    
    # Shipping time
    {
        "patterns": [
            r"\b(how long|when).*(ship|deliver|arrive)\b",
            r"\bshipping (time|duration|speed)\b",
            r"\bdelivery (time|estimate)\b"
        ],
        "response": "Our shipping times are:\n• Standard Shipping: 5-7 business days\n• Express Shipping: 2-3 business days\n• Next Day: Order by 2pm for next business day delivery\n\nAll orders are processed within 1-2 business days."
    },
    
    # Returns and refunds
    {
        "patterns": [
            r"\b(return|refund|exchange)\b",
            r"\bsend.*(back|return)\b",
            r"\bmoney back\b"
        ],
        "response": "Our return policy:\n• Returns accepted within 30 days of purchase\n• Books must be in original condition (unread, no damage)\n• Refunds processed within 5-7 business days\n• Free return shipping for defective items\n\nTo start a return, go to your Order History and select 'Return Item'."
    },
    
    # Payment methods
    {
        "patterns": [
            r"\b(payment|pay|credit card|debit)\b",
            r"\baccept.*(visa|mastercard|paypal)\b",
            r"\bhow.*(pay|purchase)\b"
        ],
        "response": "We accept the following payment methods:\n• Visa, Mastercard, American Express\n• PayPal\n• Apple Pay & Google Pay\n\nAll transactions are securely processed with SSL encryption."
    },
    
    # Book recommendations - ONLY match very generic requests, let specific ones go to LLM
    # Specific genre/author requests like "recommend scifi" or "shakespeare books" should NOT match
    # so they can be handled by the LLM with actual product context
    # {
    #     "patterns": [
    #         r"\brecommend\b",
    #         r"\bsuggest.*(book|read)\b",
    #         r"\bwhat.*(read|book)\b",
    #         r"\bbest.*(book|seller)\b"
    #     ],
    #     "response": "... disabled to allow LLM to handle with real product data ..."
    # },
    
    # Account/login issues
    {
        "patterns": [
            r"\b(login|sign in|password|account)\b",
            r"\bcan't (access|login|sign)\b",
            r"\bforgot.*(password|email)\b"
        ],
        "response": "For account issues:\n• Forgot password? Click 'Forgot Password' on the login page\n• Can't find your account? Try the email you used to purchase\n• Still having trouble? Contact support@bookstore.com\n\nMake sure to check your spam folder for our emails!"
    },
    
    # Contact/support
    {
        "patterns": [
            r"\b(contact|support|help|human|agent|person)\b",
            r"\btalk to.*(someone|person)\b",
            r"\bemail|phone\b"
        ],
        "response": "You can reach our support team at:\n• Email: support@bookstore.com\n• Hours: Monday-Friday, 9am-5pm EST\n\nTypical response time is within 24 hours. For urgent matters, please include 'URGENT' in your subject line."
    },
    
    # Thanks
    {
        "patterns": [r"\b(thanks|thank you|thx)\b"],
        "response": "You're welcome! Is there anything else I can help you with?"
    },
    
    # Goodbye
    {
        "patterns": [r"\b(bye|goodbye|see you|later)\b"],
        "response": "Goodbye! Thanks for visiting the bookstore. Happy reading! 📚"
    },
]


def get_canned_response(message: str) -> Optional[str]:
    """Check if message matches any canned response patterns.
    
    Returns the canned response if matched, None otherwise.
    """
    message_lower = message.lower().strip()
    
    for pattern_group in RESPONSE_PATTERNS:
        for pattern in pattern_group["patterns"]:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return pattern_group["response"]
    
    return None
