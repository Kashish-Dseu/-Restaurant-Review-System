#!/usr/bin/env python3
"""
Enhanced Analytics Engine for Restaurant Reviews
Features:
- Comprehensive insights generation
- Trend analysis
- User engagement metrics
- Restaurant comparisons
- Improvement recommendations
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import numpy as np

class Analytics:
    """
    Advanced analytics engine for restaurant reviews
    Generates insights, trends, and actionable data
    """
    
    def __init__(self):
        pass
    
    def generate_insights(self, reviews):
        """
        Generate comprehensive insights from reviews
        """
        if not reviews or len(reviews) == 0:
            return self._empty_insights()
        
        insights = {
            'total_reviews': len(reviews),
            'avg_rating': self._calculate_avg_rating(reviews),
            'sentiment_breakdown': self._get_sentiment_breakdown(reviews),
            'rating_distribution': self._get_rating_distribution(reviews),
            'top_keywords': self._extract_top_keywords(reviews),
            'trends': self._analyze_trends(reviews),
            'user_engagement': self._analyze_user_engagement(reviews),
            'satisfaction_score': self.calculate_satisfaction_score(reviews)
        }
        
        return insights
    
    def _empty_insights(self):
        """Return empty insights structure"""
        return {
            'total_reviews': 0,
            'avg_rating': 0,
            'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
            'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'top_keywords': [],
            'trends': {},
            'user_engagement': {},
            'satisfaction_score': 0
        }
    
    def _calculate_avg_rating(self, reviews):
        """Calculate average rating"""
        ratings = [r['rating'] for r in reviews]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0
    
    def _get_sentiment_breakdown(self, reviews):
        """Get sentiment distribution"""
        sentiments = [r['sentiment'] for r in reviews]
        counter = Counter(sentiments)
        total = len(reviews)
        
        return {
            'positive': round(counter.get('positive', 0) / total * 100, 1),
            'neutral': round(counter.get('neutral', 0) / total * 100, 1),
            'negative': round(counter.get('negative', 0) / total * 100, 1),
            'positive_count': counter.get('positive', 0),
            'neutral_count': counter.get('neutral', 0),
            'negative_count': counter.get('negative', 0)
        }
    
    def _get_rating_distribution(self, reviews):
        """Get distribution of ratings"""
        ratings = [r['rating'] for r in reviews]
        counter = Counter(ratings)
        
        return {
            1: counter.get(1, 0),
            2: counter.get(2, 0),
            3: counter.get(3, 0),
            4: counter.get(4, 0),
            5: counter.get(5, 0)
        }
    
    def _extract_top_keywords(self, reviews, top_n=10):
        """Extract most common keywords across all reviews"""
        all_keywords = []
        
        for review in reviews:
            if review['keywords']:
                try:
                    keywords = json.loads(review['keywords'])
                    all_keywords.extend(keywords)
                except:
                    pass
        
        counter = Counter(all_keywords)
        return [{'word': word, 'count': count} 
                for word, count in counter.most_common(top_n)]
    
    def _analyze_trends(self, reviews):
        """Analyze trends over time"""
        # Group by date
        date_groups = defaultdict(list)
        
        for review in reviews:
            try:
                date_str = review['created_at'].split()[0]  # Get date part
                date_groups[date_str].append(review)
            except:
                pass
        
        # Calculate daily averages
        daily_stats = {}
        for date, day_reviews in date_groups.items():
            ratings = [r['rating'] for r in day_reviews]
            sentiments = [r['sentiment'] for r in day_reviews]
            
            daily_stats[date] = {
                'count': len(day_reviews),
                'avg_rating': round(sum(ratings) / len(ratings), 2),
                'positive_ratio': sum(1 for s in sentiments if s == 'positive') / len(sentiments)
            }
        
        # Sort by date
        sorted_dates = sorted(daily_stats.keys())
        
        return {
            'daily_stats': daily_stats,
            'dates': sorted_dates,
            'total_days': len(sorted_dates)
        }
    
    def _analyze_user_engagement(self, reviews):
        """Analyze user engagement patterns"""
        # Count reviews per user
        user_reviews = defaultdict(int)
        for review in reviews:
            user_reviews[review['user_id']] += 1
        
        review_counts = list(user_reviews.values())
        
        return {
            'total_users': len(user_reviews),
            'avg_reviews_per_user': round(sum(review_counts) / len(review_counts), 2) if review_counts else 0,
            'max_reviews_by_user': max(review_counts) if review_counts else 0,
            'active_users': sum(1 for count in review_counts if count >= 3)
        }
    
    def get_restaurant_comparison(self, restaurants_data):
        """
        Compare multiple restaurants
        restaurants_data: list of {name, reviews} dicts
        """
        comparison = []
        
        for restaurant in restaurants_data:
            if not restaurant['reviews']:
                continue
            
            reviews = restaurant['reviews']
            ratings = [r['rating'] for r in reviews]
            sentiments = [r['sentiment'] for r in reviews]
            
            comparison.append({
                'name': restaurant['name'],
                'total_reviews': len(reviews),
                'avg_rating': round(sum(ratings) / len(ratings), 2),
                'positive_ratio': sum(1 for s in sentiments if s == 'positive') / len(sentiments),
                'negative_ratio': sum(1 for s in sentiments if s == 'negative') / len(sentiments),
                'satisfaction_score': self.calculate_satisfaction_score(reviews)
            })
        
        # Sort by average rating
        comparison.sort(key=lambda x: x['avg_rating'], reverse=True)
        
        return comparison
    
    def identify_improvement_areas(self, reviews):
        """
        Identify areas for improvement based on negative reviews
        """
        negative_reviews = [r for r in reviews if r['sentiment'] == 'negative']
        
        if not negative_reviews:
            return {'message': 'No negative reviews found!', 'keywords': []}
        
        # Extract keywords from negative reviews
        negative_keywords = []
        for review in negative_reviews:
            if review['keywords']:
                try:
                    keywords = json.loads(review['keywords'])
                    negative_keywords.extend(keywords)
                except:
                    pass
        
        counter = Counter(negative_keywords)
        top_issues = [{'issue': word, 'mentions': count} 
                     for word, count in counter.most_common(5)]
        
        return {
            'total_negative_reviews': len(negative_reviews),
            'percentage': round(len(negative_reviews) / len(reviews) * 100, 1),
            'common_issues': top_issues
        }
    
    def calculate_satisfaction_score(self, reviews):
        """
        Calculate overall satisfaction score (0-100)
        Based on ratings and sentiment
        """
        if not reviews:
            return 0
        
        # Weight: 60% from ratings, 40% from sentiment
        ratings = [r['rating'] for r in reviews]
        avg_rating = sum(ratings) / len(ratings)
        rating_score = (avg_rating / 5) * 60
        
        sentiments = [r['sentiment'] for r in reviews]
        positive_ratio = sum(1 for s in sentiments if s == 'positive') / len(sentiments)
        sentiment_score = positive_ratio * 40
        
        total_score = rating_score + sentiment_score
        
        return round(total_score, 1)
    
    def get_quality_metrics(self, reviews):
        """
        Calculate quality metrics for the restaurant
        """
        if not reviews:
            return {}
        
        ratings = [r['rating'] for r in reviews]
        sentiments = [r['sentiment'] for r in reviews]
        
        # Calculate metrics
        avg_rating = sum(ratings) / len(ratings)
        rating_variance = np.var(ratings) if len(ratings) > 1 else 0
        
        positive_count = sum(1 for s in sentiments if s == 'positive')
        negative_count = sum(1 for s in sentiments if s == 'negative')
        
        return {
            'avg_rating': round(avg_rating, 2),
            'rating_consistency': round(1 - min(rating_variance / 5, 1), 2),  # 0-1 scale
            'positive_percentage': round(positive_count / len(sentiments) * 100, 1),
            'negative_percentage': round(negative_count / len(sentiments) * 100, 1),
            'review_count': len(reviews),
            'quality_grade': self._calculate_grade(avg_rating, positive_count / len(sentiments))
        }
    
    def _calculate_grade(self, avg_rating, positive_ratio):
        """Calculate letter grade based on rating and sentiment"""
        score = (avg_rating / 5) * 0.6 + positive_ratio * 0.4
        
        if score >= 0.9:
            return 'A+'
        elif score >= 0.85:
            return 'A'
        elif score >= 0.8:
            return 'A-'
        elif score >= 0.75:
            return 'B+'
        elif score >= 0.7:
            return 'B'
        elif score >= 0.65:
            return 'B-'
        elif score >= 0.6:
            return 'C+'
        elif score >= 0.5:
            return 'C'
        else:
            return 'D'
    
    def get_time_based_insights(self, reviews):
        """
        Generate insights based on temporal patterns
        """
        if not reviews:
            return {}
        
        # Group by date
        date_groups = defaultdict(list)
        for review in reviews:
            try:
                date_str = review['created_at'].split()[0]
                date_groups[date_str].append(review)
            except:
                pass
        
        # Calculate trend
        dates = sorted(date_groups.keys())
        if len(dates) < 2:
            trend = 'stable'
        else:
            recent_ratings = [r['rating'] for r in date_groups[dates[-1]]]
            older_ratings = [r['rating'] for r in date_groups[dates[0]]]
            
            recent_avg = sum(recent_ratings) / len(recent_ratings)
            older_avg = sum(older_ratings) / len(older_ratings)
            
            if recent_avg > older_avg + 0.5:
                trend = 'improving'
            elif recent_avg < older_avg - 0.5:
                trend = 'declining'
            else:
                trend = 'stable'
        
        return {
            'total_days': len(dates),
            'first_review': dates[0] if dates else None,
            'latest_review': dates[-1] if dates else None,
            'trend': trend
        }


# Standalone testing
if __name__ == "__main__":
    print("Testing Enhanced Analytics Engine...\n")
    
    # Sample reviews for testing
    sample_reviews = [
        {'rating': 5, 'sentiment': 'positive', 'keywords': '["excellent", "food", "service"]', 'user_id': 1, 'created_at': '2026-03-15 10:00:00'},
        {'rating': 4, 'sentiment': 'positive', 'keywords': '["good", "tasty", "clean"]', 'user_id': 2, 'created_at': '2026-03-15 11:00:00'},
        {'rating': 2, 'sentiment': 'negative', 'keywords': '["slow", "cold", "expensive"]', 'user_id': 3, 'created_at': '2026-03-15 12:00:00'},
        {'rating': 3, 'sentiment': 'neutral', 'keywords': '["okay", "average"]', 'user_id': 1, 'created_at': '2026-03-16 09:00:00'},
        {'rating': 5, 'sentiment': 'positive', 'keywords': '["amazing", "perfect"]', 'user_id': 4, 'created_at': '2026-03-16 14:00:00'},
    ]
    
    analytics = Analytics()
    insights = analytics.generate_insights(sample_reviews)
    
    print("Analytics Results:")
    print(f"Total Reviews: {insights['total_reviews']}")
    print(f"Average Rating: {insights['avg_rating']}/5")
    print(f"Satisfaction Score: {insights['satisfaction_score']}/100")
    print(f"\nSentiment Breakdown:")
    print(f"  Positive: {insights['sentiment_breakdown']['positive']}%")
    print(f"  Neutral: {insights['sentiment_breakdown']['neutral']}%")
    print(f"  Negative: {insights['sentiment_breakdown']['negative']}%")
