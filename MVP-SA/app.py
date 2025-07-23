from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime

# Import your services - UPDATED IMPORT
from services.file_processor import FileProcessor
from services.question_generator import QuestionGenerator
from services.eye_tracker import EyeTracker  # Use no-camera version
from services.answer_rater import AnswerRater
from services.data_manager import DataManager

app = Flask(__name__)
CORS(app)

# Initialize services
file_processor = FileProcessor()
question_generator = QuestionGenerator()
eye_tracker = EyeTracker()  # This won't access camera anymore
answer_rater = AnswerRater()
data_manager = DataManager()

# Global storage for active sessions
active_sessions = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/upload-files', methods=['POST'])
def upload_files():
    """Upload and process resume and job description files"""
    try:
        if 'resume' not in request.files or 'job_description' not in request.files:
            return jsonify({"error": "Both resume and job description files are required"}), 400
        
        resume_file = request.files['resume']
        jd_file = request.files['job_description']
        
        print(f"Processing files: {resume_file.filename}, {jd_file.filename}")
        
        # Process files
        resume_text = file_processor.extract_text_from_pdf(resume_file)
        jd_text = file_processor.extract_text_from_pdf(jd_file)
        
        print(f"Extracted resume text length: {len(resume_text)}")
        print(f"Extracted JD text length: {len(jd_text)}")
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "resume_text": resume_text,
            "jd_text": jd_text,
            "created_at": datetime.now().isoformat(),
            "questions": [],
            "answers": [],
            "tracking_data": [],
            "status": "files_uploaded"
        }
        
        active_sessions[session_id] = session_data
        data_manager.save_session(session_data)
        
        return jsonify({
            "session_id": session_id,
            "resume_length": len(resume_text),
            "jd_length": len(jd_text),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in upload_files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    """Generate interview questions using Claude API"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        print(f"Generating questions for session: {session_id}")
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        session = active_sessions[session_id]
        
        print(f"Resume text length: {len(session['resume_text'])}")
        print(f"JD text length: {len(session['jd_text'])}")
        
        # Generate questions - NO API KEY PARAMETER NEEDED
        questions = question_generator.generate_questions(
            resume_text=session['resume_text'],
            jd_text=session['jd_text']
        )
        
        print(f"Generated {len(questions)} questions")
        
        # Update session
        session['questions'] = questions
        session['status'] = 'questions_generated'
        active_sessions[session_id] = session
        data_manager.save_session(session)
        
        return jsonify({
            "questions": questions,
            "total_questions": len(questions),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in generate_questions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start the interview session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        session = active_sessions[session_id]
        session['status'] = 'interview_active'
        session['interview_started_at'] = datetime.now().isoformat()
        
        # Initialize eye tracking simulation (NO CAMERA ACCESS)
        eye_tracker.start_tracking(session_id)
        
        active_sessions[session_id] = session
        data_manager.save_session(session)
        
        print(f"✅ Interview started for session: {session_id}")
        
        return jsonify({
            "status": "interview_started",
            "first_question": session['questions'][0] if session['questions'] else None
        })
        
    except Exception as e:
        print(f"Error in start_interview: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """Submit and rate an answer"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        question_index = data.get('question_index')
        answer_text = data.get('answer_text')
        
        print(f"Submitting answer for session {session_id}, question {question_index}")
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        session = active_sessions[session_id]
        
        if question_index >= len(session['questions']):
            return jsonify({"error": "Invalid question index"}), 400
        
        question = session['questions'][question_index]
        
        print(f"Rating answer: {answer_text[:100]}...")
        
        # Rate the answer - NO API KEY PARAMETER NEEDED
        rating = answer_rater.rate_answer(
            question=question,
            answer=answer_text
        )
        
        # Get tracking data for this question
        tracking_data = eye_tracker.get_question_tracking_data(session_id, question_index)
        
        # Store answer
        answer_data = {
            "question_index": question_index,
            "question": question['question'],
            "answer": answer_text,
            "rating": rating,
            "tracking_data": tracking_data,
            "timestamp": datetime.now().isoformat()
        }
        
        session['answers'].append(answer_data)
        active_sessions[session_id] = session
        data_manager.save_session(session)
        
        return jsonify({
            "rating": rating,
            "tracking_summary": eye_tracker.get_tracking_summary(tracking_data),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in submit_answer: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/end-interview', methods=['POST'])
def end_interview():
    """End the interview and generate final results"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        session = active_sessions[session_id]
        session['status'] = 'interview_completed'
        session['interview_ended_at'] = datetime.now().isoformat()
        
        # Stop eye tracking simulation
        eye_tracker.stop_tracking(session_id)
        
        # Generate final results
        results = data_manager.generate_final_results(session)
        session['final_results'] = results
        
        active_sessions[session_id] = session
        data_manager.save_session(session)
        
        print(f"✅ Interview ended for session: {session_id}")
        
        return jsonify({
            "results": results,
            "status": "interview_completed"
        })
        
    except Exception as e:
        print(f"Error in end_interview: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-tracking-data/<session_id>', methods=['GET'])
def get_tracking_data(session_id):
    """Get real-time tracking data"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        tracking_data = eye_tracker.get_current_tracking_data(session_id)
        
        return jsonify({
            "tracking_data": tracking_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export-results/<session_id>', methods=['GET'])
def export_results(session_id):
    """Export interview results as JSON file"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
        
        session = active_sessions[session_id]
        file_path = data_manager.export_results(session)
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure data directories exist
    os.makedirs('interview_data', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    print("🚀 Starting AI Interview System Backend")
    print("🔑 API key is hardcoded in services") 
    print("👁️ Using simulated eye tracking (no camera access from backend)")
    print("📹 Frontend will handle camera access directly")
    
    app.run(debug=True, host='0.0.0.0', port=5000)