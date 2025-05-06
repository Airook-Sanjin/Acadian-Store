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

# Defining user role and ID
    # Customer role
    if user_role == "customer":
        customer_result = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).fetchone()
        if not customer_result:
            message = "Customer not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
        user_id = customer_result.CID
        user_type = "CID"

        vendor_chats = conn.execute(text("SELECT CHAT_ID, VID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        admin_chats = conn.execute(text("SELECT CHAT_ID, AID AS VID, PID, 'admin' AS chat_type FROM chatroom_admin WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        chats = {chat["CHAT_ID"]: chat for chat in (vendor_chats + admin_chats)}.values()
    # Vendor role
    elif user_role == "vendor":
        vendor_result = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).fetchone()
        if not vendor_result:
            message = "Vendor not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
        user_id = vendor_result.VID
        user_type = "VID"

        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE VID = :vid"), {"vid": user_id}).mappings().all()
    # Admin role
    elif user_role == "admin":
        admin_result = conn.execute(text("SELECT AID FROM admin WHERE email = :email"), {"email": user_email}).fetchone()
        if not admin_result:
            message = "Admin not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
        user_id = admin_result.AID
        user_type = "AID"

        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID, 'admin' AS chat_type FROM chatroom_admin WHERE AID = :aid"), {"aid": user_id}).mappings().all()
    # Invalid role
    else:
        message = "Invalid user role."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    # Check for chats
    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
    chat_id = request.args.get("chat_id")
    # If there's no chat_id, use the first chat in the list
    if not chat_id and chats:
        chat_id = list(chats)[0]["CHAT_ID"]


    if request.method == "POST":
        # Get information from sending messages + creating new chats
        user_type_selected = request.form.get("user_type")
        admin_id = request.form.get("admin_id")
        vendor_id = request.form.get("vendor_id")
        product_id = request.form.get("product_id")
        message_content = request.form.get("message")
        image_url = request.form.get("image_url")
        error_message = None
        new_chat_id = None

        # Checks for image URL
        if image_url:
            valid_extensions = (".jpg", ".jpeg", ".png", ".gif")
            if not image_url.lower().endswith(valid_extensions):
                error_message = "Image URL is not valid."
                image_url = None

        # Creating a new admin chat
        if user_type_selected == "Admin" and admin_id and product_id:
            new_chat_id = conn.execute(text("SELECT MAX(CHAT_ID) + 1 AS new_chat_id FROM chat")).scalar()
            if not new_chat_id or new_chat_id is None:
                new_chat_id = 1

            conn.execute(text("INSERT INTO chat (CHAT_ID) VALUES (:chat_id)"), {"chat_id": new_chat_id})
            conn.execute(text("INSERT INTO chatroom_admin (CHAT_ID, CID, AID, PID, message, timestamp) VALUES (:chat_id, :cid, :aid, :pid, :message, CURRENT_TIMESTAMP)"),
                        {"chat_id": new_chat_id, "cid": user_id, "aid": admin_id, "pid": product_id, "message": "* * Start of Chat * *"})
            conn.commit()
            return redirect(url_for("chat_bp.chat_view", chat_id=new_chat_id))
        # Creating a new vendor chat
        elif user_type_selected == "Vendor" and vendor_id and product_id:
            new_chat_id = conn.execute(text("SELECT MAX(CHAT_ID) + 1 AS new_chat_id FROM chat")).scalar()
            if not new_chat_id or new_chat_id is None:
                new_chat_id = 1

            conn.execute(text("INSERT INTO chat (CHAT_ID) VALUES (:chat_id)"), {"chat_id": new_chat_id})
            conn.execute(text("INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, message, timestamp) VALUES (:chat_id, :cid, :vid, :pid, :message, CURRENT_TIMESTAMP)"),
                        {"chat_id": new_chat_id, "cid": user_id, "vid": vendor_id, "pid": product_id, "message": "* * Start of Chat * *"})
            conn.commit()
            return redirect(url_for("chat_bp.chat_view", chat_id=new_chat_id))
        # Sending messages in existing chats
        elif message_content:
            chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
            chat_type = "vendor"
            if not chat_details:
                chat_details = conn.execute(text("SELECT CHAT_ID, CID, AID, PID FROM chatroom_admin WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
                chat_type = "admin" if chat_details else None

            # Check if chat exists
            if not chat_details:
                message = "Chat not found."
                return render_template("chat.html", message=message, messages=[], previous_chats=chats, selected_chat=None)

            # Get chat details
            if chat_type == "vendor":
                conn.execute(text(f"INSERT INTO chatroom_vendor (CHAT_ID, {user_type}, PID, message, images, timestamp) VALUES (:chat_id, :user_id, :pid, :message, :images, CURRENT_TIMESTAMP)"),
                            {"chat_id": chat_id, "user_id": user_id, "pid": chat_details["PID"], "message": message_content, "images": image_url})
            elif chat_type == "admin":
                conn.execute(text(f"INSERT INTO chatroom_admin (CHAT_ID, {user_type}, PID, message, images, timestamp) VALUES (:chat_id, :user_id, :pid, :message, :images, CURRENT_TIMESTAMP)"),
                            {"chat_id": chat_id, "user_id": user_id, "pid": chat_details["PID"], "message": message_content, "images": image_url})
            conn.commit()
            return redirect(url_for("chat_bp.chat_view", chat_id=chat_id, message=error_message))
        # If no message content is provided, return an error message
        else:
            message = "No message content provided."
            return render_template("chat.html", message=message, messages=[], previous_chats=chats, selected_chat=None)

    chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
    chat_type = "vendor"
    if not chat_details:
        chat_details = conn.execute(text("SELECT CHAT_ID, CID, AID, PID FROM chatroom_admin WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
        chat_type = "admin" if chat_details else None

    # Check if chat exists
    if not chat_details:
        message = "Chat not found."
        return render_template("chat.html", message=message, messages=[], previous_chats=chats, selected_chat=None)

    # Selecting chat type and details
    selected_chat = dict(chat_details)
    selected_chat['chat_type'] = chat_type
    if chat_type == "admin":
        selected_chat['AID'] = chat_details.get('AID')
    elif chat_type == "vendor":
        selected_chat['VID'] = chat_details.get('VID')
    else:
        selected_chat['VID'] = None
        selected_chat['AID'] = None

    # Getting messages for the selected chat and chat type
    if chat_type == "vendor":
        messages = conn.execute(text("SELECT * FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()
    elif chat_type == "admin":
        messages = conn.execute(text("SELECT * FROM chatroom_admin WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()
    else:
        messages = []

    return render_template("chat.html", messages=messages, previous_chats=chats, selected_chat=selected_chat, message=None)