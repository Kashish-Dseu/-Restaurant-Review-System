#!/usr/bin/env python3
"""
Enhanced Sentiment Analyzer for Restaurant Reviews
Features:
- Expanded keyword dictionaries
- Polarity scoring with intensifiers
- Negation handling
- Keyword extraction
- Confidence scoring
- Batch processing
"""

import re
from collections import Counter
import numpy as np

class SentimentAnalyzer:
    """
    ML-based sentiment analyzer for restaurant reviews
    Uses polarity scoring, keyword extraction, and confidence metrics
    """
    
    def __init__(self):
        # Comprehensive stop words to exclude from keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their', 'this',
            'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our',
            'also', 'just', 'get', 'got', 'went', 'came', 'very', 'really', 'so',
            'too', 'quite', 'much', 'many', 'some', 'any', 'all', 'each', 'every'
        }
        
        # Expanded positive keywords for sentiment analysis
        self.positive_words = {
            # Quality
            'excellent', 'amazing', 'wonderful', 'fantastic', 'great', 'good',
            'delicious', 'tasty', 'perfect', 'outstanding', 'superb', 'brilliant',
            'awesome', 'best', 'incredible', 'impressive', 'beautiful', 'magnificent',
            'exceptional', 'phenomenal', 'spectacular', 'marvelous', 'splendid',
            
            # Food Quality
            'fresh', 'flavorful', 'savory', 'tender', 'juicy', 'crispy', 'creamy',
            'authentic', 'homemade', 'quality', 'premium', 'gourmet', 'delightful',
            'mouthwatering', 'scrumptious', 'yummy', 'heavenly',
            
            # Service & Experience
            'friendly', 'helpful', 'attentive', 'professional', 'courteous', 'polite',
            'welcoming', 'warm', 'accommodating', 'efficient', 'prompt', 'quick',
            
            # Atmosphere
            'clean', 'cozy', 'comfortable', 'elegant', 'charming', 'inviting',
            'pleasant', 'nice', 'lovely', 'gorgeous', 'stunning',
            
            # Recommendation
            'recommend', 'love', 'loved', 'favorite', 'enjoyable', 'satisfied',
            'happy', 'pleased', 'delighted', 'thrilled', 'worth', 'worthwhile',
            
            # Value
            'affordable', 'reasonable', 'value', 'bargain', 'worth'
        }
        
        # Expanded negative keywords for sentiment analysis
        self.negative_words = {
            # Quality
            'terrible', 'awful', 'horrible', 'bad', 'poor', 'worst', 'disappointing',
            'disappointed', 'disgusting', 'nasty', 'mediocre', 'subpar', 'underwhelming',
            'lacking', 'inferior', 'unacceptable', 'pathetic', 'dreadful', 'appalling',
            
            # Food Quality
            'bland', 'tasteless', 'flavorless', 'stale', 'soggy', 'burnt', 'undercooked',
            'overcooked', 'cold', 'lukewarm', 'greasy', 'oily', 'salty', 'dry',
            'rubbery', 'tough', 'chewy', 'gross', 'inedible',
            
            # Service
            'rude', 'slow', 'unprofessional', 'disorganized', 'incompetent', 'careless',
            'inattentive', 'dismissive', 'unfriendly', 'unhelpful',
            
            # Atmosphere
            'dirty', 'filthy', 'unclean', 'messy', 'cramped', 'uncomfortable', 'noisy',
            'crowded', 'dark', 'dingy',
            
            # Experience
            'unpleasant', 'hate', 'hated', 'avoid', 'never', 'waste', 'regret',
            'complained', 'complaint', 'problem', 'issue', 'wrong',
            
            # Value
            'overpriced', 'expensive', 'costly', 'pricey', 'rip', 'ripoff', 'robbery'
        }
        
        # Intensifiers that strengthen sentiment
        self.intensifiers = {
            'very', 'extremely', 'absolutely', 'really', 'truly', 'incredibly',
            'particularly', 'especially', 'remarkably', 'exceptionally', 'utterly',
            'totally', 'completely', 'highly', 'super', 'quite'
        }
        
        # Negations that flip sentiment
        self.negations = {
            'not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere',
            'hardly', 'barely', 'scarcely', "don't", "doesn't", "didn't",
            "won't", "wouldn't", "can't", "cannot", "couldn't"
        }
    
    def clean_text(self, text):
        """Clean and normalize text while preserving important punctuation"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep spaces and some punctuation
        text = re.sub(r'[^a-zA-Z\s\'\-]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def handle_negations(self, words):
        """
        Handle negations by marking words after negation markers
        Returns list of tuples: (word, is_negated)
        """
        result = []
        negated = False
        
        for word in words:
            if word in self.negations:
                negated = True
                result.append((word, False))
            else:
                result.append((word, negated))
                # Reset negation after a few words
                if len(result) > 3:
                    negated = False
        
        return result
    
    def calculate_polarity(self, text):
        """
        Calculate sentiment polarity score with negation handling
        Returns a score between -1 (negative) and 1 (positive)
        """
        words = text.split()
        
        # Handle negations
        words_with_negation = self.handle_negations(words)
        
        positive_count = 0
        negative_count = 0
        intensifier_active = False
        intensifier_multiplier = 1.0
        
        for i, (word, is_negated) in enumerate(words_with_negation):
            # Check for intensifiers
            if word in self.intensifiers:
                intensifier_active = True
                intensifier_multiplier = 1.5
                continue
            
            # Calculate sentiment with intensifier
            multiplier = intensifier_multiplier if intensifier_active else 1.0
            
            if word in self.positive_words:
                if is_negated:
                    negative_count += multiplier  # Negated positive = negative
                else:
                    positive_count += multiplier
            elif word in self.negative_words:
                if is_negated:
                    positive_count += multiplier  # Negated negative = positive
                else:
                    negative_count += multiplier
            
            # Reset intensifier after applying
            if word not in self.intensifiers:
                intensifier_active = False
                intensifier_multiplier = 1.0
        
        # Calculate polarity
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return 0.0
        
        polarity = (positive_count - negative_count) / total_sentiment_words
        
        # Normalize to [-1, 1]
        polarity = max(-1, min(1, polarity))
        
        return polarity
    
    def extract_keywords(self, text, top_n=5):
        """Extract important keywords from the review"""
        words = text.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words 
                   if word not in self.stop_words 
                   and len(word) > 3
                   and not word in self.intensifiers
                   and not word in self.negations]
        
        # Count frequency
        word_counts = Counter(keywords)
        
        # Get top N keywords
        top_keywords = [word for word, count in word_counts.most_common(top_n)]
        
        # Add sentiment-relevant words even if not most frequent
        sentiment_keywords = [word for word in words 
                            if word in self.positive_words or word in self.negative_words]
        
        # Combine and remove duplicates while maintaining order
        all_keywords = list(dict.fromkeys(top_keywords + sentiment_keywords))[:top_n]
        
        return all_keywords
    
    def calculate_confidence(self, polarity, text_length):
        """
        Calculate confidence score based on polarity strength and text length
        Returns value between 0 and 1
        """
        # Base confidence from polarity strength
        polarity_confidence = abs(polarity)
        
        # Length-based confidence (longer reviews = more confident)
        if text_length < 20:
            length_factor = 0.5
        elif text_length < 50:
            length_factor = 0.7
        elif text_length < 200:
            length_factor = 1.0
        else:
            length_factor = 0.9  # Very long reviews might be rambling
        
        # Combined confidence
        confidence = polarity_confidence * length_factor
        
        return min(1.0, confidence)
    
    def analyze(self, text):
        """
        Main sentiment analysis function
        Returns: {
            'sentiment': 'positive'|'neutral'|'negative',
            'score': float (-1 to 1),
            'keywords': list,
            'confidence': float (0 to 1)
        }
        """
        if not text or len(text.strip()) == 0:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'keywords': [],
                'confidence': 0.0
            }
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Calculate polarity
        polarity = self.calculate_polarity(cleaned_text)
        
        # Determine sentiment category
        if polarity > 0.15:
            sentiment = 'positive'
        elif polarity < -0.15:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence
        confidence = self.calculate_confidence(polarity, len(text))
        
        # Extract keywords
        keywords = self.extract_keywords(cleaned_text)
        
        return {
            'sentiment': sentiment,
            'score': round(polarity, 3),
            'keywords': keywords,
            'confidence': round(confidence, 3)
        }
    
    def batch_analyze(self, texts):
        """
        Analyze multiple texts at once
        Returns list of analysis results
        """
        return [self.analyze(text) for text in texts]
    
    def get_sentiment_distribution(self, results):
        """
        Get distribution of sentiments from analysis results
        Returns percentages and counts
        """
        sentiments = [r['sentiment'] for r in results]
        counter = Counter(sentiments)
        total = len(results)
        
        return {
            'positive': counter.get('positive', 0) / total if total > 0 else 0,
            'neutral': counter.get('neutral', 0) / total if total > 0 else 0,
            'negative': counter.get('negative', 0) / total if total > 0 else 0,
            'positive_count': counter.get('positive', 0),
            'neutral_count': counter.get('neutral', 0),
            'negative_count': counter.get('negative', 0),
            'total_reviews': total
        }
    
    def get_average_score(self, results):
        """Calculate average sentiment score from multiple results"""
        if not results:
            return 0.0
        scores = [r['score'] for r in results]
        return round(sum(scores) / len(scores), 3)
    
    def get_all_keywords(self, results, top_n=10):
        """Extract most common keywords across all results"""
        all_keywords = []
        for result in results:
            all_keywords.extend(result['keywords'])
        
        counter = Counter(all_keywords)
        return [word for word, count in counter.most_common(top_n)]


# Standalone testing
if __name__ == "__main__":
    print("Testing Enhanced Sentiment Analyzer...\n")
    
    analyzer = SentimentAnalyzer()
    
    test_reviews = [
        "The food was absolutely amazing! Best restaurant ever!",
        "Terrible service, won't be coming back.",
        "It was okay, nothing special.",
        "Not bad, but not great either.",
        "I loved everything except the dessert which was disappointing.",
    ]
    
    for review in test_reviews:
        result = analyzer.analyze(review)
        print(f"Review: {review}")
        print(f"→ Sentiment: {result['sentiment']} (Score: {result['score']})")
        print(f"  Keywords: {', '.join(result['keywords'])}")
        print()