"""
AI Analytics Module for Electronics Store
Includes demand forecasting, price optimization, and automated reorder suggestions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DemandForecaster:
    """AI-powered demand forecasting for inventory management"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.models = {}
        self.scalers = {}
        self.model_path = "models/"
        os.makedirs(self.model_path, exist_ok=True)
    
    def extract_features(self, sales_data: pd.DataFrame) -> pd.DataFrame:
        """Extract features for demand forecasting"""
        features = sales_data.copy()
        
        # Time-based features
        features['day_of_week'] = pd.to_datetime(features['sale_date']).dt.dayofweek
        features['month'] = pd.to_datetime(features['sale_date']).dt.month
        features['quarter'] = pd.to_datetime(features['sale_date']).dt.quarter
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Seasonal features
        features['sin_month'] = np.sin(2 * np.pi * features['month'] / 12)
        features['cos_month'] = np.cos(2 * np.pi * features['month'] / 12)
        features['sin_day'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
        features['cos_day'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
        
        # Lag features (previous sales)
        for lag in [1, 7, 14, 30]:
            features[f'sales_lag_{lag}'] = features.groupby('product_id')['quantity'].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            features[f'sales_mean_{window}'] = features.groupby('product_id')['quantity'].rolling(window).mean().reset_index(0, drop=True)
            features[f'sales_std_{window}'] = features.groupby('product_id')['quantity'].rolling(window).std().reset_index(0, drop=True)
        
        # Price-related features
        if 'price' in features.columns:
            features['price_change'] = features.groupby('product_id')['price'].pct_change()
            features['price_vs_avg'] = features.groupby('product_id')['price'].transform(lambda x: (x - x.mean()) / x.std())
        
        return features
    
    def get_sales_data(self, product_id: Optional[int] = None, days_back: int = 365) -> pd.DataFrame:
        """Retrieve sales data from database"""
        query = """
        SELECT 
            si.product_id,
            s.sale_date,
            si.quantity,
            si.price,
            p.name as product_name,
            p.category_id,
            s.location_id
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.sale_id
        JOIN products p ON si.product_id = p.product_id
        WHERE s.sale_date >= :start_date
        """
        
        params = {'start_date': datetime.now() - timedelta(days=days_back)}
        
        if product_id:
            query += " AND si.product_id = :product_id"
            params['product_id'] = product_id
        
        query += " ORDER BY s.sale_date"
        
        result = self.db.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        if df.empty:
            logger.warning("No sales data found for forecasting")
            return pd.DataFrame()
        
        return df
    
    def train_demand_model(self, product_id: int) -> Dict:
        """Train demand forecasting model for a specific product"""
        try:
            # Get sales data
            sales_data = self.get_sales_data(product_id=product_id)
            
            if len(sales_data) < 30:  # Need minimum data points
                logger.warning(f"Insufficient data for product {product_id}")
                return {"error": "Insufficient historical data"}
            
            # Prepare daily aggregated data
            daily_sales = sales_data.groupby(['product_id', 'sale_date']).agg({
                'quantity': 'sum',
                'price': 'mean'
            }).reset_index()
            
            # Create date range and fill missing dates with 0 sales
            date_range = pd.date_range(
                start=daily_sales['sale_date'].min(),
                end=daily_sales['sale_date'].max(),
                freq='D'
            )
            
            full_dates = pd.DataFrame({
                'sale_date': date_range,
                'product_id': product_id
            })
            
            daily_sales = full_dates.merge(daily_sales, on=['sale_date', 'product_id'], how='left')
            daily_sales['quantity'] = daily_sales['quantity'].fillna(0)
            daily_sales['price'] = daily_sales['price'].fillna(method='ffill')
            
            # Extract features
            features_df = self.extract_features(daily_sales)
            
            # Remove rows with NaN values (from lag features)
            features_df = features_df.dropna()
            
            if len(features_df) < 20:
                return {"error": "Insufficient clean data after feature extraction"}
            
            # Prepare features and target
            feature_columns = [col for col in features_df.columns 
                             if col not in ['sale_date', 'product_id', 'quantity', 'product_name']]
            
            X = features_df[feature_columns]
            y = features_df['quantity']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train multiple models and select best
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression()
            }
            
            best_model = None
            best_score = float('inf')
            best_model_name = None
            
            for name, model in models.items():
                if name == 'linear_regression':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                mae = mean_absolute_error(y_test, y_pred)
                
                if mae < best_score:
                    best_score = mae
                    best_model = model
                    best_model_name = name
            
            # Save model and scaler
            model_filename = f"{self.model_path}demand_model_{product_id}.joblib"
            scaler_filename = f"{self.model_path}scaler_{product_id}.joblib"
            
            joblib.dump(best_model, model_filename)
            joblib.dump(scaler, scaler_filename)
            
            self.models[product_id] = best_model
            self.scalers[product_id] = scaler
            
            return {
                "success": True,
                "model_type": best_model_name,
                "mae": best_score,
                "training_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training demand model for product {product_id}: {str(e)}")
            return {"error": str(e)}
    
    def predict_demand(self, product_id: int, days_ahead: int = 30) -> Dict:
        """Predict demand for a product for the next N days"""
        try:
            # Load model if not in memory
            if product_id not in self.models:
                model_filename = f"{self.model_path}demand_model_{product_id}.joblib"
                scaler_filename = f"{self.model_path}scaler_{product_id}.joblib"
                
                if not os.path.exists(model_filename):
                    # Train model if it doesn't exist
                    train_result = self.train_demand_model(product_id)
                    if "error" in train_result:
                        return train_result
                else:
                    self.models[product_id] = joblib.load(model_filename)
                    self.scalers[product_id] = joblib.load(scaler_filename)
            
            # Get recent sales data for feature generation
            recent_sales = self.get_sales_data(product_id=product_id, days_back=90)
            
            if recent_sales.empty:
                return {"error": "No recent sales data available"}
            
            # Prepare prediction data
            last_date = recent_sales['sale_date'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            predictions = []
            
            for date in future_dates:
                # Create feature row for this date
                feature_row = {
                    'product_id': product_id,
                    'sale_date': date,
                    'day_of_week': date.dayofweek,
                    'month': date.month,
                    'quarter': date.quarter,
                    'is_weekend': 1 if date.dayofweek in [5, 6] else 0,
                    'sin_month': np.sin(2 * np.pi * date.month / 12),
                    'cos_month': np.cos(2 * np.pi * date.month / 12),
                    'sin_day': np.sin(2 * np.pi * date.dayofweek / 7),
                    'cos_day': np.cos(2 * np.pi * date.dayofweek / 7)
                }
                
                # Add lag features from recent sales
                recent_quantities = recent_sales['quantity'].tail(30).values
                if len(recent_quantities) >= 1:
                    feature_row['sales_lag_1'] = recent_quantities[-1]
                if len(recent_quantities) >= 7:
                    feature_row['sales_lag_7'] = recent_quantities[-7]
                if len(recent_quantities) >= 14:
                    feature_row['sales_lag_14'] = recent_quantities[-14]
                if len(recent_quantities) >= 30:
                    feature_row['sales_lag_30'] = recent_quantities[-30]
                
                # Add rolling statistics
                if len(recent_quantities) >= 7:
                    feature_row['sales_mean_7'] = np.mean(recent_quantities[-7:])
                    feature_row['sales_std_7'] = np.std(recent_quantities[-7:])
                if len(recent_quantities) >= 14:
                    feature_row['sales_mean_14'] = np.mean(recent_quantities[-14:])
                    feature_row['sales_std_14'] = np.std(recent_quantities[-14:])
                if len(recent_quantities) >= 30:
                    feature_row['sales_mean_30'] = np.mean(recent_quantities[-30:])
                    feature_row['sales_std_30'] = np.std(recent_quantities[-30:])
                
                # Fill missing values with 0
                for key in ['sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_30',
                           'sales_mean_7', 'sales_std_7', 'sales_mean_14', 'sales_std_14',
                           'sales_mean_30', 'sales_std_30']:
                    if key not in feature_row:
                        feature_row[key] = 0
                
                # Create feature vector
                feature_columns = [col for col in feature_row.keys() 
                                 if col not in ['sale_date', 'product_id']]
                
                X = np.array([feature_row[col] for col in feature_columns]).reshape(1, -1)
                
                # Scale if using linear regression
                model = self.models[product_id]
                if hasattr(model, 'coef_'):  # Linear regression
                    X = self.scalers[product_id].transform(X)
                
                # Make prediction
                pred = model.predict(X)[0]
                pred = max(0, pred)  # Ensure non-negative
                
                predictions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted_demand': round(pred, 2)
                })
            
            total_predicted = sum([p['predicted_demand'] for p in predictions])
            
            return {
                "success": True,
                "product_id": product_id,
                "predictions": predictions,
                "total_predicted_demand": round(total_predicted, 2),
                "average_daily_demand": round(total_predicted / days_ahead, 2)
            }
            
        except Exception as e:
            logger.error(f"Error predicting demand for product {product_id}: {str(e)}")
            return {"error": str(e)}

