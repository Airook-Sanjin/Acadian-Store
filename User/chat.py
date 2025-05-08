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
    if request.method == "POST":
        try:
            # Retrieve form data
            user_type = request.form.get("user_type")
            vendor_id = request.form.get("vendor_id")
            admin_id = request.form.get("admin_id")
            product_id = request.form.get("product_id")
            action = request.form.get("action")
            chat_id = request.form.get("chat_id")
            chat_type = request.form.get("chat_type")
            message_text = request.form.get("message")
            image_url = request.form.get("image_url")
            user_email = g.User["Email"]
            user_role = g.User["Role"]

            # Assign user_id based on user role
            try:
                if user_role == "customer":
                    user_id = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).scalar()
                elif user_role == "vendor":
                    user_id = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).scalar()
                elif user_role == "admin":
                    user_id = conn.execute(text("SELECT AID FROM admin WHERE email = :email"), {"email": user_email}).scalar()
                else:
                    return render_template("chat.html", message="Invalid user role.", previous_chats=[], selected_chat=None)

                if not user_id:
                    return render_template("chat.html", message="User ID not found.", previous_chats=[], selected_chat=None)
                print(f"User Role: {user_role}, User ID: {user_id}")  # Debugging
            except Exception as e:
                print(f"Error fetching user ID: {e}")
                return render_template("chat.html", message="An error occurred while fetching user ID.", previous_chats=[], selected_chat=None)

            # Insert a new row into the `chat` table to generate a CHAT_ID
            try:
                result = conn.execute(text("INSERT INTO chat () VALUES ()"))
                conn.commit()
                chat_id = result.lastrowid  # Retrieve the generated CHAT_ID
                print(f"Generated CHAT_ID: {chat_id}")  # Debugging
            except Exception as e:
                print(f"Error inserting into chat table: {e}")
                return render_template("chat.html", message="An error occurred while creating a new chat.", previous_chats=[], selected_chat=None)

            # Convert boolean values to 'YES'/'NO'
            returns = 'YES' if action == "RETURN" else 'NO'
            refund = 'YES' if action == "REFUND" else 'NO'
            warranty_claim = 'YES' if action == "WARRANTY CLAIM" else 'NO'

            # Insert into the appropriate chatroom table
            if user_type == "Vendor" and action:
                try:
                    print(f"Inserting into chatroom_vendor with CHAT_ID: {chat_id}")  # Debugging
                    conn.execute(text("""
                        INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, images, message, returns, refund, warranty_claim, timestamp)
                        VALUES (:chat_id, :cid, :vid, :pid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
                    """), {
                        "chat_id": chat_id,
                        "cid": user_id,
                        "vid": vendor_id,
                        "pid": product_id,
                        "images": image_url,
                        "message": message_text,
                        "returns": returns,
                        "refund": refund,
                        "warranty_claim": warranty_claim
                    })
                    conn.commit()
                except Exception as e:
                    print(f"Error inserting into chatroom_vendor: {e}")
                    return render_template("chat.html", message="An error occurred while creating a vendor chat.", previous_chats=[], selected_chat=None)

            elif user_type == "Admin" and action:
                try:
                    print(f"Inserting into chatroom_admin with CHAT_ID: {chat_id}")  # Debugging
                    conn.execute(text("""
                        INSERT INTO chatroom_admin (CHAT_ID, CID, AID, PID, images, message, returns, refund, warranty_claim, timestamp)
                        VALUES (:chat_id, :cid, :aid, :pid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
                    """), {
                        "chat_id": chat_id,
                        "cid": user_id,
                        "aid": admin_id,
                        "pid": product_id,
                        "images": image_url,
                        "message": message_text,
                        "returns": returns,
                        "refund": refund,
                        "warranty_claim": warranty_claim
                    })
                    conn.commit()
                except Exception as e:
                    print(f"Error inserting into chatroom_admin: {e}")
                    return render_template("chat.html", message="An error occurred while creating an admin chat.", previous_chats=[], selected_chat=None)

            return redirect(url_for("chat_bp.chat_view", chat_id=chat_id))

        except Exception as e:
            print(f"Error creating chat or sending message: {e}")
            return render_template("chat.html", message="An error occurred while processing your request.", previous_chats=[], selected_chat=None)

    # Existing GET logic for displaying chats
    user_email = g.User["Email"]
    user_role = g.User["Role"]

    # Defining user role and ID
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

        vendor_chats = conn.execute(text("""
            SELECT CHAT_ID, VID, PID, 'vendor' AS chat_type
            FROM chatroom_vendor
            WHERE CID = :cid"""), {"cid": user_id}).mappings().all()
        admin_chats = conn.execute(text("""
            SELECT CHAT_ID, AID AS VID, PID, 'admin' AS chat_type
            FROM chatroom_admin
            WHERE CID = :cid"""), {"cid": user_id}).mappings().all()
        chats = {chat["CHAT_ID"]: chat for chat in (vendor_chats + admin_chats)}.values()
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
    else:
        message = "Invalid user role."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    # Check for chats
    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    chat_id = request.args.get("chat_id")
    if not chat_id:
        try:
            chat_id = list(chats)[0]["CHAT_ID"]
        except:
            message = "No chat ID found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    try:
        # Retrieve chat details
        print(f"Fetching chat details for CHAT_ID: {chat_id}")  # Debugging
        chat_details = conn.execute(text("""
            SELECT CHAT_ID, CID, VID, PID, images, message, returns, refund, warranty_claim
            FROM chatroom_vendor
            WHERE CHAT_ID = :chat_id
        """), {"chat_id": chat_id}).mappings().first()

        chat_type = "vendor"
        if not chat_details:
            chat_details = conn.execute(text("""
                SELECT CHAT_ID, CID, AID, PID, images, message, returns, refund, warranty_claim
                FROM chatroom_admin
                WHERE CHAT_ID = :chat_id
            """), {"chat_id": chat_id}).mappings().first()
            chat_type = "admin" if chat_details else None

        if not chat_details:
            print(f"Chat not found for CHAT_ID: {chat_id}")  # Debugging
            return render_template("chat.html", message="Chat not found.", previous_chats=chats, selected_chat=None)

        selected_chat = dict(chat_details)
        selected_chat['chat_type'] = chat_type
        print(f"Selected Chat: {selected_chat}")  # Debugging

        messages = conn.execute(text(f"""
            SELECT * FROM chatroom_{chat_type}
            WHERE CHAT_ID = :chat_id
            ORDER BY timestamp ASC
        """), {"chat_id": chat_id}).mappings().all()

        return render_template("chat.html", messages=messages, selected_chat=selected_chat, previous_chats=chats, message=None)

    except Exception as e:
        print(f"Error: {e}")
        return render_template("chat.html", message="An error occurred.", previous_chats=[], selected_chat=None)