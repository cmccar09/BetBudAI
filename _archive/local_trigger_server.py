#!/usr/bin/env python3
"""
Simple local API server to trigger betting workflow on demand
Run this on your laptop: python local_trigger_server.py
"""
from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import os
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

WORKFLOW_SCRIPT = os.path.join(os.path.dirname(__file__), 'scheduled_workflow.ps1')

@app.route('/trigger', methods=['GET', 'POST'])
def trigger_workflow():
    """Trigger the betting workflow in background"""
    try:
        # Run workflow in background thread
        def run_workflow():
            subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', WORKFLOW_SCRIPT],
                cwd=os.path.dirname(__file__),
                capture_output=True
            )
        
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Workflow started',
            'info': 'New picks will be generated in ~60-90 seconds. Refresh to see updates.'
        }), 202
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'running', 'service': 'betting-trigger-server'}), 200

if __name__ == '__main__':
    print("="*60)
    print("Local Betting Workflow Trigger Server")
    print("="*60)
    print(f"Workflow script: {WORKFLOW_SCRIPT}")
    print("\nListening on: http://localhost:5001")
    print("Trigger endpoint: http://localhost:5001/trigger")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
