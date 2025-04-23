from flask import Blueprint, render_template, request, redirect, url_for, session, g
from dbconnect import Connecttodb
from sqlalchemy import text

chat_bp = Blueprint('chat_bp', __name__, template_folder='templates', static_folder='static')
conn = Connecttodb()

@chat_bp.before_request
def load_user():
    if "User" in session:
        g.User = session["User"]
    else:
        return redirect(url_for('login_bp.Login'))

@chat_bp.route('/chat', methods=["GET", "POST"])
def chat_view():
    user_email = g.User["Email"]
    customer_result = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).fetchone()
    if not customer_result:
        message = "Customer not found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
    customer_id = customer_result.CID
    chats = conn.execute(text("SELECT DISTINCT CHAT_ID FROM chatroom_vendor WHERE CID = :cid"),
                        {"cid": customer_id}).mappings().all()
    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
    chat_id = request.args.get("chat_id")
    if not chat_id:
        chat_id = chats[0]["CHAT_ID"]
    messages = conn.execute(text("SELECT * FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"),
                            {"chat_id": chat_id}).mappings().all()
    selected_chat = {"CHAT_ID": chat_id, "vendor_name": "Vendor", "product_name": "Product"}
    return render_template("chat.html", messages=messages, previous_chats=chats, selected_chat=selected_chat, message=None)