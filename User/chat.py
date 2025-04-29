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

    message = " "

    if request.method == "POST":
        vendor_id = request.form.get("vendor_id")
        product_id = request.form.get("product_id")
        new_chat_id = None
        if vendor_id and product_id:
            new_chat_id = conn.execute(text("SELECT MAX(CHAT_ID) + 1 AS new_chat_id FROM chat")).scalar()
            if not new_chat_id:
                new_chat_id = 1

            conn.execute(text("INSERT INTO chat (CHAT_ID) VALUES (:chat_id)"), {"chat_id": new_chat_id})

            conn.execute(text("INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, message, timestamp) VALUES (:chat_id, :cid, :vid, :pid, :message, CURRENT_TIMESTAMP)"),
                        {"chat_id": new_chat_id, "cid": user_id if user_role == "customer" else None, "vid": vendor_id, "pid": product_id, "message": "* * Start of Chat * *"})
            conn.commit()
            return redirect(url_for("chat_bp.chat_view", chat_id=new_chat_id))

        message_content = request.form.get("message")
        chat_id = request.args.get("chat_id")
        if not chat_id:
            message = "Chat ID is missing. Please select a chat."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

        if message_content:
            chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
            if not chat_details:
                message = "Chat details not found. Please try again."
                return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

            conn.execute(text(f"INSERT INTO chatroom_vendor (CHAT_ID, {user_type}, PID, message, timestamp) VALUES (:chat_id, :user_id, :pid, :message, CURRENT_TIMESTAMP)"),
                        {"chat_id": chat_id, "user_id": user_id, "pid": chat_details["PID"], "message": message_content})
            conn.commit()

            return redirect(url_for("chat_bp.chat_view", chat_id=chat_id))
    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    chat_id = request.args.get("chat_id")
    if not chat_id:
        chat_id = chats[0]["CHAT_ID"]

    chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
    messages = conn.execute(text("SELECT * FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()

    message = message if message else " "

    return render_template("chat.html", messages=messages, previous_chats=chats, selected_chat=chat_details, message=message)