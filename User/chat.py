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
    user_role = g.User["Role"]

    if user_role == "customer":
        customer_result = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).fetchone()
        if not customer_result:
            message = "Customer not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
        user_id = customer_result.CID
        user_type = "CID"
        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, VID, PID FROM chatroom_vendor WHERE CID = :cid"), {"cid": user_id}).mappings().all()

    elif user_role == "vendor":
        vendor_result = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).fetchone()
        if not vendor_result:
            message = "Vendor not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
        user_id = vendor_result.VID
        user_type = "VID"
        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID FROM chatroom_vendor WHERE VID = :vid"), {"vid": user_id}).mappings().all()

    else:
        message = "Invalid user role."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    chat_id = request.args.get("chat_id")
    if not chat_id:
        chat_id = chats[0]["CHAT_ID"]

    chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
    if request.method == "POST":
        message_content = request.form.get("message")
        if message_content:
            conn.execute(text(f"INSERT INTO chatroom_vendor (CHAT_ID, {user_type}, PID, message, timestamp) VALUES (:chat_id, :user_id, :pid, :message, CURRENT_TIMESTAMP)"),
                        {"chat_id": chat_id, "user_id": user_id, "pid": chat_details["PID"], "message": message_content})
            conn.commit()
    messages = conn.execute(text("SELECT * FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()
    return render_template("chat.html", messages=messages, previous_chats=chats, selected_chat=chat_details, message=None)