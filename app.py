from typing import List, Dict, Any, Optional, Union
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os
import urllib.parse

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # This properly enables CORS for all routes

# Database configuration
def get_db_connection():
    """Get a connection to the PostgreSQL database, using DATABASE_URL from environment or default local settings"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Handle potential "postgres://" style URLs from Render
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Connect using the URL
        conn = psycopg2.connect(database_url)
    else:
        # Local development fallback
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'dnd_quests'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            port=os.environ.get('DB_PORT', '5432')
        )
    
    conn.autocommit = True
    return conn

def init_db():
    """Initialize the database by creating the quests table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create quests table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quests (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        quest_type TEXT NOT NULL,
        description TEXT NOT NULL,
        reward TEXT NOT NULL,
        creator TEXT NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.close()
    conn.close()

# Initialize the database
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Error initializing database: {e}")

# Helper function to convert quest row to dict
def quest_to_dict(quest) -> Dict[str, Any]:
    return {
        'id': quest['id'],
        'title': quest['title'],
        'quest_type': quest['quest_type'],
        'description': quest['description'],
        'reward': quest['reward'],
        'creator': quest['creator'],
        'completed': quest['completed'],
        'created_at': quest['created_at'].isoformat() if quest['created_at'] else None
    }

# API Routes
@app.route('/api/quests', methods=['GET'])
def get_quests() -> Any:
    """Get all quests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM quests ORDER BY created_at DESC')
        quests = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([quest_to_dict(quest) for quest in quests])
    except Exception as e:
        print(f"Error fetching quests: {e}")
        return jsonify({"error": "Failed to fetch quests"}), 500

@app.route('/api/quests', methods=['POST'])
def create_quest() -> Any:
    """Create a new quest"""
    data = request.json
    
    # Validate required fields
    required_fields = ['title', 'quest_type', 'description', 'reward', 'creator']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
        INSERT INTO quests (title, quest_type, description, reward, creator)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        ''', (data['title'], data['quest_type'], data['description'], data['reward'], data['creator']))
        
        new_quest = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify(quest_to_dict(new_quest)), 201
    except Exception as e:
        print(f"Error creating quest: {e}")
        return jsonify({"error": "Failed to create quest"}), 500

@app.route('/api/quests/<int:quest_id>', methods=['PUT'])
def update_quest(quest_id: int) -> Any:
    """Update a quest (e.g., mark as completed)"""
    data = request.json
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if quest exists
        cursor.execute('SELECT * FROM quests WHERE id = %s', (quest_id,))
        quest = cursor.fetchone()
        
        if not quest:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Quest not found'}), 404
        
        # Update fields
        update_fields = []
        update_values = []
        
        if 'completed' in data:
            update_fields.append('completed = %s')
            update_values.append(data['completed'])
        
        if 'title' in data:
            update_fields.append('title = %s')
            update_values.append(data['title'])
            
        if 'quest_type' in data:
            update_fields.append('quest_type = %s')
            update_values.append(data['quest_type'])
            
        if 'description' in data:
            update_fields.append('description = %s')
            update_values.append(data['description'])
            
        if 'reward' in data:
            update_fields.append('reward = %s')
            update_values.append(data['reward'])
            
        if 'creator' in data:
            update_fields.append('creator = %s')
            update_values.append(data['creator'])
        
        if update_fields:
            cursor.execute(
                f'UPDATE quests SET {", ".join(update_fields)} WHERE id = %s RETURNING *',
                update_values + [quest_id]
            )
            updated_quest = cursor.fetchone()
        else:
            updated_quest = quest
        
        cursor.close()
        conn.close()
        
        return jsonify(quest_to_dict(updated_quest))
    except Exception as e:
        print(f"Error updating quest: {e}")
        return jsonify({"error": "Failed to update quest"}), 500

@app.route('/api/quests/<int:quest_id>', methods=['DELETE'])
def delete_quest(quest_id: int) -> Any:
    """Delete a quest"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if quest exists
        cursor.execute('SELECT * FROM quests WHERE id = %s', (quest_id,))
        quest = cursor.fetchone()
        
        if not quest:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Quest not found'}), 404
        
        cursor.execute('DELETE FROM quests WHERE id = %s', (quest_id,))
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Quest deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting quest: {e}")
        return jsonify({"error": "Failed to delete quest"}), 500

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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=bool(os.environ.get('DEBUG', True)), host='0.0.0.0', port=port)
