"""Bookstore API client for order and product queries."""
import os
import logging
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class BookstoreClient:
    """Client for communicating with the Bookstore API.
    
    Enables the chatbot to:
    - Look up order status
    - Search for products
    - Get product recommendations
    
    Environment variables:
        BOOKSTORE_API_URL: Base URL for Bookstore API
    """
    
    def __init__(self):
        self.base_url = os.getenv("BOOKSTORE_API_URL", "http://bookstore-service.bookstore:8080")
        self.timeout = 10.0
        
        logger.info(f"Initialized Bookstore client: {self.base_url}")
    
    async def get_order_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get status of an order.
        
        Args:
            order_id: The order ID to look up
            
        Returns:
            Order data dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/orders/{order_id}/status")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Order status error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    async def search_products(
        self, 
        query: str, 
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for products in the bookstore.
        
        Args:
            query: Search query string
            category: Optional category filter
            limit: Max number of results
            
        Returns:
            List of product dicts
        """
        try:
            params = {"q": query}
            if category:
                params["category"] = category
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/products/search",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # API returns array directly, not wrapped in {"products": ...}
                    if isinstance(data, list):
                        # Filter out any None entries
                        products = [p for p in data if isinstance(p, dict)]
                    elif isinstance(data, dict) and "products" in data:
                        products = [p for p in data.get("products", []) if isinstance(p, dict)]
                    else:
                        products = []
                    return products[:limit]
                else:
                    logger.error(f"Product search error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            return []
    
    async def get_recommendations(self, category: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get product recommendations for a category.
        
        Args:
            category: Category to get recommendations for
            limit: Max number of recommendations
            
        Returns:
            List of recommended product dicts
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/products",
                    params={"category": category}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # API returns array directly, not wrapped in {"products": ...}
                    if isinstance(data, list):
                        # Filter out any None entries
                        products = [p for p in data if isinstance(p, dict)]
                    elif isinstance(data, dict) and "products" in data:
                        products = [p for p in data.get("products", []) if isinstance(p, dict)]
                    else:
                        products = []
                    return products[:limit]
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Bookstore API is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
