from typing import List, Dict, Any, Optional, Union
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import json
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Database setup
DB_PATH = 'quests.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create quests table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        quest_type TEXT NOT NULL,
        description TEXT NOT NULL,
        reward TEXT NOT NULL,
        creator TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Helper function to convert quest row to dict
def quest_to_dict(quest) -> Dict[str, Any]:
    return {
        'id': quest['id'],
        'title': quest['title'],
        'quest_type': quest['quest_type'],
        'description': quest['description'],
        'reward': quest['reward'],
        'creator': quest['creator'],
        'completed': bool(quest['completed']),
        'created_at': quest['created_at']
    }

# API Routes
@app.route('/api/quests', methods=['GET'])
def get_quests() -> Any:
    """Get all quests"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quests ORDER BY created_at DESC')
    quests = [quest_to_dict(quest) for quest in cursor.fetchall()]
    conn.close()
    
    return jsonify(quests)

@app.route('/api/quests', methods=['POST'])
def create_quest() -> Any:
    """Create a new quest"""
    data = request.json
    
    # Validate required fields
    required_fields = ['title', 'quest_type', 'description', 'reward', 'creator']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO quests (title, quest_type, description, reward, creator)
    VALUES (?, ?, ?, ?, ?)
    ''', (data['title'], data['quest_type'], data['description'], data['reward'], data['creator']))
    
    quest_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the newly created quest
    cursor.execute('SELECT * FROM quests WHERE id = ?', (quest_id,))
    new_quest = cursor.fetchone()
    
    conn.close()
    
    return jsonify(quest_to_dict(new_quest)), 201

@app.route('/api/quests/<int:quest_id>', methods=['PUT'])
def update_quest(quest_id: int) -> Any:
    """Update a quest (e.g., mark as completed)"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if quest exists
    cursor.execute('SELECT * FROM quests WHERE id = ?', (quest_id,))
    quest = cursor.fetchone()
    
    if not quest:
        conn.close()
        return jsonify({'error': 'Quest not found'}), 404
    
    # Update fields
    update_fields = []
    update_values = []
    
    if 'completed' in data:
        update_fields.append('completed = ?')
        update_values.append(1 if data['completed'] else 0)
    
    if 'title' in data:
        update_fields.append('title = ?')
        update_values.append(data['title'])
        
    if 'quest_type' in data:
        update_fields.append('quest_type = ?')
        update_values.append(data['quest_type'])
        
    if 'description' in data:
        update_fields.append('description = ?')
        update_values.append(data['description'])
        
    if 'reward' in data:
        update_fields.append('reward = ?')
        update_values.append(data['reward'])
        
    if 'creator' in data:
        update_fields.append('creator = ?')
        update_values.append(data['creator'])
    
    if update_fields:
        cursor.execute(
            f'UPDATE quests SET {", ".join(update_fields)} WHERE id = ?',
            update_values + [quest_id]
        )
        conn.commit()
    
    # Fetch updated quest
    cursor.execute('SELECT * FROM quests WHERE id = ?', (quest_id,))
    updated_quest = cursor.fetchone()
    
    conn.close()
    
    return jsonify(quest_to_dict(updated_quest))

@app.route('/api/quests/<int:quest_id>', methods=['DELETE'])
def delete_quest(quest_id: int) -> Any:
    """Delete a quest"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if quest exists
    cursor.execute('SELECT * FROM quests WHERE id = ?', (quest_id,))
    quest = cursor.fetchone()
    
    if not quest:
        conn.close()
        return jsonify({'error': 'Quest not found'}), 404
    
    cursor.execute('DELETE FROM quests WHERE id = ?', (quest_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Quest deleted successfully'}), 200

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Serve frontend files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path: str) -> Any:
    """Serve static files"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
