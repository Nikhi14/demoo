import requests
import json
import re

class QuestionGenerator:
    def __init__(self):
        self.api_base_url = "https://api.anthropic.com/v1/messages"
        # API key is hardcoded here
        self.api_key = "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"
    
    def generate_questions(self, resume_text, jd_text, num_questions=10):
        """Generate interview questions using Claude API - NO api_key parameter needed"""
        try:
            prompt = self._create_question_prompt(resume_text, jd_text, num_questions)
            response = self._call_claude_api(prompt)  # Use self.api_key internally
            questions = self._parse_questions(response)
            return questions
        except Exception as e:
            print(f"Error in generate_questions: {str(e)}")  # Add debugging
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def _create_question_prompt(self, resume_text, jd_text, num_questions):
        """Create the prompt for question generation"""
        return f"""
        Based on the following resume and job description, generate {num_questions} diverse interview questions.
        Create a mix of technical, behavioral, and situational questions that are specific to the candidate's experience and the job requirements.
        
        RESUME:
        {resume_text[:3000]}  # Limit to avoid token limits
        
        JOB DESCRIPTION:
        {jd_text[:2000]}
        
        Please generate questions that cover:
        1. Technical skills and experience
        2. Behavioral scenarios
        3. Situational problem-solving
        4. Role-specific competencies
        5. Cultural fit
        
        Return the response as a JSON array with the following structure:
        [
            {{
                "question": "Question text here",
                "type": "technical|behavioral|situational",
                "difficulty": "easy|medium|hard",
                "category": "relevant category",
                "expected_points": ["point1", "point2", "point3"],
                "time_limit": 180
            }}
        ]
        
        Make sure each question is:
        - Relevant to both the resume and job description
        - Clear and specific
        - Appropriate for the role level
        - Designed to assess key competencies
        """
    
    def _call_claude_api(self, prompt):
        """Make API call to Claude using self.api_key"""
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,  # Use self.api_key
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        print(f"Making API call to: {self.api_base_url}")  # Debug print
        print(f"Using API key: {self.api_key[:20]}...")  # Debug print (partial key)
        
        response = requests.post(self.api_base_url, headers=headers, json=payload)
        
        print(f"API response status: {response.status_code}")  # Debug print
        
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")  # Debug print
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        
        return response.json()['content'][0]['text']
    
    def _parse_questions(self, response):
        """Parse the API response to extract questions"""
        try:
            print(f"Parsing response: {response[:200]}...")  # Debug print
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                questions_data = json.loads(json_match.group(0))
                print(f"Successfully parsed {len(questions_data)} questions")  # Debug print
                return questions_data
            else:
                print("No JSON found, using fallback parsing")  # Debug print
                # Fallback: create questions from text lines
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                questions = []
                
                for i, line in enumerate(lines[:10]):  # Limit to 10 questions
                    # Clean up the line (remove numbering, etc.)
                    question_text = re.sub(r'^\d+\.?\s*', '', line)
                    if len(question_text) > 10:  # Only if it's a substantial question
                        questions.append({
                            "question": question_text,
                            "type": "general",
                            "difficulty": "medium",
                            "category": "general",
                            "expected_points": ["Clear communication", "Relevant experience", "Problem-solving"],
                            "time_limit": 180
                        })
                
                return questions if questions else self._get_fallback_questions()
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")  # Debug print
            return self._get_fallback_questions()
        except Exception as e:
            print(f"Parse error: {str(e)}")  # Debug print
            return self._get_fallback_questions()
    
    def _get_fallback_questions(self):
        """Provide fallback questions if parsing fails"""
        print("Using fallback questions")  # Debug print
        return [
            {
                "question": "Tell me about yourself and your relevant experience for this role.",
                "type": "behavioral",
                "difficulty": "easy",
                "category": "introduction",
                "expected_points": ["Clear introduction", "Relevant experience", "Career goals"],
                "time_limit": 180
            },
            {
                "question": "Describe a challenging project you worked on and how you overcame obstacles.",
                "type": "behavioral",
                "difficulty": "medium",
                "category": "problem-solving",
                "expected_points": ["Problem identification", "Solution approach", "Results achieved"],
                "time_limit": 240
            },
            {
                "question": "How do you stay updated with the latest trends in your field?",
                "type": "behavioral",
                "difficulty": "easy",
                "category": "learning",
                "expected_points": ["Learning methods", "Continuous improvement", "Industry awareness"],
                "time_limit": 120
            }
        ]