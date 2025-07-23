import os
import json
from datetime import datetime
import shutil

class DataManager:
    def __init__(self):
        self.base_dir = "interview_data"
        self.exports_dir = "exports"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ['sessions', 'tracking_data', 'audio_recordings', 'results']
        for subdir in subdirs:
            os.makedirs(os.path.join(self.base_dir, subdir), exist_ok=True)
    
    def save_session(self, session_data):
        """Save session data to file"""
        session_id = session_data['session_id']
        filename = f"{session_id}.json"
        filepath = os.path.join(self.base_dir, 'sessions', filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception as e:
            raise Exception(f"Failed to save session: {str(e)}")
    
    def load_session(self, session_id):
        """Load session data from file"""
        filename = f"{session_id}.json"
        filepath = os.path.join(self.base_dir, 'sessions', filename)
        
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            raise Exception(f"Failed to load session: {str(e)}")
    
    def save_tracking_data(self, session_id, tracking_data):
        """Save tracking data separately for large datasets"""
        filename = f"{session_id}_tracking.json"
        filepath = os.path.join(self.base_dir, 'tracking_data', filename)
        
        try:
            # Append to existing file or create new
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
            
            existing_data.extend(tracking_data)
            
            with open(filepath, 'w') as f:
                json.dump(existing_data, f, default=str)
        except Exception as e:
            raise Exception(f"Failed to save tracking data: {str(e)}")
    
    def save_audio_recording(self, session_id, question_index, audio_data):
        """Save audio recording"""
        filename = f"{session_id}_q{question_index}.wav"
        filepath = os.path.join(self.base_dir, 'audio_recordings', filename)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to save audio: {str(e)}")
    
    def generate_final_results(self, session_data):
        """Generate comprehensive final results"""
        answers = session_data.get('answers', [])
        
        if not answers:
            return {
                "overall_score": 0,
                "total_questions": 0,
                "questions_answered": 0,
                "performance_summary": "No answers provided"
            }
        
        # Calculate overall metrics
        total_questions = len(session_data.get('questions', []))
        questions_answered = len(answers)
        
        # Calculate scores
        scores = [answer['rating']['final_score'] for answer in answers if 'rating' in answer]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate detailed metrics
        detailed_scores = {
            'relevance': [],
            'technical_accuracy': [],
            'clarity': [],
            'completeness': [],
            'examples': [],
            'depth': []
        }
        
        for answer in answers:
            if 'rating' in answer and 'detailed_scores' in answer['rating']:
                for metric, score in answer['rating']['detailed_scores'].items():
                    if metric in detailed_scores:
                        detailed_scores[metric].append(score)
        
        # Average detailed scores
        avg_detailed_scores = {}
        for metric, scores in detailed_scores.items():
            avg_detailed_scores[metric] = sum(scores) / len(scores) if scores else 0
        
        # Analyze tracking data
        tracking_summary = self._analyze_tracking_data(answers)
        
        # Performance categorization
        performance_category = self._categorize_performance(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, avg_detailed_scores, tracking_summary
        )
        
        # Calculate interview duration
        start_time = session_data.get('interview_started_at')
        end_time = session_data.get('interview_ended_at')
        duration_minutes = 0
        
        if start_time and end_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
        
        results = {
            "overall_score": round(overall_score, 1),
            "performance_category": performance_category,
            "total_questions": total_questions,
            "questions_answered": questions_answered,
            "completion_rate": round((questions_answered / total_questions) * 100, 1) if total_questions > 0 else 0,
            "interview_duration_minutes": round(duration_minutes, 1),
            "detailed_scores": {k: round(v, 1) for k, v in avg_detailed_scores.items()},
            "tracking_summary": tracking_summary,
            "question_analysis": self._analyze_questions_by_type(answers),
            "strengths": self._extract_common_strengths(answers),
            "areas_for_improvement": self._extract_common_improvements(answers),
            "recommendations": recommendations,
            "score_distribution": self._calculate_score_distribution(scores),
            "session_metadata": {
                "session_id": session_data['session_id'],
                "created_at": session_data['created_at'],
                "completed_at": session_data.get('interview_ended_at')
            }
        }
        
        # Save detailed results
        self._save_detailed_results(session_data['session_id'], results)
        
        return results
    
    def _analyze_tracking_data(self, answers):
        """Analyze tracking data across all answers"""
        all_tracking_data = []
        for answer in answers:
            if 'tracking_data' in answer:
                all_tracking_data.extend(answer['tracking_data'])
        
        if not all_tracking_data:
            return {
                "avg_eye_contact": 0,
                "avg_face_visibility": 0,
                "total_blinks": 0,
                "head_movement_stability": "unknown"
            }
        
        # Calculate averages
        eye_contact_scores = [d.get('eye_contact_score', 0) for d in all_tracking_data]
        face_visibility_scores = [d.get('face_visibility', 0) for d in all_tracking_data]
        blinks = [d.get('blink_detected', False) for d in all_tracking_data]
        
        return {
            "avg_eye_contact": round(sum(eye_contact_scores) / len(eye_contact_scores), 1),
            "avg_face_visibility": round(sum(face_visibility_scores) / len(face_visibility_scores), 1),
            "total_blinks": sum(blinks),
            "blink_rate_per_minute": round(sum(blinks) / (len(all_tracking_data) / 600), 1),  # Assuming 10 FPS
            "head_movement_stability": self._analyze_head_movement(all_tracking_data)
        }
    
    def _analyze_head_movement(self, tracking_data):
        """Analyze head movement stability"""
        head_poses = [d.get('head_pose', {}) for d in tracking_data if 'head_pose' in d]
        if not head_poses:
            return "unknown"
        
        yaw_values = [p.get('yaw', 0) for p in head_poses]
        pitch_values = [p.get('pitch', 0) for p in head_poses]
        
        import numpy as np
        yaw_std = np.std(yaw_values)
        pitch_std = np.std(pitch_values)
        
        avg_movement = (yaw_std + pitch_std) / 2
        
        if avg_movement < 5:
            return "very_stable"
        elif avg_movement < 10:
            return "stable"
        elif avg_movement < 20:
            return "moderate"
        else:
            return "excessive"
    
    def _categorize_performance(self, overall_score):
        """Categorize performance based on overall score"""
        if overall_score >= 9:
            return "excellent"
        elif overall_score >= 8:
            return "very_good"
        elif overall_score >= 7:
            return "good"
        elif overall_score >= 6:
            return "satisfactory"
        elif overall_score >= 5:
            return "needs_improvement"
        else:
            return "poor"
    
    def _generate_recommendations(self, overall_score, detailed_scores, tracking_summary):
        """Generate personalized recommendations"""
        recommendations = []
        
        # Score-based recommendations
        if overall_score < 6:
            recommendations.append("Consider additional preparation focusing on core competencies")
        
        # Detailed score recommendations
        for metric, score in detailed_scores.items():
            if score < 6:
                if metric == 'relevance':
                    recommendations.append("Practice answering questions more directly and staying on topic")
                elif metric == 'technical_accuracy':
                    recommendations.append("Review technical concepts and ensure accuracy in responses")
                elif metric == 'clarity':
                    recommendations.append("Work on structuring answers more clearly and concisely")
                elif metric == 'completeness':
                    recommendations.append("Provide more comprehensive answers covering all aspects")
                elif metric == 'examples':
                    recommendations.append("Include more specific, relevant examples in responses")
                elif metric == 'depth':
                    recommendations.append("Demonstrate deeper understanding and insight")
        
        # Tracking-based recommendations
        if tracking_summary['avg_eye_contact'] < 60:
            recommendations.append("Practice maintaining better eye contact with the camera")
        
        if tracking_summary['avg_face_visibility'] < 80:
            recommendations.append("Ensure proper lighting and camera positioning for better visibility")
        
        if tracking_summary['head_movement_stability'] in ['moderate', 'excessive']:
            recommendations.append("Try to minimize excessive head movements during responses")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Continue practicing to maintain your strong performance")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _analyze_questions_by_type(self, answers):
        """Analyze performance by question type"""
        type_performance = {}
        
        for answer in answers:
            question_type = answer.get('question_type', 'general')
            score = answer.get('rating', {}).get('final_score', 0)
            
            if question_type not in type_performance:
                type_performance[question_type] = []
            type_performance[question_type].append(score)
        
        # Calculate averages by type
        type_averages = {}
        for qtype, scores in type_performance.items():
            type_averages[qtype] = {
                'average_score': round(sum(scores) / len(scores), 1),
                'question_count': len(scores),
                'performance_level': self._categorize_performance(sum(scores) / len(scores))
            }
        
        return type_averages
    
    def _extract_common_strengths(self, answers):
        """Extract most common strengths across all answers"""
        all_strengths = []
        for answer in answers:
            strengths = answer.get('rating', {}).get('strengths', [])
            all_strengths.extend(strengths)
        
        # Count frequency
        strength_counts = {}
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        # Return top 3 most common strengths
        sorted_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)
        return [strength for strength, count in sorted_strengths[:3]]
    
    def _extract_common_improvements(self, answers):
        """Extract most common improvement areas across all answers"""
        all_improvements = []
        for answer in answers:
            improvements = answer.get('rating', {}).get('improvements', [])
            all_improvements.extend(improvements)
        
        # Count frequency
        improvement_counts = {}
        for improvement in all_improvements:
            improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        # Return top 3 most common improvements
        sorted_improvements = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)
        return [improvement for improvement, count in sorted_improvements[:3]]
    
    def _calculate_score_distribution(self, scores):
        """Calculate score distribution"""
        if not scores:
            return {}
        
        ranges = {
            '9-10': 0, '8-9': 0, '7-8': 0, '6-7': 0, '5-6': 0, '0-5': 0
        }
        
        for score in scores:
            if score >= 9:
                ranges['9-10'] += 1
            elif score >= 8:
                ranges['8-9'] += 1
            elif score >= 7:
                ranges['7-8'] += 1
            elif score >= 6:
                ranges['6-7'] += 1
            elif score >= 5:
                ranges['5-6'] += 1
            else:
                ranges['0-5'] += 1
        
        # Convert to percentages
        total = len(scores)
        return {range_name: round((count / total) * 100, 1) 
                for range_name, count in ranges.items()}
    
    def _save_detailed_results(self, session_id, results):
        """Save detailed results to file"""
        filename = f"{session_id}_results.json"
        filepath = os.path.join(self.base_dir, 'results', filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save detailed results: {str(e)}")
    
    def export_results(self, session_data):
        """Export results to a downloadable file"""
        session_id = session_data['session_id']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_results_{session_id}_{timestamp}.json"
        filepath = os.path.join(self.exports_dir, filename)
        
        # Create comprehensive export data
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "session_id": session_id,
                "export_version": "1.0"
            },
            "session_data": session_data,
            "summary": session_data.get('final_results', {}),
            "detailed_answers": []
        }
        
        # Add detailed answer analysis
        for i, answer in enumerate(session_data.get('answers', [])):
            detailed_answer = {
                "question_number": i + 1,
                "question": answer.get('question', ''),
                "answer": answer.get('answer', ''),
                "rating": answer.get('rating', {}),
                "tracking_summary": answer.get('tracking_data', []),
                "timestamp": answer.get('timestamp', '')
            }
            export_data["detailed_answers"].append(detailed_answer)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to export results: {str(e)}")