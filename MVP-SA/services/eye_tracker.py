# services/eye_tracker_no_camera.py - Modified Eye Tracker (No Camera Access)
import threading
import time
from collections import deque
import math
import random

class EyeTracker:
    """Eye tracker that simulates data without accessing camera directly"""
    
    def __init__(self):
        # Active tracking sessions
        self.tracking_sessions = {}
        self.tracking_threads = {}
        
    def start_tracking(self, session_id):
        """Start eye tracking simulation for a session"""
        if session_id in self.tracking_sessions:
            return  # Already tracking
        
        print(f"🎯 Starting tracking simulation for session: {session_id}")
        
        self.tracking_sessions[session_id] = {
            'active': True,
            'data': deque(maxlen=1000),  # Keep last 1000 data points
            'current_question': 0,
            'question_data': {}
        }
        
        # Start tracking simulation thread
        thread = threading.Thread(target=self._tracking_simulation_loop, args=(session_id,))
        thread.daemon = True
        thread.start()
        self.tracking_threads[session_id] = thread
    
    def stop_tracking(self, session_id):
        """Stop eye tracking for a session"""
        if session_id in self.tracking_sessions:
            self.tracking_sessions[session_id]['active'] = False
            del self.tracking_sessions[session_id]
            print(f"🛑 Stopped tracking for session: {session_id}")
        
        if session_id in self.tracking_threads:
            del self.tracking_threads[session_id]
    
    def _tracking_simulation_loop(self, session_id):
        """Simulate tracking data without camera access"""
        base_eye_contact = 75  # Base eye contact percentage
        base_face_visibility = 85  # Base face visibility
        
        while session_id in self.tracking_sessions and self.tracking_sessions[session_id]['active']:
            # Generate realistic tracking data
            tracking_data = self._generate_simulated_metrics(base_eye_contact, base_face_visibility)
            tracking_data['timestamp'] = time.time()
            
            # Store data
            self.tracking_sessions[session_id]['data'].append(tracking_data)
            
            # Slightly vary the base values for realism
            base_eye_contact += random.uniform(-2, 2)
            base_eye_contact = max(60, min(95, base_eye_contact))  # Keep in realistic range
            
            base_face_visibility += random.uniform(-1, 1)
            base_face_visibility = max(75, min(100, base_face_visibility))
            
            time.sleep(1)  # Update every second
    
    def _generate_simulated_metrics(self, base_eye_contact, base_face_visibility):
        """Generate realistic simulated tracking metrics"""
        
        # Add some randomness to make it look realistic
        eye_contact_variation = random.uniform(-15, 15)
        face_visibility_variation = random.uniform(-10, 10)
        
        eye_contact_score = max(0, min(100, base_eye_contact + eye_contact_variation))
        face_visibility = max(0, min(100, base_face_visibility + face_visibility_variation))
        
        # Simulate head pose
        yaw = random.uniform(-20, 20)  # Left-right head rotation
        pitch = random.uniform(-10, 10)  # Up-down head rotation
        
        # Simulate blinks (occasional)
        blink_detected = random.random() < 0.1  # 10% chance of blink detection
        
        return {
            'eye_contact_score': round(eye_contact_score, 1),
            'face_visibility': round(face_visibility, 1),
            'head_pose': {
                'yaw': round(yaw, 1),
                'pitch': round(pitch, 1),
                'roll': 0.0
            },
            'blink_detected': blink_detected,
            'gaze_direction': {
                'x': yaw / 30.0,  # Normalize to -1 to 1 range
                'y': pitch / 30.0
            }
        }
    
    def get_current_tracking_data(self, session_id):
        """Get current tracking data for a session"""
        if session_id not in self.tracking_sessions:
            return None
        
        data = list(self.tracking_sessions[session_id]['data'])
        if not data:
            return None
        
        # Return the last 10 data points
        return data[-10:]
    
    def get_question_tracking_data(self, session_id, question_index):
        """Get tracking data for a specific question"""
        if session_id not in self.tracking_sessions:
            return []
        
        # Mark the start of a new question
        current_time = time.time()
        self.tracking_sessions[session_id]['question_data'][question_index] = {
            'start_time': current_time,
            'data': []
        }
        
        # Get data from the last 2 minutes (typical question duration)
        all_data = list(self.tracking_sessions[session_id]['data'])
        question_data = [d for d in all_data if current_time - d.get('timestamp', 0) <= 120]
        
        return question_data
    
    def get_tracking_summary(self, tracking_data):
        """Generate summary statistics from tracking data"""
        if not tracking_data:
            return {
                'avg_eye_contact': 0,
                'avg_face_visibility': 0,
                'blink_rate': 0,
                'head_movement': 'stable'
            }
        
        # Calculate averages
        avg_eye_contact = sum(d.get('eye_contact_score', 0) for d in tracking_data) / len(tracking_data)
        avg_face_visibility = sum(d.get('face_visibility', 0) for d in tracking_data) / len(tracking_data)
        
        # Calculate blink rate (blinks per minute)
        blinks = sum(1 for d in tracking_data if d.get('blink_detected', False))
        duration_minutes = len(tracking_data) / 60  # 1 second intervals
        blink_rate = blinks / max(duration_minutes, 1)
        
        # Analyze head movement
        head_poses = [d.get('head_pose', {}) for d in tracking_data]
        yaw_values = [p.get('yaw', 0) for p in head_poses if p]
        
        if yaw_values:
            import numpy as np
            yaw_variance = np.var(yaw_values)
            
            if yaw_variance < 25:
                head_movement = 'stable'
            elif yaw_variance < 100:
                head_movement = 'moderate'
            else:
                head_movement = 'excessive'
        else:
            head_movement = 'stable'
        
        return {
            'avg_eye_contact': round(avg_eye_contact, 1),
            'avg_face_visibility': round(avg_face_visibility, 1),
            'blink_rate': round(blink_rate, 1),
            'head_movement': head_movement
        }
