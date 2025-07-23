import requests
import json
import re
from textstat import flesch_reading_ease, flesch_kincaid_grade
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

class AnswerRater:
    def __init__(self):
        self.api_base_url = "https://api.anthropic.com/v1/messages"
        # API key is hardcoded here
        self.api_key = "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"
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except:
            self.sentiment_analyzer = None
    
    def rate_answer(self, question, answer):
        """Rate an answer using multiple criteria"""
        try:
            print(f"Rating answer: {answer[:50]}...")
            
            ai_rating = self._get_ai_rating(question, answer)
            

            linguistic_metrics = self._calculate_linguistic_metrics(answer)
            sentiment_metrics = self._calculate_sentiment_metrics(answer)
            
            final_rating = self._combine_ratings(ai_rating, linguistic_metrics, sentiment_metrics)
            
            print(f"Final rating: {final_rating.get('final_score', 'N/A')}/10")
            
            return final_rating
            
        except Exception as e:
            print(f"Error in rate_answer: {str(e)}")
            # Fallback rating
            return self._get_fallback_rating(question, answer)
    
    def _get_ai_rating(self, question, answer):
        """Get rating from Claude API using self.api_key"""
        prompt = f"""
        Rate this interview answer comprehensively on a scale of 1-10 considering multiple criteria:
        
        QUESTION: {question['question']}
        QUESTION TYPE: {question.get('type', 'general')}
        EXPECTED POINTS: {', '.join(question.get('expected_points', []))}
        
        CANDIDATE ANSWER: {answer}
        
        Please evaluate based on:
        1. RELEVANCE (1-10): How well does the answer address the question?
        2. TECHNICAL ACCURACY (1-10): Correctness of technical information (if applicable)
        3. CLARITY (1-10): How clear and well-structured is the communication?
        4. COMPLETENESS (1-10): Does the answer cover all important aspects?
        5. EXAMPLES (1-10): Quality and relevance of examples provided
        6. DEPTH (1-10): Level of insight and understanding demonstrated
        
        Also provide:
        - Overall score (1-10)
        - Top 3 strengths
        - Top 3 areas for improvement
        - Specific feedback for the candidate
        
        Return as JSON:
        {{
            "overall_score": X,
            "detailed_scores": {{
                "relevance": X,
                "technical_accuracy": X,
                "clarity": X,
                "completeness": X,
                "examples": X,
                "depth": X
            }},
            "strengths": ["strength1", "strength2", "strength3"],
            "improvements": ["improvement1", "improvement2", "improvement3"],
            "feedback": "Detailed feedback paragraph",
            "confidence": X
        }}
        """
        
        try:
            response = self._call_claude_api(prompt)
            return self._parse_ai_rating(response)
        except Exception as e:
            print(f"AI rating API call failed: {str(e)}")
            raise Exception(f"AI rating failed: {str(e)}")
    
    def _call_claude_api(self, prompt):
        """Make API call to Claude using self.api_key"""
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 2000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        print(f"Making API call for rating...")
        print(f"Using API key: {self.api_key[:20]}...")
        
        response = requests.post(self.api_base_url, headers=headers, json=payload)
        
        print(f"Rating API response status: {response.status_code}")  # Debug
        
        if response.status_code != 200:
            print(f"Rating API Error: {response.text}")  # Debug
            raise Exception(f"API request failed with status {response.status_code}")
        
        return response.json()['content'][0]['text']
    
    def _parse_ai_rating(self, response):
        """Parse AI rating response"""
        try:
            print(f"Parsing rating response: {response[:100]}...")  # Debug
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                rating = json.loads(json_match.group(0))
                print(f"Successfully parsed rating: {rating.get('overall_score', 'N/A')}/10")  # Debug
                return rating
            else:
                print("No JSON found in rating response, using fallback parsing")  # Debug
                # Extract scores manually if JSON parsing fails
                scores = re.findall(r'(\d+(?:\.\d+)?)', response)
                if scores:
                    overall_score = float(scores[0])
                    return {
                        "overall_score": min(10, max(1, overall_score)),
                        "detailed_scores": {
                            "relevance": min(10, max(1, float(scores[1]) if len(scores) > 1 else overall_score)),
                            "technical_accuracy": min(10, max(1, float(scores[2]) if len(scores) > 2 else overall_score)),
                            "clarity": min(10, max(1, float(scores[3]) if len(scores) > 3 else overall_score)),
                            "completeness": min(10, max(1, float(scores[4]) if len(scores) > 4 else overall_score)),
                            "examples": min(10, max(1, float(scores[5]) if len(scores) > 5 else overall_score)),
                            "depth": min(10, max(1, float(scores[6]) if len(scores) > 6 else overall_score))
                        },
                        "strengths": ["Clear communication", "Relevant content", "Good structure"],
                        "improvements": ["Add more examples", "Provide more detail", "Better organization"],
                        "feedback": "The answer addresses the question with reasonable clarity.",
                        "confidence": 0.7
                    }
                else:
                    raise Exception("No scores found in response")
        except json.JSONDecodeError as e:
            print(f"JSON decode error in rating: {str(e)}")  # Debug
            raise Exception(f"Failed to parse AI rating: {str(e)}")
        except Exception as e:
            print(f"Parse error in rating: {str(e)}")  # Debug
            raise Exception(f"Failed to parse AI rating: {str(e)}")
    
    def _calculate_linguistic_metrics(self, answer):
        """Calculate linguistic quality metrics"""
        if not answer or len(answer.strip()) == 0:
            return {
                "word_count": 0,
                "readability_score": 0,
                "grade_level": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0
            }
        
        word_count = len(answer.split())
        sentences = answer.split('.')
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        try:
            readability = flesch_reading_ease(answer)
            grade_level = flesch_kincaid_grade(answer)
        except:
            readability = 50  # Average readability
            grade_level = 10   # High school level
        
        return {
            "word_count": word_count,
            "readability_score": readability,
            "grade_level": grade_level,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1)
        }
    
    def _calculate_sentiment_metrics(self, answer):
        """Calculate sentiment and confidence metrics"""
        if not self.sentiment_analyzer or not answer:
            return {
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }
        
        try:
            scores = self.sentiment_analyzer.polarity_scores(answer)
            
            # Determine dominant sentiment
            if scores['compound'] >= 0.05:
                sentiment = "positive"
            elif scores['compound'] <= -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Calculate confidence based on sentence structure and word choice
            confidence_indicators = [
                "confident", "certain", "sure", "definitely", "absolutely",
                "clearly", "obviously", "undoubtedly", "experience shows",
                "I know", "I'm experienced", "I've successfully"
            ]
            
            uncertainty_indicators = [
                "maybe", "perhaps", "possibly", "might", "could be",
                "I think", "I guess", "not sure", "uncertain", "probably"
            ]
            
            answer_lower = answer.lower()
            confidence_count = sum(1 for phrase in confidence_indicators if phrase in answer_lower)
            uncertainty_count = sum(1 for phrase in uncertainty_indicators if phrase in answer_lower)
            
            # Base confidence on sentiment compound score and linguistic indicators
            base_confidence = abs(scores['compound'])
            confidence_adjustment = (confidence_count - uncertainty_count) * 0.1
            final_confidence = max(0, min(1, base_confidence + confidence_adjustment))
            
            return {
                "sentiment": sentiment,
                "confidence_score": round(final_confidence, 2),
                "positive_score": round(scores['pos'], 2),
                "negative_score": round(scores['neg'], 2),
                "neutral_score": round(scores['neu'], 2)
            }
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }
    
    def _combine_ratings(self, ai_rating, linguistic_metrics, sentiment_metrics):
        """Combine all ratings into final score"""
        # Base score from AI
        base_score = ai_rating['overall_score']
        
        # Adjustments based on linguistic metrics
        word_count = linguistic_metrics['word_count']
        readability = linguistic_metrics['readability_score']
        
        # Word count adjustment (optimal range: 50-200 words)
        if word_count < 20:
            word_count_adjustment = -1.0  # Too short
        elif word_count < 50:
            word_count_adjustment = -0.5
        elif 50 <= word_count <= 200:
            word_count_adjustment = 0.0   # Optimal
        elif word_count <= 300:
            word_count_adjustment = -0.2
        else:
            word_count_adjustment = -0.5  # Too long
        
        # Readability adjustment (target: 30-70 range)
        if 30 <= readability <= 70:
            readability_adjustment = 0.2
        else:
            readability_adjustment = 0.0
        
        # Confidence adjustment
        confidence_adjustment = (sentiment_metrics['confidence_score'] - 0.5) * 0.5
        
        # Calculate final score
        final_score = base_score + word_count_adjustment + readability_adjustment + confidence_adjustment
        final_score = max(1, min(10, final_score))
        
        # Add linguistic and sentiment data to the rating
        ai_rating['final_score'] = round(final_score, 1)
        ai_rating['linguistic_metrics'] = linguistic_metrics
        ai_rating['sentiment_metrics'] = sentiment_metrics
        ai_rating['adjustments'] = {
            'word_count': word_count_adjustment,
            'readability': readability_adjustment,
            'confidence': confidence_adjustment
        }
        
        return ai_rating
    
    def _get_fallback_rating(self, question, answer):
        """Provide fallback rating when AI rating fails"""
        print("Using fallback rating")  # Debug
        
        word_count = len(answer.split()) if answer else 0
        
        # Simple scoring based on answer length and basic criteria
        if word_count == 0:
            score = 1
        elif word_count < 20:
            score = 3
        elif word_count < 50:
            score = 5
        elif word_count <= 150:
            score = 7
        else:
            score = 6
        
        return {
            "overall_score": score,
            "final_score": score,
            "detailed_scores": {
                "relevance": score,
                "technical_accuracy": score,
                "clarity": score,
                "completeness": score,
                "examples": score,
                "depth": score
            },
            "strengths": ["Answer provided", "Appropriate length"],
            "improvements": ["Could add more detail", "Include specific examples"],
            "feedback": f"Answer provided with {word_count} words. Consider expanding with more specific details and examples.",
            "confidence": 0.5,
            "linguistic_metrics": self._calculate_linguistic_metrics(answer),
            "sentiment_metrics": self._calculate_sentiment_metrics(answer),
            "adjustments": {"word_count": 0, "readability": 0, "confidence": 0}
        }