class PriceOptimizer:
    """AI-powered price optimization"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_price_elasticity(self, product_id: int) -> Dict:
        """Calculate price elasticity of demand"""
        try:
            query = """
            SELECT 
                si.price,
                si.quantity,
                s.sale_date
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE si.product_id = :product_id
            AND s.sale_date >= :start_date
            ORDER BY s.sale_date
            """
            
            result = self.db.execute(text(query), {
                'product_id': product_id,
                'start_date': datetime.now() - timedelta(days=180)
            })
            
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            if len(df) < 10:
                return {"error": "Insufficient price variation data"}
            
            # Group by price ranges to get demand at different price points
            df['price_range'] = pd.cut(df['price'], bins=5)
            price_demand = df.groupby('price_range').agg({
                'quantity': 'sum',
                'price': 'mean'
            }).reset_index()
            
            # Calculate elasticity using log-log regression
            price_demand = price_demand.dropna()
            
            if len(price_demand) < 3:
                return {"error": "Insufficient price points for elasticity calculation"}
            
            log_price = np.log(price_demand['price'])
            log_quantity = np.log(price_demand['quantity'] + 1)  # Add 1 to avoid log(0)
            
            # Fit linear regression on log-log data
            model = LinearRegression()
            model.fit(log_price.values.reshape(-1, 1), log_quantity)
            
            elasticity = model.coef_[0]
            
            return {
                "success": True,
                "price_elasticity": round(elasticity, 3),
                "interpretation": self._interpret_elasticity(elasticity),
                "data_points": len(price_demand)
            }
            
        except Exception as e:
            logger.error(f"Error calculating price elasticity for product {product_id}: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_elasticity(self, elasticity: float) -> str:
        """Interpret price elasticity value"""
        if elasticity > 0:
            return "Unusual: Positive elasticity (demand increases with price)"
        elif elasticity > -0.5:
            return "Inelastic: Demand is relatively insensitive to price changes"
        elif elasticity > -1:
            return "Moderately elastic: Demand responds to price changes"
        else:
            return "Highly elastic: Demand is very sensitive to price changes"
    
    def optimize_price(self, product_id: int, current_cost: float, target_margin: float = 0.3) -> Dict:
        """Suggest optimal price based on elasticity and profit maximization"""
        try:
            # Get current product info
            query = """
            SELECT price, cost, name FROM products WHERE product_id = :product_id
            """
            result = self.db.execute(text(query), {'product_id': product_id})
            product = result.fetchone()
            
            if not product:
                return {"error": "Product not found"}
            
            current_price = float(product.price)
            cost = float(product.cost or current_cost)
            
            # Get price elasticity
            elasticity_result = self.get_price_elasticity(product_id)
            
            if "error" in elasticity_result:
                # Use default elasticity if calculation fails
                elasticity = -1.0
            else:
                elasticity = elasticity_result["price_elasticity"]
            
            # Get recent sales volume
            query = """
            SELECT AVG(daily_quantity) as avg_daily_sales
            FROM (
                SELECT DATE(s.sale_date) as sale_date, SUM(si.quantity) as daily_quantity
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
                WHERE si.product_id = :product_id
                AND s.sale_date >= :start_date
                GROUP BY DATE(s.sale_date)
            ) daily_sales
            """
            
            result = self.db.execute(text(query), {
                'product_id': product_id,
                'start_date': datetime.now() - timedelta(days=30)
            })
            
            avg_sales = result.fetchone()
            base_demand = float(avg_sales[0] or 1)
            
            # Price optimization using profit maximization
            # Profit = (Price - Cost) * Quantity
            # Quantity = Base_Demand * (Price/Current_Price)^elasticity
            
            def profit_function(price):
                if price <= cost:
                    return 0
                quantity = base_demand * ((price / current_price) ** elasticity)
                return (price - cost) * quantity
            
            # Test different price points
            price_range = np.linspace(cost * 1.1, current_price * 2, 100)
            profits = [profit_function(p) for p in price_range]
            
            optimal_idx = np.argmax(profits)
            optimal_price = price_range[optimal_idx]
            max_profit = profits[optimal_idx]
            
            # Calculate metrics
            optimal_margin = (optimal_price - cost) / optimal_price
            current_profit = profit_function(current_price)
            profit_improvement = ((max_profit - current_profit) / current_profit * 100) if current_profit > 0 else 0
            
            # Alternative: Target margin price
            target_price = cost / (1 - target_margin)
            target_profit = profit_function(target_price)
            
            return {
                "success": True,
                "current_price": round(current_price, 2),
                "optimal_price": round(optimal_price, 2),
                "target_margin_price": round(target_price, 2),
                "current_margin": round((current_price - cost) / current_price, 3),
                "optimal_margin": round(optimal_margin, 3),
                "profit_improvement_percent": round(profit_improvement, 1),
                "price_elasticity": round(elasticity, 3),
                "recommendation": self._generate_price_recommendation(
                    current_price, optimal_price, target_price, elasticity
                )
            }
            
        except Exception as e:
            logger.error(f"Error optimizing price for product {product_id}: {str(e)}")
            return {"error": str(e)}
    
    def _generate_price_recommendation(self, current: float, optimal: float, 
                                     target: float, elasticity: float) -> str:
        """Generate human-readable price recommendation"""
        if abs(optimal - current) / current < 0.05:
            return "Current price is near optimal. Consider minor adjustments based on market conditions."
        elif optimal > current:
            increase_pct = (optimal - current) / current * 100
            return f"Consider increasing price by {increase_pct:.1f}% to ${optimal:.2f} for maximum profit."
        else:
            decrease_pct = (current - optimal) / current * 100
            return f"Consider decreasing price by {decrease_pct:.1f}% to ${optimal:.2f} to increase volume and profit."

class AutoReorderSystem:
    """Automated reorder suggestion system"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.demand_forecaster = DemandForecaster(db_session)
    
    def calculate_reorder_point(self, product_id: int, location_id: int, 
                               service_level: float = 0.95) -> Dict:
        """Calculate optimal reorder point using demand forecasting"""
        try:
            # Get demand forecast
            demand_forecast = self.demand_forecaster.predict_demand(product_id, days_ahead=30)
            
            if "error" in demand_forecast:
                # Fallback to simple calculation
                return self._simple_reorder_calculation(product_id, location_id)
            
            # Get lead time (assume 7 days if not specified)
            lead_time_days = 7
            
            # Calculate average daily demand
            avg_daily_demand = demand_forecast["average_daily_demand"]
            
            # Get demand variability from historical data
            query = """
            SELECT 
                DATE(s.sale_date) as sale_date,
                SUM(si.quantity) as daily_quantity
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE si.product_id = :product_id
            AND s.location_id = :location_id
            AND s.sale_date >= :start_date
            GROUP BY DATE(s.sale_date)
            """
            
            result = self.db.execute(text(query), {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': datetime.now() - timedelta(days=90)
            })
            
            daily_sales = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            if len(daily_sales) < 10:
                demand_std = avg_daily_demand * 0.3  # Assume 30% coefficient of variation
            else:
                demand_std = daily_sales['daily_quantity'].std()
            
            # Calculate safety stock using normal distribution
            from scipy.stats import norm
            z_score = norm.ppf(service_level)
            safety_stock = z_score * demand_std * np.sqrt(lead_time_days)
            
            # Reorder point = Lead time demand + Safety stock
            lead_time_demand = avg_daily_demand * lead_time_days
            reorder_point = lead_time_demand + safety_stock
            
            # Calculate economic order quantity (EOQ)
            # Simplified EOQ assuming holding cost = 20% of item cost per year
            query = """SELECT cost, price FROM products WHERE product_id = :product_id"""
            result = self.db.execute(text(query), {'product_id': product_id})
            product = result.fetchone()
            
            if product and product.cost:
                annual_demand = avg_daily_demand * 365
                holding_cost_per_unit = float(product.cost) * 0.20  # 20% holding cost
                ordering_cost = 50  # Assume $50 per order
                
                eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
            else:
                eoq = avg_daily_demand * 30  # 30-day supply as fallback
            
            return {
                "success": True,
                "product_id": product_id,
                "location_id": location_id,
                "reorder_point": round(reorder_point, 0),
                "safety_stock": round(safety_stock, 0),
                "economic_order_quantity": round(eoq, 0),
                "lead_time_demand": round(lead_time_demand, 1),
                "average_daily_demand": round(avg_daily_demand, 2),
                "service_level": service_level,
                "recommendation": f"Reorder when stock reaches {round(reorder_point, 0)} units. Order {round(eoq, 0)} units each time."
            }
            
        except Exception as e:
            logger.error(f"Error calculating reorder point: {str(e)}")
            return {"error": str(e)}
    
    def _simple_reorder_calculation(self, product_id: int, location_id: int) -> Dict:
        """Simple reorder calculation when AI forecasting fails"""
        try:
            # Get average sales over last 30 days
            query = """
            SELECT AVG(daily_quantity) as avg_daily_sales
            FROM (
                SELECT DATE(s.sale_date) as sale_date, SUM(si.quantity) as daily_quantity
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
                WHERE si.product_id = :product_id
                AND s.location_id = :location_id
                AND s.sale_date >= :start_date
                GROUP BY DATE(s.sale_date)
            ) daily_sales
            """
            
            result = self.db.execute(text(query), {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': datetime.now() - timedelta(days=30)
            })
            
            avg_sales = result.fetchone()
            daily_demand = float(avg_sales[0] or 0.1)
            
            # Simple calculation: 14 days of demand + 50% safety stock
            reorder_point = daily_demand * 14 * 1.5
            order_quantity = daily_demand * 30  # 30-day supply
            
            return {
                "success": True,
                "product_id": product_id,
                "location_id": location_id,
                "reorder_point": round(reorder_point, 0),
                "economic_order_quantity": round(order_quantity, 0),
                "average_daily_demand": round(daily_demand, 2),
                "method": "simple",
                "recommendation": f"Reorder when stock reaches {round(reorder_point, 0)} units. Order {round(order_quantity, 0)} units each time."
            }
            
        except Exception as e:
            logger.error(f"Error in simple reorder calculation: {str(e)}")
            return {"error": str(e)}
    
    def generate_reorder_suggestions(self, location_id: Optional[int] = None) -> List[Dict]:
        """Generate reorder suggestions for all products or specific location"""
        try:
            # Get products that need reordering
            query = """
            SELECT 
                pl.product_id,
                pl.location_id,
                pl.stock_quantity,
                p.name,
                p.reorder_level,
                p.reorder_quantity
            FROM product_locations pl
            JOIN products p ON pl.product_id = p.product_id
            WHERE pl.stock_quantity <= p.reorder_level
            """
            
            params = {}
            if location_id:
                query += " AND pl.location_id = :location_id"
                params['location_id'] = location_id
            
            result = self.db.execute(text(query), params)
            low_stock_products = result.fetchall()
            
            suggestions = []
            
            for product in low_stock_products:
                # Calculate optimal reorder parameters
                reorder_calc = self.calculate_reorder_point(
                    product.product_id, 
                    product.location_id
                )
                
                if "error" not in reorder_calc:
                    suggestion = {
                        "product_id": product.product_id,
                        "product_name": product.name,
                        "location_id": product.location_id,
                        "current_stock": product.stock_quantity,
                        "reorder_level": product.reorder_level,
                        "suggested_reorder_point": reorder_calc["reorder_point"],
                        "suggested_order_quantity": reorder_calc["economic_order_quantity"],
                        "current_reorder_quantity": product.reorder_quantity,
                        "priority": self._calculate_priority(product.stock_quantity, product.reorder_level),
                        "recommendation": reorder_calc["recommendation"]
                    }
                    suggestions.append(suggestion)
            
            # Sort by priority (most urgent first)
            suggestions.sort(key=lambda x: x["priority"], reverse=True)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating reorder suggestions: {str(e)}")
            return []
    
    def _calculate_priority(self, current_stock: int, reorder_level: int) -> int:
        """Calculate priority score for reordering (higher = more urgent)"""
        if current_stock <= 0:
            return 100  # Critical - out of stock
        elif current_stock <= reorder_level * 0.5:
            return 80   # High priority
        elif current_stock <= reorder_level * 0.75:
            return 60   # Medium priority
        else:
            return 40   # Low priority

# Factory function to create AI analytics instances
def create_ai_analytics(db_session: Session) -> Dict:
    """Create AI analytics instances"""
    return {
        "demand_forecaster": DemandForecaster(db_session),
        "price_optimizer": PriceOptimizer(db_session),
        "auto_reorder": AutoReorderSystem(db_session)
    }
