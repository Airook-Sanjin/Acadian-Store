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
        try:
            customer_result = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).fetchone()
            if not customer_result:
                message = "Customer not found."
                return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
            user_id = customer_result.CID
            user_type = "CID"
        except:
            message = "Error fetching customer ID"
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

        vendor_chats = conn.execute(text("SELECT CHAT_ID, VID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        admin_chats = conn.execute(text("SELECT CHAT_ID, AID AS VID, PID, 'admin' AS chat_type FROM chatroom_admin WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        chats = {chat["CHAT_ID"]: chat for chat in (vendor_chats + admin_chats)}.values()
    # Vendor role
    elif user_role == "vendor":
        try:
            vendor_result = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).fetchone()
            if not vendor_result:
                message = "Vendor not found."
                return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
            user_id = vendor_result.VID
            user_type = "VID"
        except:
            message = "Error fetching vendor ID."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE VID = :vid"), {"vid": user_id}).mappings().all()
    # Admin role
    elif user_role == "admin":
        try:
            admin_result = conn.execute(text("SELECT AID FROM admin WHERE email = :email"), {"email": user_email}).fetchone()
            if not admin_result:
                message = "Admin not found."
                return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
            user_id = admin_result.AID
            user_type = "AID"
        except:
            message = "Error fetching admin ID."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

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
        try:
            chat_id = list(chats)[0]["CHAT_ID"]
        except:
            message = "No chat ID found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    try:
        if request.method == "POST":
        # Get information from the form
            user_type_selected = request.form.get("user_type")
            admin_id = request.form.get("admin_id")
            vendor_id = request.form.get("vendor_id")
            product_id = request.form.get("product_id")
            user_id = g.User.get("ID")
            message_content = request.form.get("message")
            image_url = request.form.get("image_url")
            action = request.form.get("action")
            error_message = None
            new_chat_id = None

            # Determine which column to set to "YES" based on the action
            returns = "YES" if action == "RETURN" else "NO"
            refund = "YES" if action == "REFUND" else "NO"
            warranty_claim = "YES" if action == "WARRANTY CLAIM" else "NO"

            # Creating a new admin chat
            if user_type_selected == "Admin" and admin_id and product_id:
                new_chat_id = conn.execute(text("SELECT MAX(CHAT_ID) + 1 AS new_chat_id FROM chat")).scalar()
                if not new_chat_id or new_chat_id is None:
                    new_chat_id = 1

                conn.execute(text("INSERT INTO chat (CHAT_ID) VALUES (:chat_id)"), {"chat_id": new_chat_id})
                conn.commit()

                conn.execute(text("""INSERT INTO chatroom_admin (CHAT_ID, CID, AID, PID, message, returns, refund, warranty_claim, timestamp)
                                VALUES (:chat_id, :cid, :aid, :pid, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"""),
                                {"chat_id": new_chat_id,
                                "cid": user_id,
                                "aid": admin_id,
                                "pid": product_id,
                                "message": "* * Start of Chat * *",
                                "returns": returns,
                                "refund": refund,
                                "warranty_claim": warranty_claim})
                conn.commit()
                return redirect(url_for("chat_bp.chat_view", chat_id=new_chat_id))
            # Creating a new vendor chat
            elif user_type_selected == "Vendor" and vendor_id and product_id:
                new_chat_id = conn.execute(text("SELECT MAX(CHAT_ID) + 1 AS new_chat_id FROM chat")).scalar()
                if not new_chat_id or new_chat_id is None:
                    new_chat_id = 1

                conn.execute(text("INSERT INTO chat (CHAT_ID) VALUES (:chat_id)"), {"chat_id": new_chat_id})
                conn.commit()

                conn.execute(text("""INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, message, returns, refund, warranty_claim, timestamp)
                            VALUES (:chat_id, :cid, :vid, :pid, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"""),
                            {"chat_id": new_chat_id,
                            "cid": user_id,
                            "vid": vendor_id,
                            "pid": product_id,
                            "message": "* * Start of Chat * *",
                            "returns": returns,
                            "refund": refund,
                            "warranty_claim": warranty_claim})
                conn.commit()
                return redirect(url_for("chat_bp.chat_view", chat_id=new_chat_id))
            # Sending messages in existing chats
            elif message_content:
                chat_id = request.args.get("chat_id")
                chat_details = conn.execute(text("""
                    SELECT CHAT_ID, CID, VID, PID, returns, refund, warranty_claim
                    FROM chatroom_vendor
                    WHERE CHAT_ID = :chat_id
                """), {"chat_id": chat_id}).mappings().first()

                chat_type = "vendor"
                if not chat_details:
                    chat_details = conn.execute(text("""
                        SELECT CHAT_ID, CID, AID, PID, returns, refund, warranty_claim
                        FROM chatroom_admin
                        WHERE CHAT_ID = :chat_id
                    """), {"chat_id": chat_id}).mappings().first()
                    chat_type = "admin" if chat_details else None

                # Check if chat exists
                if not chat_details:
                    message = "Chat not found."
                    return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

                # Insert message into the appropriate chatroom
                if chat_type == "vendor":
                    conn.execute(text("""
                        INSERT INTO chatroom_vendor (CHAT_ID, CID, PID, message, images, timestamp)
                        VALUES (:chat_id, :cid, :pid, :message, :images, CURRENT_TIMESTAMP)
                    """), {
                        "chat_id": chat_id,
                        "cid": user_id,
                        "pid": chat_details["PID"],
                        "message": message_content,
                        "images": image_url
                    })
                elif chat_type == "admin":
                    conn.execute(text("""
                        INSERT INTO chatroom_admin (CHAT_ID, CID, PID, message, images, timestamp)
                        VALUES (:chat_id, :cid, :pid, :message, :images, CURRENT_TIMESTAMP)
                    """), {
                        "chat_id": chat_id,
                        "cid": user_id,
                        "pid": chat_details["PID"],
                        "message": message_content,
                        "images": image_url
                    })
                conn.commit()
                return redirect(url_for("chat_bp.chat_view", chat_id=chat_id))

        # Retrieve chat details for GET requests
        chat_id = request.args.get("chat_id")
        chat_details = conn.execute(text("""
            SELECT CHAT_ID, CID, VID, PID, returns, refund, warranty_claim
            FROM chatroom_vendor
            WHERE CHAT_ID = :chat_id
        """), {"chat_id": chat_id}).mappings().first()

        chat_type = "vendor"
        if not chat_details:
            chat_details = conn.execute(text("""
                SELECT CHAT_ID, CID, AID, PID, returns, refund, warranty_claim
                FROM chatroom_admin
                WHERE CHAT_ID = :chat_id
            """), {"chat_id": chat_id}).mappings().first()
            chat_type = "admin" if chat_details else None

        # Check if chat exists
        if not chat_details:
            message = "Chat not found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

        # Pass chat details to the template
        selected_chat = dict(chat_details)
        selected_chat['chat_type'] = chat_type

        messages = conn.execute(text(f"""
            SELECT * FROM chatroom_{chat_type}
            WHERE CHAT_ID = :chat_id
            ORDER BY timestamp ASC
        """), {"chat_id": chat_id}).mappings().all()

        return render_template("chat.html", messages=messages, selected_chat=selected_chat, message=None)

    except Exception as e:
        message = f"An error occurred: {e}"
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)
