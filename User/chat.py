from flask import Blueprint, render_template, request, redirect, url_for
from dbconnect import Connecttodb
from sqlalchemy import text

chat_bp = Blueprint('chat_bp', __name__, template_folder='templates', static_folder='static')

@chat_bp.route('/chat')
def chat_view():
    return render_template('chat.html')