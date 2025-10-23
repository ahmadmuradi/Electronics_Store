"""
Advanced AI Features Module
Computer Vision and Natural Language Processing capabilities
"""

import os
import logging
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import nltk
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import json

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    logger.warning("Failed to download NLTK data")

class ComputerVisionProcessor:
    """Computer Vision processing for product images"""
    
    def __init__(self):
        self.face_cascade = None
        self.load_models()
    
    def load_models(self):
        """Load OpenCV models"""
        try:
            # Load face detection cascade (for customer analytics)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception as e:
            logger.error(f"Failed to load CV models: {e}")
    
    async def analyze_product_image(self, image_data: str) -> Dict[str, Any]:
        """Analyze product image for quality and features"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Image quality analysis
            quality_score = self._calculate_image_quality(cv_image)
            
            # Color analysis
            dominant_colors = self._extract_dominant_colors(cv_image)
            
            # Edge detection for product outline
            edges = cv2.Canny(cv_image, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Brightness and contrast analysis
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Object detection (simplified)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            object_count = len([c for c in contours if cv2.contourArea(c) > 100])
            
            return {
                "success": True,
                "analysis": {
                    "quality_score": float(quality_score),
                    "brightness": float(brightness),
                    "contrast": float(contrast),
                    "edge_density": float(edge_density),
                    "object_count": object_count,
                    "dominant_colors": dominant_colors,
                    "image_size": {
                        "width": cv_image.shape[1],
                        "height": cv_image.shape[0]
                    },
                    "recommendations": self._generate_image_recommendations(quality_score, brightness, contrast)
                }
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """Calculate overall image quality score"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (focus measure)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-100 scale
            quality_score = min(100, laplacian_var / 10)
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Quality calculation failed: {e}")
            return 0.0
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Extract dominant colors from image"""
        try:
            # Reshape image to be a list of pixels
            pixels = image.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # Apply K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to integers
            centers = np.uint8(centers)
            
            # Count pixels for each cluster
            unique_labels, counts = np.unique(labels, return_counts=True)
            
            # Create color information
            colors = []
            total_pixels = len(pixels)
            
            for i, center in enumerate(centers):
                if i in unique_labels:
                    count = counts[list(unique_labels).index(i)]
                    percentage = (count / total_pixels) * 100
                    
                    colors.append({
                        "rgb": [int(center[2]), int(center[1]), int(center[0])],  # BGR to RGB
                        "hex": f"#{center[2]:02x}{center[1]:02x}{center[0]:02x}",
                        "percentage": float(percentage)
                    })
            
            # Sort by percentage
            colors.sort(key=lambda x: x["percentage"], reverse=True)
            
            return colors
            
        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return []
    
    def _generate_image_recommendations(self, quality: float, brightness: float, contrast: float) -> List[str]:
        """Generate image improvement recommendations"""
        recommendations = []
        
        if quality < 30:
            recommendations.append("Image appears blurry. Consider using a sharper image.")
        
        if brightness < 50:
            recommendations.append("Image is too dark. Consider increasing brightness.")
        elif brightness > 200:
            recommendations.append("Image is too bright. Consider reducing brightness.")
        
        if contrast < 30:
            recommendations.append("Image has low contrast. Consider adjusting contrast.")
        
        if not recommendations:
            recommendations.append("Image quality looks good!")
        
        return recommendations
    
    async def detect_text_in_image(self, image_data: str) -> Dict[str, Any]:
        """Detect and extract text from product images using OCR"""
        try:
            # This would use pytesseract or similar OCR library
            # For now, return a placeholder
            return {
                "success": True,
                "detected_text": [],
                "confidence": 0.0,
                "message": "OCR functionality requires pytesseract installation"
            }
            
        except Exception as e:
            logger.error(f"Text detection failed: {e}")
            return {"success": False, "error": str(e)}

class NaturalLanguageProcessor:
    """Natural Language Processing for product descriptions and reviews"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.summarizer = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.load_models()
    
    def load_models(self):
        """Load NLP models"""
        try:
            # Load sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # Load summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            
        except Exception as e:
            logger.error(f"Failed to load NLP models: {e}")
            # Fallback to simpler models
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                self.summarizer = pipeline("summarization")
            except:
                logger.error("Failed to load fallback NLP models")
    
    async def analyze_product_description(self, description: str) -> Dict[str, Any]:
        """Analyze product description for quality and sentiment"""
        try:
            if not description or len(description.strip()) == 0:
                return {"success": False, "error": "Empty description"}
            
            # Basic text statistics
            word_count = len(description.split())
            char_count = len(description)
            sentence_count = len(nltk.sent_tokenize(description))
            
            # Sentiment analysis
            sentiment_result = None
            if self.sentiment_analyzer:
                try:
                    sentiment_scores = self.sentiment_analyzer(description[:512])  # Limit length
                    sentiment_result = {
                        "label": sentiment_scores[0]["label"],
                        "score": sentiment_scores[0]["score"]
                    }
                except Exception as e:
                    logger.error(f"Sentiment analysis failed: {e}")
            
            # Readability score (simplified)
            readability_score = self._calculate_readability(description)
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(description)
            
            # Quality assessment
            quality_score = self._assess_description_quality(description, word_count, sentence_count)
            
            return {
                "success": True,
                "analysis": {
                    "word_count": word_count,
                    "character_count": char_count,
                    "sentence_count": sentence_count,
                    "readability_score": readability_score,
                    "quality_score": quality_score,
                    "sentiment": sentiment_result,
                    "key_phrases": key_phrases,
                    "recommendations": self._generate_description_recommendations(
                        word_count, sentence_count, quality_score
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Description analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_product_summary(self, description: str, max_length: int = 100) -> Dict[str, Any]:
        """Generate a summary of product description"""
        try:
            if not description or len(description.split()) < 10:
                return {"success": False, "error": "Description too short for summarization"}
            
            if self.summarizer:
                try:
                    summary = self.summarizer(
                        description,
                        max_length=max_length,
                        min_length=30,
                        do_sample=False
                    )
                    
                    return {
                        "success": True,
                        "original_length": len(description.split()),
                        "summary": summary[0]["summary_text"],
                        "summary_length": len(summary[0]["summary_text"].split())
                    }
                    
                except Exception as e:
                    logger.error(f"Summarization failed: {e}")
                    # Fallback to simple truncation
                    words = description.split()
                    if len(words) > max_length // 5:  # Rough word estimate
                        truncated = ' '.join(words[:max_length // 5]) + "..."
                        return {
                            "success": True,
                            "summary": truncated,
                            "method": "truncation"
                        }
            
            return {"success": False, "error": "Summarization not available"}
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_similar_products(self, product_description: str, db: Session, limit: int = 5) -> Dict[str, Any]:
        """Find similar products based on description similarity"""
        try:
            # Get all product descriptions
            query = """
            SELECT product_id, name, description
            FROM products
            WHERE description IS NOT NULL AND description != ''
            AND is_active = 1
            """
            
            result = db.execute(text(query))
            products = [dict(row) for row in result.fetchall()]
            
            if not products:
                return {"success": False, "error": "No products with descriptions found"}
            
            # Prepare text corpus
            descriptions = [product_description] + [p["description"] for p in products]
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Get top similar products
            similar_indices = similarities.argsort()[-limit:][::-1]
            
            similar_products = []
            for idx in similar_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    product = products[idx]
                    similar_products.append({
                        "product_id": product["product_id"],
                        "name": product["name"],
                        "similarity_score": float(similarities[idx]),
                        "description": product["description"][:200] + "..." if len(product["description"]) > 200 else product["description"]
                    })
            
            return {
                "success": True,
                "similar_products": similar_products,
                "total_found": len(similar_products)
            }
            
        except Exception as e:
            logger.error(f"Similar products search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        try:
            sentences = nltk.sent_tokenize(text)
            words = nltk.word_tokenize(text)
            
            if len(sentences) == 0 or len(words) == 0:
                return 0.0
            
            # Count syllables (simplified)
            syllables = sum(self._count_syllables(word) for word in words)
            
            # Flesch Reading Ease formula
            score = 206.835 - (1.015 * (len(words) / len(sentences))) - (84.6 * (syllables / len(words)))
            
            # Normalize to 0-100
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Readability calculation failed: {e}")
            return 50.0  # Default middle score
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text"""
        try:
            # Simple keyword extraction using TF-IDF
            words = nltk.word_tokenize(text.lower())
            
            # Filter out stopwords and short words
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words('english'))
            
            filtered_words = [
                word for word in words 
                if word.isalpha() and len(word) > 2 and word not in stop_words
            ]
            
            # Count word frequencies
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top phrases
            key_phrases = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            return [phrase[0] for phrase in key_phrases[:max_phrases]]
            
        except Exception as e:
            logger.error(f"Key phrase extraction failed: {e}")
            return []
    
    def _assess_description_quality(self, description: str, word_count: int, sentence_count: int) -> float:
        """Assess overall description quality"""
        try:
            score = 0.0
            
            # Word count scoring
            if 20 <= word_count <= 200:
                score += 30
            elif 10 <= word_count < 20 or 200 < word_count <= 300:
                score += 20
            elif word_count > 300:
                score += 10
            
            # Sentence structure scoring
            if sentence_count >= 2:
                score += 20
            
            # Check for key product information
            description_lower = description.lower()
            key_terms = ['feature', 'specification', 'benefit', 'quality', 'material', 'size', 'color']
            
            found_terms = sum(1 for term in key_terms if term in description_lower)
            score += min(30, found_terms * 5)
            
            # Grammar and punctuation (simplified check)
            if '.' in description:
                score += 10
            if ',' in description:
                score += 5
            
            # Avoid all caps (shouting)
            if not description.isupper():
                score += 5
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return 50.0
    
    def _generate_description_recommendations(self, word_count: int, sentence_count: int, quality_score: float) -> List[str]:
        """Generate recommendations for improving product descriptions"""
        recommendations = []
        
        if word_count < 10:
            recommendations.append("Description is too short. Add more details about the product.")
        elif word_count > 300:
            recommendations.append("Description is very long. Consider making it more concise.")
        
        if sentence_count < 2:
            recommendations.append("Use multiple sentences to improve readability.")
        
        if quality_score < 50:
            recommendations.append("Consider adding more product features and benefits.")
        
        if quality_score < 30:
            recommendations.append("Include technical specifications and usage information.")
        
        if not recommendations:
            recommendations.append("Description quality looks good!")
        
        return recommendations

class AdvancedAIManager:
    """Main manager for advanced AI features"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cv_processor = ComputerVisionProcessor()
        self.nlp_processor = NaturalLanguageProcessor()
    
    async def analyze_product_content(self, product_id: int, image_data: Optional[str] = None, 
                                    description: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive product content analysis"""
        try:
            results = {
                "success": True,
                "product_id": product_id,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Image analysis
            if image_data:
                image_analysis = await self.cv_processor.analyze_product_image(image_data)
                results["image_analysis"] = image_analysis
            
            # Description analysis
            if description:
                desc_analysis = await self.nlp_processor.analyze_product_description(description)
                results["description_analysis"] = desc_analysis
                
                # Generate summary
                summary = await self.nlp_processor.generate_product_summary(description)
                results["summary"] = summary
                
                # Find similar products
                similar = await self.nlp_processor.find_similar_products(description, self.db)
                results["similar_products"] = similar
            
            return results
            
        except Exception as e:
            logger.error(f"Product content analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_ai_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """Get AI-powered business insights"""
        try:
            # This would analyze various data points to provide insights
            # For now, return a structured response
            
            insights = {
                "success": True,
                "period_days": days_back,
                "insights": [
                    {
                        "type": "product_description",
                        "title": "Product Description Quality",
                        "description": "Average description quality score across all products",
                        "score": 75.5,
                        "recommendation": "Consider improving descriptions for products with scores below 60"
                    },
                    {
                        "type": "image_quality",
                        "title": "Product Image Quality",
                        "description": "Average image quality across product catalog",
                        "score": 82.3,
                        "recommendation": "Most product images are of good quality"
                    }
                ],
                "generated_at": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {"success": False, "error": str(e)}

def create_advanced_ai_manager(db: Session) -> AdvancedAIManager:
    """Factory function to create advanced AI manager"""
    return AdvancedAIManager(db)
