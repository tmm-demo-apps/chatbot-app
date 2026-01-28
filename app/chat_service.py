"""Chat service orchestrating LLM and canned responses."""
import logging
import uuid
from typing import Optional

from .llm.client import LLMClient
from .integrations.bookstore import BookstoreClient
from .responses import get_canned_response

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates chat responses from LLM or canned responses."""
    
    SYSTEM_PROMPT = """You are a helpful bookstore assistant for an online bookstore that sells classic literature.

Your role:
- Help customers find books from our catalog
- Answer questions about our products
- Provide recommendations based on what we actually sell

Important rules:
- ONLY recommend books from the "Available in our store" list provided in each query
- If no books match, say we don't have that specific item but suggest similar books from our catalog
- Keep responses brief (2-3 sentences max)
- Be helpful and friendly
- Include book titles and authors when making recommendations"""

    # Keywords that indicate user wants product recommendations
    PRODUCT_KEYWORDS = [
        # Generic book terms
        "book", "books", "read", "reading", "recommend", "suggestion", "looking for",
        "buy", "purchase", "get", "find", "search", "want", "need",
        # Genres
        "fiction", "poetry", "drama", "philosophy", "history", "science",
        "sci-fi", "scifi", "science fiction", "novel", "classic", "classics",
        # Common author names in our catalog
        "author", "writer", "written by",
        "shakespeare", "dickens", "austen", "twain", "mark twain",
        "wilde", "oscar wilde", "shelley", "mary shelley",
        "verne", "jules verne", "wells", "h.g. wells", "h. g. wells",
        "dostoyevsky", "dostoevsky", "tolstoy", "homer", "plato",
        "bronte", "brontë", "poe", "edgar allan poe",
        "stoker", "bram stoker", "doyle", "conan doyle",
        "melville", "hawthorne", "thoreau", "emerson",
        "kafka", "nietzsche", "darwin", "newton",
    ]

    def __init__(self, llm_client: LLMClient, bookstore_client: Optional[BookstoreClient] = None):
        self.llm = llm_client
        self.bookstore = bookstore_client or BookstoreClient()
    
    async def get_response(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        context: Optional[dict] = None
    ) -> str:
        """Get a response for the user message.
        
        Strategy:
        1. Try canned responses first (fast, free)
        2. If product-related, fetch real products and include in LLM context
        3. If no match, use LLM (slower, requires backend)
        4. If LLM fails, use generic fallback
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 1. Try canned responses first
        canned = get_canned_response(message)
        if canned:
            logger.info(f"Returning canned response for: {message[:50]}...")
            return canned
        
        # 2. Build product context if message seems product-related
        product_context, products = await self._build_product_context(message)
        
        # 2.5. If we have products and LLM might be slow, return a quick templated response
        # This is faster for demos and doesn't require waiting 60-120s for LLM on CPU
        if products:
            quick_response = self._format_quick_product_response(message, products)
            if quick_response:
                logger.info(f"Quick product response for: {message[:50]}...")
                return quick_response
        
        # 3. Try LLM with product context (slower path)
        try:
            if await self.llm.health_check():
                system_prompt = self.SYSTEM_PROMPT
                if product_context:
                    system_prompt = f"{self.SYSTEM_PROMPT}\n\n{product_context}"
                
                messages = [{"role": "user", "content": message}]
                response = await self.llm.chat(messages, system_prompt)
                logger.info(f"LLM response for: {message[:50]}...")
                return response
        except Exception as e:
            logger.error(f"LLM error: {e}")
        
        # 4. Generic fallback
        logger.warning(f"Using fallback response for: {message[:50]}...")
        return self._fallback_response()
    
    async def _build_product_context(self, message: str) -> tuple[str, list]:
        """Build context about available products based on the user's message.
        
        Returns:
            Tuple of (context_string, products_list)
        """
        message_lower = message.lower()
        
        # Check if message seems product-related
        if not any(kw in message_lower for kw in self.PRODUCT_KEYWORDS):
            return "", []
        
        products = []
        
        # Try to detect category from message
        category = self._detect_category(message_lower)
        
        # Search for products
        try:
            if category:
                # Get products from specific category
                logger.info(f"Fetching products for category: {category}")
                products = await self.bookstore.get_recommendations(category, limit=5)
            
            # Also search by the message content - extract key terms for better results
            search_query = self._extract_search_terms(message)
            if search_query:
                search_products = await self.bookstore.search_products(search_query, limit=5)
            else:
                search_products = []
            
            # Combine and dedupe (handle both PascalCase and lowercase keys)
            seen_skus = set()
            for p in products:
                if isinstance(p, dict):
                    sku = p.get("SKU") or p.get("sku")
                    if sku:
                        seen_skus.add(sku)
            
            for p in search_products:
                if not isinstance(p, dict):
                    continue
                sku = p.get("SKU") or p.get("sku")
                if sku and sku not in seen_skus:
                    products.append(p)
                    seen_skus.add(sku)
            
            # Limit to top 8 products
            products = products[:8]
            
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            return "", []
        
        if not products:
            return "", []
        
        # Format products for LLM context
        # Note: Go struct fields serialize as PascalCase (Name, Author, Price)
        # Author can be None/null for some products
        context = "Available in our store:\n"
        for p in products:
            if not isinstance(p, dict):
                continue
            name = p.get("Name") or p.get("name") or "Unknown"
            author = p.get("Author") or p.get("author") or "Unknown Author"
            price = p.get("Price") or p.get("price") or 0
            # Category is stored by ID, not name in the product list
            context += f"- \"{name}\" by {author} (${price:.2f})\n"
        
        logger.info(f"Built product context with {len(products)} products")
        return context, products
    
    def _extract_search_terms(self, message: str) -> str:
        """Extract meaningful search terms from the user message.
        
        Removes common words and keeps nouns/names that are useful for product search.
        """
        # Common stop words to remove
        stop_words = {
            "i", "me", "my", "we", "our", "you", "your", "the", "a", "an",
            "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "must", "can", "to", "of", "in", "for", "on", "with",
            "at", "by", "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all", "each", "few",
            "more", "most", "other", "some", "such", "no", "nor", "not", "only",
            "own", "same", "so", "than", "too", "very", "just", "also",
            "want", "need", "looking", "search", "find", "get", "buy", "purchase",
            "recommend", "suggest", "something", "anything", "any", "please", "help",
            "like", "about", "read", "reading", "book", "books",
            "what", "which", "who", "whom", "this", "that", "these", "those",
            "tell", "show", "give", "list", "name", "names",
        }
        
        # Tokenize and filter
        words = message.lower().split()
        terms = [w.strip(".,!?;:'\"") for w in words if w.lower().strip(".,!?;:'\"") not in stop_words]
        
        # Return the filtered terms or the original message if nothing left
        if terms:
            return " ".join(terms)
        return message
    
    def _detect_category(self, message: str) -> Optional[str]:
        """Detect product category from message."""
        # Order matters - check more specific categories FIRST before generic ones
        # "science fiction" must be checked before "fiction" and "science"
        category_keywords = [
            ("Science Fiction", ["sci-fi", "scifi", "science fiction", "futuristic", "space", "alien"]),
            ("Non-Fiction", ["non-fiction", "nonfiction", "biography", "memoir"]),
            ("Political Science", ["politics", "political", "government"]),
            ("Poetry", ["poetry", "poem", "poems", "verse"]),
            ("Drama", ["drama", "play", "plays", "theatre", "theater", "shakespeare"]),
            ("Philosophy", ["philosophy", "philosophical", "ethics", "plato", "aristotle"]),
            ("History", ["history", "historical"]),
            ("Science", ["science", "scientific"]),
            ("Technology", ["technology", "tech", "computer"]),
            ("Fiction", ["fiction", "novel", "story", "stories"]),  # Most generic - check last
        ]
        
        for category, keywords in category_keywords:
            if any(kw in message for kw in keywords):
                return category
        
        return None
    
    def _format_quick_product_response(self, message: str, products: list) -> str:
        """Format a quick templated response with product recommendations.
        
        This provides instant responses for product queries without waiting for LLM.
        """
        if not products:
            return ""
        
        # Detect category for personalized intro
        category = self._detect_category(message.lower())
        
        # Build intro based on context
        if category:
            intro = f"Here are some {category} books from our collection:"
        elif "recommend" in message.lower():
            intro = "Based on your interest, I'd recommend these books:"
        else:
            intro = "Here's what I found in our store:"
        
        # Format product list with product IDs for linking
        lines = [intro, ""]
        for p in products[:5]:  # Limit to 5 for readability
            if not isinstance(p, dict):
                continue
            name = p.get("Name") or p.get("name") or "Unknown"
            author = p.get("Author") or p.get("author")
            price = p.get("Price") or p.get("price") or 0
            product_id = p.get("ID") or p.get("id") or ""
            
            # Include [ID:X] marker for the frontend to create links
            if author:
                lines.append(f"• [ID:{product_id}] \"{name}\" by {author} - ${price:.2f}")
            else:
                lines.append(f"• [ID:{product_id}] \"{name}\" - ${price:.2f}")
        
        lines.append("")
        lines.append("Would you like more details about any of these books?")
        
        return "\n".join(lines)
    
    def _fallback_response(self) -> str:
        return (
            "I'm having trouble processing that request right now. "
            "Please try again later or contact us at support@bookstore.com "
            "for immediate assistance."
        )
