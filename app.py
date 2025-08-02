from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Izinkan akses dari semua domain. Untuk produksi, batasi domain.
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, room TEXT, username TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Endpoint untuk halaman utama (jika diakses langsung)
@app.route('/')
def home():
    return render_template('index.html')

# Endpoint untuk mendapatkan history chat
@app.route('/history')
def get_history():
    room = request.args.get('room')
    if not room:
        return jsonify([])
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages WHERE room = ? ORDER BY timestamp ASC", (room,))
    rows = c.fetchall()
    conn.close()
    
    history = [{'username': row[0], 'message': row[1], 'timestamp': row[2]} for row in rows]
    return jsonify(history)

# Event ketika user join room
@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    join_room(room)
    emit('message', {'username': 'System', 'message': f'{username} bergabung ke room'}, room=room)

# Event ketika user kirim pesan
@socketio.on('send_message')
def on_send_message(data):
    room = data['room']
    username = data['username']
    message = data['message']
    
    # Simpan ke database
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (room, username, message) VALUES (?,?,?)", 
              (room, username, message))
    conn.commit()
    conn.close()
    
    # Broadcast ke semua di room
    emit('message', {'username': username, 'message': message}, room=room)

# Event ketika user keluar (opsional)
@socketio.on('leave')
def on_leave(data):
    room = data['room']
    username = data['username']
    leave_room(room)
    emit('message', {'username': 'System', 'message': f'{username} keluar'}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)