from flask import Blueprint, render_template, request, redirect, url_for
from dbconnect import Connecttodb
from sqlalchemy import text

chat_bp = Blueprint('chat_bp', __name__, template_folder='templates', static_folder='static')

conn = Connecttodb()

@chat_bp.route('/chat', methods = ["GET", "POST"])
def chat_view():
    message = None
    try:
        messages = conn.execute(text("SELECT * FROM chatroom_vendor ORDER BY timestamp ASC")).mappings().all()
        return render_template('chat.html', messages=messages)
    except:
        message = "Error fetching messages."
    return render_template('chat.html', message=message, messages=[])
