"""
E-commerce Integrations Module
Handles Shopify and Amazon Seller Central integrations
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import boto3
from botocore.exceptions import ClientError
import shopify
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ShopifyIntegration:
    """Shopify integration for inventory synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.shop_url = os.environ.get('SHOPIFY_SHOP_URL', '')
        self.api_key = os.environ.get('SHOPIFY_API_KEY', '')
        self.password = os.environ.get('SHOPIFY_PASSWORD', '')
        self.webhook_secret = os.environ.get('SHOPIFY_WEBHOOK_SECRET', '')
        
        if self.shop_url and self.api_key and self.password:
            shopify.ShopifyResource.set_site(f"https://{self.api_key}:{self.password}@{self.shop_url}")
    
    async def sync_products_to_shopify(self) -> Dict[str, Any]:
        """Sync local products to Shopify"""
        try:
            if not self.shop_url:
                return {"success": False, "error": "Shopify not configured"}
            
            # Get local products
            products_query = """
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.category_id 
            WHERE p.is_active = 1
            """
            
            result = self.db.execute(text(products_query))
            local_products = result.fetchall()
            
            synced_count = 0
            errors = []
            
            for product_row in local_products:
                try:
                    # Check if product exists in Shopify
                    existing_products = shopify.Product.find(title=product_row.name)
                    
                    if existing_products:
                        # Update existing product
                        shopify_product = existing_products[0]
                        shopify_product.title = product_row.name
                        shopify_product.body_html = product_row.description or ""
                        
                        # Update variant (assuming single variant)
                        if shopify_product.variants:
                            variant = shopify_product.variants[0]
                            variant.price = str(product_row.price)
                            variant.sku = product_row.sku
                            variant.inventory_quantity = product_row.stock_quantity or 0
                            variant.inventory_management = "shopify"
                    else:
                        # Create new product
                        shopify_product = shopify.Product()
                        shopify_product.title = product_row.name
                        shopify_product.body_html = product_row.description or ""
                        shopify_product.product_type = product_row.category_name or "Electronics"
                        shopify_product.vendor = "Electronics Store"
                        
                        # Create variant
                        variant = shopify.Variant()
                        variant.price = str(product_row.price)
                        variant.sku = product_row.sku
                        variant.inventory_quantity = product_row.stock_quantity or 0
                        variant.inventory_management = "shopify"
                        variant.inventory_policy = "deny"
                        
                        shopify_product.variants = [variant]
                    
                    # Save product
                    if shopify_product.save():
                        synced_count += 1
                        logger.info(f"Synced product to Shopify: {product_row.name}")
                    else:
                        errors.append(f"Failed to save {product_row.name}: {shopify_product.errors}")
                        
                except Exception as e:
                    errors.append(f"Error syncing {product_row.name}: {str(e)}")
                    logger.error(f"Shopify sync error for {product_row.name}: {e}")
            
            return {
                "success": True,
                "synced_count": synced_count,
                "total_products": len(local_products),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Shopify sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_inventory_from_shopify(self) -> Dict[str, Any]:
        """Sync inventory levels from Shopify to local database"""
        try:
            if not self.shop_url:
                return {"success": False, "error": "Shopify not configured"}
            
            # Get all Shopify products
            shopify_products = shopify.Product.find()
            updated_count = 0
            errors = []
            
            for shopify_product in shopify_products:
                try:
                    for variant in shopify_product.variants:
                        if variant.sku:
                            # Find local product by SKU
                            local_product_query = """
                            SELECT product_id FROM products WHERE sku = :sku
                            """
                            result = self.db.execute(text(local_product_query), {'sku': variant.sku})
                            local_product = result.fetchone()
                            
                            if local_product:
                                # Update local inventory
                                update_query = """
                                UPDATE products 
                                SET stock_quantity = :quantity, 
                                    updated_at = CURRENT_TIMESTAMP 
                                WHERE product_id = :product_id
                                """
                                self.db.execute(text(update_query), {
                                    'quantity': variant.inventory_quantity or 0,
                                    'product_id': local_product.product_id
                                })
                                updated_count += 1
                                
                except Exception as e:
                    errors.append(f"Error updating inventory for {shopify_product.title}: {str(e)}")
            
            self.db.commit()
            
            return {
                "success": True,
                "updated_count": updated_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Shopify inventory sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_shopify_webhook(self, webhook_data: Dict[str, Any], webhook_topic: str) -> Dict[str, Any]:
        """Handle incoming Shopify webhooks"""
        try:
            if webhook_topic == "orders/create":
                return await self._handle_order_created(webhook_data)
            elif webhook_topic == "orders/updated":
                return await self._handle_order_updated(webhook_data)
            elif webhook_topic == "inventory_levels/update":
                return await self._handle_inventory_updated(webhook_data)
            else:
                return {"success": True, "message": f"Webhook {webhook_topic} received but not processed"}
                
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_order_created(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new order from Shopify"""
        try:
            # Reduce inventory for ordered items
            for line_item in order_data.get('line_items', []):
                if line_item.get('sku'):
                    update_query = """
                    UPDATE products 
                    SET stock_quantity = GREATEST(0, stock_quantity - :quantity)
                    WHERE sku = :sku
                    """
                    self.db.execute(text(update_query), {
                        'quantity': line_item.get('quantity', 0),
                        'sku': line_item.get('sku')
                    })
            
            self.db.commit()
            return {"success": True, "message": "Order processed"}
            
        except Exception as e:
            logger.error(f"Order processing error: {e}")
            return {"success": False, "error": str(e)}


class AmazonSellerIntegration:
    """Amazon Seller Central integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.access_key = os.environ.get('AMAZON_ACCESS_KEY', '')
        self.secret_key = os.environ.get('AMAZON_SECRET_KEY', '')
        self.seller_id = os.environ.get('AMAZON_SELLER_ID', '')
        self.marketplace_id = os.environ.get('AMAZON_MARKETPLACE_ID', 'ATVPDKIKX0DER')  # US marketplace
        self.region = os.environ.get('AMAZON_REGION', 'us-east-1')
        
        # Amazon SP-API endpoints
        self.base_url = "https://sellingpartnerapi-na.amazon.com"
        
    async def get_amazon_orders(self, days_back: int = 7) -> Dict[str, Any]:
        """Fetch recent orders from Amazon"""
        try:
            if not self.access_key or not self.seller_id:
                return {"success": False, "error": "Amazon credentials not configured"}
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # This is a simplified example - actual Amazon SP-API requires OAuth2 and LWA tokens
            headers = {
                'x-amz-access-token': self._get_access_token(),
                'Content-Type': 'application/json'
            }
            
            params = {
                'MarketplaceIds': self.marketplace_id,
                'CreatedAfter': start_date.isoformat(),
                'CreatedBefore': end_date.isoformat()
            }
            
            # Note: This is a placeholder - actual implementation requires proper SP-API authentication
            response = requests.get(
                f"{self.base_url}/orders/v0/orders",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                orders_data = response.json()
                return {
                    "success": True,
                    "orders": orders_data.get('payload', {}).get('Orders', []),
                    "count": len(orders_data.get('payload', {}).get('Orders', []))
                }
            else:
                return {"success": False, "error": f"Amazon API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Amazon orders fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_amazon_inventory(self) -> Dict[str, Any]:
        """Update inventory levels on Amazon"""
        try:
            if not self.access_key or not self.seller_id:
                return {"success": False, "error": "Amazon credentials not configured"}
            
            # Get local products with Amazon ASINs
            products_query = """
            SELECT product_id, name, sku, stock_quantity, amazon_asin 
            FROM products 
            WHERE amazon_asin IS NOT NULL AND is_active = 1
            """
            
            result = self.db.execute(text(products_query))
            products = result.fetchall()
            
            updated_count = 0
            errors = []
            
            for product in products:
                try:
                    # Prepare inventory update payload
                    inventory_update = {
                        "sku": product.sku,
                        "quantity": product.stock_quantity or 0,
                        "fulfillment_latency": 2  # Days to fulfill
                    }
                    
                    # This is a placeholder for actual Amazon SP-API call
                    # Real implementation would use the Inventory API
                    success = await self._update_amazon_product_inventory(inventory_update)
                    
                    if success:
                        updated_count += 1
                    else:
                        errors.append(f"Failed to update {product.sku}")
                        
                except Exception as e:
                    errors.append(f"Error updating {product.sku}: {str(e)}")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "total_products": len(products),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Amazon inventory update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_amazon_product_data(self) -> Dict[str, Any]:
        """Sync product data from Amazon catalog"""
        try:
            # Get products by ASIN
            products_query = """
            SELECT product_id, amazon_asin 
            FROM products 
            WHERE amazon_asin IS NOT NULL
            """
            
            result = self.db.execute(text(products_query))
            products = result.fetchall()
            
            synced_count = 0
            errors = []
            
            for product in products:
                try:
                    # Fetch product data from Amazon
                    product_data = await self._get_amazon_product_data(product.amazon_asin)
                    
                    if product_data:
                        # Update local product with Amazon data
                        update_query = """
                        UPDATE products 
                        SET 
                            amazon_price = :price,
                            amazon_rank = :rank,
                            amazon_reviews = :reviews,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = :product_id
                        """
                        
                        self.db.execute(text(update_query), {
                            'price': product_data.get('price'),
                            'rank': product_data.get('sales_rank'),
                            'reviews': product_data.get('review_count'),
                            'product_id': product.product_id
                        })
                        synced_count += 1
                        
                except Exception as e:
                    errors.append(f"Error syncing ASIN {product.amazon_asin}: {str(e)}")
            
            self.db.commit()
            
            return {
                "success": True,
                "synced_count": synced_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Amazon product sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_access_token(self) -> str:
        """Get Amazon LWA access token (placeholder)"""
        # This is a placeholder - actual implementation requires LWA OAuth2 flow
        return "placeholder_access_token"
    
    async def _update_amazon_product_inventory(self, inventory_data: Dict[str, Any]) -> bool:
        """Update single product inventory on Amazon (placeholder)"""
        # Placeholder for actual Amazon SP-API inventory update
        return True
    
    async def _get_amazon_product_data(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get product data from Amazon catalog (placeholder)"""
        # Placeholder for actual Amazon SP-API product lookup
        return {
            "price": 99.99,
            "sales_rank": 1000,
            "review_count": 50
        }


class EcommerceIntegrationManager:
    """Main manager for all e-commerce integrations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.shopify = ShopifyIntegration(db)
        self.amazon = AmazonSellerIntegration(db)
    
    async def sync_all_platforms(self) -> Dict[str, Any]:
        """Sync inventory across all e-commerce platforms"""
        results = {}
        
        try:
            # Sync to Shopify
            shopify_result = await self.shopify.sync_products_to_shopify()
            results['shopify'] = shopify_result
            
            # Update Amazon inventory
            amazon_result = await self.amazon.update_amazon_inventory()
            results['amazon'] = amazon_result
            
            return {
                "success": True,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Multi-platform sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all e-commerce platform integrations"""
        status = {
            "shopify": {
                "configured": bool(self.shopify.shop_url and self.shopify.api_key),
                "last_sync": None,
                "products_synced": 0
            },
            "amazon": {
                "configured": bool(self.amazon.access_key and self.amazon.seller_id),
                "last_sync": None,
                "products_synced": 0
            }
        }
        
        try:
            # Get sync statistics from database
            sync_stats_query = """
            SELECT 
                platform,
                COUNT(*) as product_count,
                MAX(last_sync) as last_sync_time
            FROM ecommerce_sync_log 
            GROUP BY platform
            """
            
            result = self.db.execute(text(sync_stats_query))
            sync_stats = result.fetchall()
            
            for stat in sync_stats:
                if stat.platform in status:
                    status[stat.platform]['products_synced'] = stat.product_count
                    status[stat.platform]['last_sync'] = stat.last_sync_time
            
        except Exception as e:
            logger.error(f"Error getting platform status: {e}")
        
        return status
    
    async def handle_inventory_change(self, product_id: int, old_quantity: int, new_quantity: int) -> Dict[str, Any]:
        """Handle inventory changes and sync to e-commerce platforms"""
        try:
            results = {}
            
            # Get product details
            product_query = """
            SELECT sku, name, shopify_product_id, amazon_asin 
            FROM products 
            WHERE product_id = :product_id
            """
            
            result = self.db.execute(text(product_query), {'product_id': product_id})
            product = result.fetchone()
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Update Shopify if configured
            if product.shopify_product_id and self.shopify.shop_url:
                try:
                    shopify_product = shopify.Product.find(product.shopify_product_id)
                    if shopify_product and shopify_product.variants:
                        variant = shopify_product.variants[0]
                        variant.inventory_quantity = new_quantity
                        if shopify_product.save():
                            results['shopify'] = {"success": True, "updated_quantity": new_quantity}
                        else:
                            results['shopify'] = {"success": False, "error": "Failed to update Shopify"}
                except Exception as e:
                    results['shopify'] = {"success": False, "error": str(e)}
            
            # Update Amazon if configured
            if product.amazon_asin and self.amazon.access_key:
                try:
                    amazon_result = await self.amazon._update_amazon_product_inventory({
                        "sku": product.sku,
                        "quantity": new_quantity
                    })
                    results['amazon'] = {"success": amazon_result, "updated_quantity": new_quantity}
                except Exception as e:
                    results['amazon'] = {"success": False, "error": str(e)}
            
            return {
                "success": True,
                "product_id": product_id,
                "quantity_change": new_quantity - old_quantity,
                "platform_results": results
            }
            
        except Exception as e:
            logger.error(f"Inventory change handling failed: {e}")
            return {"success": False, "error": str(e)}


def create_ecommerce_integrations(db: Session) -> Dict[str, Any]:
    """Factory function to create e-commerce integration instances"""
    return {
        "manager": EcommerceIntegrationManager(db),
        "shopify": ShopifyIntegration(db),
        "amazon": AmazonSellerIntegration(db)
    }
