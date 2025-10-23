"""
Advanced Financial Reporting System
Comprehensive financial analysis, profit tracking, and business intelligence
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class FinancialReportingManager:
    """Advanced financial reporting and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_profit_loss_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive profit and loss report"""
        try:
            # Revenue Analysis
            revenue_query = """
            SELECT 
                DATE(s.sale_date) as sale_date,
                SUM(s.total_amount) as daily_revenue,
                COUNT(s.sale_id) as transaction_count,
                AVG(s.total_amount) as avg_transaction_value
            FROM sales s
            WHERE s.sale_date BETWEEN :start_date AND :end_date
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_date
            """
            
            revenue_result = self.db.execute(text(revenue_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            daily_revenue = [dict(row) for row in revenue_result.fetchall()]
            
            # Cost of Goods Sold (COGS)
            cogs_query = """
            SELECT 
                DATE(s.sale_date) as sale_date,
                SUM(si.quantity * COALESCE(p.cost, 0)) as daily_cogs
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE s.sale_date BETWEEN :start_date AND :end_date
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_date
            """
            
            cogs_result = self.db.execute(text(cogs_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            daily_cogs = [dict(row) for row in cogs_result.fetchall()]
            
            # Product Performance
            product_performance_query = """
            SELECT 
                p.name,
                p.sku,
                c.name as category,
                SUM(si.quantity) as units_sold,
                SUM(si.quantity * si.price) as revenue,
                SUM(si.quantity * COALESCE(p.cost, 0)) as cogs,
                SUM(si.quantity * si.price) - SUM(si.quantity * COALESCE(p.cost, 0)) as gross_profit,
                CASE 
                    WHEN SUM(si.quantity * si.price) > 0 
                    THEN ((SUM(si.quantity * si.price) - SUM(si.quantity * COALESCE(p.cost, 0))) / SUM(si.quantity * si.price)) * 100
                    ELSE 0 
                END as margin_percent
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE s.sale_date BETWEEN :start_date AND :end_date
            GROUP BY p.product_id, p.name, p.sku, c.name
            ORDER BY gross_profit DESC
            """
            
            product_result = self.db.execute(text(product_performance_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            product_performance = [dict(row) for row in product_result.fetchall()]
            
            # Returns Impact
            returns_query = """
            SELECT 
                COUNT(*) as return_count,
                SUM(r.refund_amount) as total_refunds,
                AVG(r.refund_amount) as avg_refund
            FROM returns r
            WHERE r.return_date BETWEEN :start_date AND :end_date
            AND r.status = 'completed'
            """
            
            returns_result = self.db.execute(text(returns_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            returns_impact = dict(returns_result.fetchone())
            
            # Calculate totals
            total_revenue = sum(day['daily_revenue'] for day in daily_revenue)
            total_cogs = sum(day['daily_cogs'] for day in daily_cogs)
            total_refunds = returns_impact['total_refunds'] or 0
            
            net_revenue = total_revenue - total_refunds
            gross_profit = net_revenue - total_cogs
            gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0
            
            return {
                "success": True,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days + 1
                },
                "summary": {
                    "total_revenue": float(total_revenue),
                    "total_cogs": float(total_cogs),
                    "total_refunds": float(total_refunds),
                    "net_revenue": float(net_revenue),
                    "gross_profit": float(gross_profit),
                    "gross_margin_percent": float(gross_margin)
                },
                "daily_revenue": daily_revenue,
                "daily_cogs": daily_cogs,
                "product_performance": product_performance,
                "returns_impact": returns_impact,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"P&L report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_inventory_valuation_report(self) -> Dict[str, Any]:
        """Generate inventory valuation and turnover analysis"""
        try:
            # Current inventory valuation
            valuation_query = """
            SELECT 
                p.product_id,
                p.name,
                p.sku,
                c.name as category,
                p.stock_quantity,
                p.cost,
                p.price,
                (p.stock_quantity * COALESCE(p.cost, 0)) as cost_value,
                (p.stock_quantity * p.price) as retail_value,
                p.reorder_level,
                CASE 
                    WHEN p.stock_quantity <= p.reorder_level THEN 'Low Stock'
                    WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                    ELSE 'In Stock'
                END as stock_status
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
            ORDER BY cost_value DESC
            """
            
            valuation_result = self.db.execute(text(valuation_query))
            inventory_valuation = [dict(row) for row in valuation_result.fetchall()]
            
            # Inventory turnover analysis (last 90 days)
            ninety_days_ago = datetime.now() - timedelta(days=90)
            
            turnover_query = """
            SELECT 
                p.product_id,
                p.name,
                p.sku,
                p.stock_quantity as current_stock,
                COALESCE(SUM(si.quantity), 0) as units_sold_90d,
                CASE 
                    WHEN p.stock_quantity > 0 AND SUM(si.quantity) > 0
                    THEN (SUM(si.quantity) / p.stock_quantity) * (365.0 / 90.0)
                    ELSE 0
                END as annual_turnover_ratio,
                CASE 
                    WHEN SUM(si.quantity) > 0
                    THEN 365.0 / ((SUM(si.quantity) / 90.0))
                    ELSE NULL
                END as days_of_supply
            FROM products p
            LEFT JOIN sale_items si ON p.product_id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.sale_id AND s.sale_date >= :ninety_days_ago
            WHERE p.is_active = 1
            GROUP BY p.product_id, p.name, p.sku, p.stock_quantity
            ORDER BY annual_turnover_ratio DESC
            """
            
            turnover_result = self.db.execute(text(turnover_query), {
                'ninety_days_ago': ninety_days_ago
            })
            turnover_analysis = [dict(row) for row in turnover_result.fetchall()]
            
            # Dead stock analysis (no sales in 180 days)
            dead_stock_query = """
            SELECT 
                p.product_id,
                p.name,
                p.sku,
                p.stock_quantity,
                (p.stock_quantity * COALESCE(p.cost, 0)) as tied_up_capital,
                MAX(s.sale_date) as last_sale_date
            FROM products p
            LEFT JOIN sale_items si ON p.product_id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.sale_id
            WHERE p.is_active = 1 
            AND p.stock_quantity > 0
            GROUP BY p.product_id, p.name, p.sku, p.stock_quantity
            HAVING MAX(s.sale_date) < :cutoff_date OR MAX(s.sale_date) IS NULL
            ORDER BY tied_up_capital DESC
            """
            
            dead_stock_cutoff = datetime.now() - timedelta(days=180)
            dead_stock_result = self.db.execute(text(dead_stock_query), {
                'cutoff_date': dead_stock_cutoff
            })
            dead_stock = [dict(row) for row in dead_stock_result.fetchall()]
            
            # Calculate summary metrics
            total_cost_value = sum(item['cost_value'] for item in inventory_valuation)
            total_retail_value = sum(item['retail_value'] for item in inventory_valuation)
            total_units = sum(item['stock_quantity'] for item in inventory_valuation)
            
            low_stock_items = [item for item in inventory_valuation if item['stock_status'] == 'Low Stock']
            out_of_stock_items = [item for item in inventory_valuation if item['stock_status'] == 'Out of Stock']
            
            return {
                "success": True,
                "summary": {
                    "total_cost_value": float(total_cost_value),
                    "total_retail_value": float(total_retail_value),
                    "total_units": total_units,
                    "total_products": len(inventory_valuation),
                    "low_stock_count": len(low_stock_items),
                    "out_of_stock_count": len(out_of_stock_items),
                    "dead_stock_count": len(dead_stock),
                    "dead_stock_value": sum(item['tied_up_capital'] for item in dead_stock)
                },
                "inventory_valuation": inventory_valuation,
                "turnover_analysis": turnover_analysis,
                "dead_stock": dead_stock,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Inventory valuation report failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_customer_analysis_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate customer behavior and profitability analysis"""
        try:
            # Customer lifetime value analysis
            clv_query = """
            SELECT 
                c.customer_id,
                c.name,
                c.email,
                COUNT(s.sale_id) as total_orders,
                SUM(s.total_amount) as total_spent,
                AVG(s.total_amount) as avg_order_value,
                MIN(s.sale_date) as first_purchase,
                MAX(s.sale_date) as last_purchase,
                JULIANDAY('now') - JULIANDAY(MAX(s.sale_date)) as days_since_last_purchase
            FROM customers c
            JOIN sales s ON c.customer_id = s.customer_id
            WHERE s.sale_date BETWEEN :start_date AND :end_date
            GROUP BY c.customer_id, c.name, c.email
            ORDER BY total_spent DESC
            """
            
            clv_result = self.db.execute(text(clv_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            customer_analysis = [dict(row) for row in clv_result.fetchall()]
            
            # Customer segmentation (RFM Analysis)
            rfm_query = """
            SELECT 
                c.customer_id,
                c.name,
                JULIANDAY('now') - JULIANDAY(MAX(s.sale_date)) as recency_days,
                COUNT(s.sale_id) as frequency,
                SUM(s.total_amount) as monetary_value
            FROM customers c
            JOIN sales s ON c.customer_id = s.customer_id
            WHERE s.sale_date >= :start_date
            GROUP BY c.customer_id, c.name
            """
            
            rfm_result = self.db.execute(text(rfm_query), {
                'start_date': start_date
            })
            rfm_data = [dict(row) for row in rfm_result.fetchall()]
            
            # Calculate RFM scores and segments
            rfm_segments = self._calculate_rfm_segments(rfm_data)
            
            # New vs returning customers
            customer_type_query = """
            SELECT 
                DATE(s.sale_date) as sale_date,
                COUNT(DISTINCT CASE WHEN customer_first_purchase.first_date = DATE(s.sale_date) THEN s.customer_id END) as new_customers,
                COUNT(DISTINCT CASE WHEN customer_first_purchase.first_date < DATE(s.sale_date) THEN s.customer_id END) as returning_customers
            FROM sales s
            JOIN (
                SELECT customer_id, MIN(DATE(sale_date)) as first_date
                FROM sales
                GROUP BY customer_id
            ) customer_first_purchase ON s.customer_id = customer_first_purchase.customer_id
            WHERE s.sale_date BETWEEN :start_date AND :end_date
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_date
            """
            
            customer_type_result = self.db.execute(text(customer_type_query), {
                'start_date': start_date,
                'end_date': end_date
            })
            customer_acquisition = [dict(row) for row in customer_type_result.fetchall()]
            
            return {
                "success": True,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "customer_analysis": customer_analysis,
                "rfm_segments": rfm_segments,
                "customer_acquisition": customer_acquisition,
                "summary": {
                    "total_customers": len(customer_analysis),
                    "total_clv": sum(c['total_spent'] for c in customer_analysis),
                    "avg_clv": sum(c['total_spent'] for c in customer_analysis) / len(customer_analysis) if customer_analysis else 0,
                    "avg_order_value": sum(c['avg_order_value'] for c in customer_analysis) / len(customer_analysis) if customer_analysis else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Customer analysis report failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_sales_forecast(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Generate sales forecast using historical data"""
        try:
            # Get historical sales data (last 365 days)
            historical_query = """
            SELECT 
                DATE(sale_date) as sale_date,
                SUM(total_amount) as daily_sales,
                COUNT(sale_id) as transaction_count
            FROM sales
            WHERE sale_date >= DATE('now', '-365 days')
            GROUP BY DATE(sale_date)
            ORDER BY sale_date
            """
            
            historical_result = self.db.execute(text(historical_query))
            historical_data = [dict(row) for row in historical_result.fetchall()]
            
            if len(historical_data) < 30:
                return {"success": False, "error": "Insufficient historical data for forecasting"}
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(historical_data)
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            df = df.set_index('sale_date')
            
            # Simple moving average forecast
            window_size = 30
            df['ma_30'] = df['daily_sales'].rolling(window=window_size).mean()
            
            # Trend analysis
            df['trend'] = df['daily_sales'].rolling(window=7).mean().diff()
            
            # Seasonal analysis (day of week effect)
            df['day_of_week'] = df.index.dayofweek
            seasonal_factors = df.groupby('day_of_week')['daily_sales'].mean()
            
            # Generate forecast
            last_ma = df['ma_30'].iloc[-1]
            last_trend = df['trend'].iloc[-1]
            
            forecast_dates = pd.date_range(
                start=df.index[-1] + pd.Timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            forecast_values = []
            for i, date in enumerate(forecast_dates):
                base_forecast = last_ma + (last_trend * i)
                seasonal_factor = seasonal_factors[date.dayofweek] / df['daily_sales'].mean()
                forecasted_value = base_forecast * seasonal_factor
                
                forecast_values.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'forecasted_sales': max(0, float(forecasted_value)),
                    'confidence': 'medium'  # Simplified confidence level
                })
            
            # Calculate forecast summary
            total_forecast = sum(f['forecasted_sales'] for f in forecast_values)
            avg_daily_forecast = total_forecast / days_ahead
            
            return {
                "success": True,
                "forecast_period": {
                    "start_date": forecast_dates[0].strftime('%Y-%m-%d'),
                    "end_date": forecast_dates[-1].strftime('%Y-%m-%d'),
                    "days": days_ahead
                },
                "forecast": forecast_values,
                "summary": {
                    "total_forecasted_sales": float(total_forecast),
                    "avg_daily_sales": float(avg_daily_forecast),
                    "historical_avg": float(df['daily_sales'].mean()),
                    "growth_rate": float(((avg_daily_forecast / df['daily_sales'].mean()) - 1) * 100)
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sales forecast generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_financial_dashboard_data(self) -> Dict[str, Any]:
        """Generate key financial metrics for dashboard"""
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            last_month = today - timedelta(days=30)
            
            # Today's metrics
            today_query = """
            SELECT 
                COUNT(sale_id) as transactions,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_transaction
            FROM sales
            WHERE DATE(sale_date) = :today
            """
            
            today_result = self.db.execute(text(today_query), {'today': today})
            today_metrics = dict(today_result.fetchone())
            
            # Yesterday's metrics for comparison
            yesterday_query = """
            SELECT 
                COUNT(sale_id) as transactions,
                SUM(total_amount) as revenue
            FROM sales
            WHERE DATE(sale_date) = :yesterday
            """
            
            yesterday_result = self.db.execute(text(yesterday_query), {'yesterday': yesterday})
            yesterday_metrics = dict(yesterday_result.fetchone())
            
            # Monthly metrics
            monthly_query = """
            SELECT 
                COUNT(sale_id) as transactions,
                SUM(total_amount) as revenue,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales
            WHERE sale_date >= :last_month
            """
            
            monthly_result = self.db.execute(text(monthly_query), {'last_month': last_month})
            monthly_metrics = dict(monthly_result.fetchone())
            
            # Top products this month
            top_products_query = """
            SELECT 
                p.name,
                SUM(si.quantity) as units_sold,
                SUM(si.quantity * si.price) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.sale_date >= :last_month
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT 5
            """
            
            top_products_result = self.db.execute(text(top_products_query), {'last_month': last_month})
            top_products = [dict(row) for row in top_products_result.fetchall()]
            
            # Calculate growth rates
            revenue_growth = 0
            if yesterday_metrics['revenue'] and yesterday_metrics['revenue'] > 0:
                revenue_growth = ((today_metrics['revenue'] or 0) / yesterday_metrics['revenue'] - 1) * 100
            
            return {
                "success": True,
                "today": {
                    "transactions": today_metrics['transactions'] or 0,
                    "revenue": float(today_metrics['revenue'] or 0),
                    "avg_transaction": float(today_metrics['avg_transaction'] or 0)
                },
                "growth": {
                    "revenue_vs_yesterday": float(revenue_growth)
                },
                "monthly": {
                    "transactions": monthly_metrics['transactions'] or 0,
                    "revenue": float(monthly_metrics['revenue'] or 0),
                    "unique_customers": monthly_metrics['unique_customers'] or 0
                },
                "top_products": top_products,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_rfm_segments(self, rfm_data: List[Dict]) -> Dict[str, Any]:
        """Calculate RFM segments for customer analysis"""
        if not rfm_data:
            return {"segments": [], "summary": {}}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(rfm_data)
        
        # Calculate quintiles for each metric
        df['r_score'] = pd.qcut(df['recency_days'], 5, labels=[5,4,3,2,1])  # Lower recency = higher score
        df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
        df['m_score'] = pd.qcut(df['monetary_value'].rank(method='first'), 5, labels=[1,2,3,4,5])
        
        # Create RFM segments
        def segment_customers(row):
            if row['r_score'] >= 4 and row['f_score'] >= 4 and row['m_score'] >= 4:
                return 'Champions'
            elif row['r_score'] >= 3 and row['f_score'] >= 3 and row['m_score'] >= 3:
                return 'Loyal Customers'
            elif row['r_score'] >= 4 and row['f_score'] <= 2:
                return 'New Customers'
            elif row['r_score'] <= 2 and row['f_score'] >= 3:
                return 'At Risk'
            elif row['r_score'] <= 2 and row['f_score'] <= 2:
                return 'Lost Customers'
            else:
                return 'Potential Loyalists'
        
        df['segment'] = df.apply(segment_customers, axis=1)
        
        # Calculate segment summary
        segment_summary = df.groupby('segment').agg({
            'customer_id': 'count',
            'monetary_value': ['sum', 'mean'],
            'frequency': 'mean',
            'recency_days': 'mean'
        }).round(2)
        
        segments = []
        for segment in segment_summary.index:
            segments.append({
                'segment': segment,
                'customer_count': int(segment_summary.loc[segment, ('customer_id', 'count')]),
                'total_value': float(segment_summary.loc[segment, ('monetary_value', 'sum')]),
                'avg_value': float(segment_summary.loc[segment, ('monetary_value', 'mean')]),
                'avg_frequency': float(segment_summary.loc[segment, ('frequency', 'mean')]),
                'avg_recency': float(segment_summary.loc[segment, ('recency_days', 'mean')])
            })
        
        return {
            "segments": segments,
            "summary": {
                "total_customers": len(df),
                "champions_count": len(df[df['segment'] == 'Champions']),
                "at_risk_count": len(df[df['segment'] == 'At Risk']),
                "lost_customers_count": len(df[df['segment'] == 'Lost Customers'])
            }
        }


def create_financial_reporting_manager(db: Session) -> FinancialReportingManager:
    """Factory function to create financial reporting manager"""
    return FinancialReportingManager(db)
