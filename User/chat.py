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
            action = request.form.get("action")
            if action:
                user_type = request.form.get("user_type")
                vendor_id = request.form.get("vendor_id")
                admin_id = request.form.get("admin_id")
                product_id = request.form.get("product_id")
                message_text = request.form.get("message")
                image_url = request.form.get("image_url")
                user_email = g.User["Email"]
                user_role = g.User["Role"]

                if user_role == "customer":
                    user_id = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).scalar()
                else:
                    message = "Only customers can initiate chats."
                    return render_template("chat.html", message=message, previous_chats=[], selected_chat=None)

                result = conn.execute(text("INSERT INTO chat () VALUES ()"))
                conn.commit()
                chat_id = result.lastrowid

                returns = 'YES' if action == "RETURN" else 'NO'
                refund = 'YES' if action == "REFUND" else 'NO'
                warranty_claim = 'YES' if action == "WARRANTY CLAIM" else 'NO'

                if user_type == "Vendor":
                    conn.execute(text("""
                        INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, message, returns, refund, warranty_claim, timestamp)
                        VALUES (:chat_id, :cid, :vid, :pid, '* * Start of Chat * *', :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
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
                elif user_type == "Admin":
                     conn.execute(text("""
                        INSERT INTO chatroom_admin (CHAT_ID, CID, AID, PID, message, returns, refund, warranty_claim, timestamp)
                        VALUES (:chat_id, :cid, :aid, :pid, '* * Start of Chat * *', :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
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
                return redirect(url_for("chat_bp.chat_view", chat_id=chat_id))

            else:
                chat_id = request.form.get("chat_id")
                chat_type = request.form.get("chat_type")
                message_text = request.form.get("message")
                image_url = request.form.get("image_url")

                if not chat_id or not chat_type:
                    return render_template("chat.html", message="Invalid chat context.", previous_chats=[], selected_chat=None)

                user_email = g.User["Email"]
                user_role = g.User["Role"]

                if user_role == "customer":
                    user_id = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).scalar()
                elif user_role == "vendor":
                    user_id = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).scalar()
                elif user_role == "admin":
                    user_id = conn.execute(text("SELECT AID FROM admin WHERE email = :email"), {"email": user_email}).scalar()
                else:
                    return render_template("chat.html", message="Invalid user role.", previous_chats=[], selected_chat=None)

                if chat_type == "vendor":
                    flag_query = text("SELECT returns, refund, warranty_claim FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC LIMIT 1")
                elif chat_type == "admin":
                    flag_query = text("SELECT returns, refund, warranty_claim FROM chatroom_admin WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC LIMIT 1")
                else:
                    return render_template("chat.html", message="Invalid chat type.", previous_chats=[], selected_chat=None)

                flags = conn.execute(flag_query, {"chat_id": chat_id}).mappings().first()
                returns = flags["returns"] if flags else "NO"
                refund = flags["refund"] if flags else "NO"
                warranty_claim = flags["warranty_claim"] if flags else "NO"

                values ={
                    "chat_id": chat_id,
                    "images": image_url,
                    "message": message_text,
                    "returns": returns,
                    "refund": refund,
                    "warranty_claim": warranty_claim}

                if chat_type == "vendor":
                    if user_role == "customer":
                        values["cid"] = user_id
                        sql = "INSERT INTO chatroom_vendor (CHAT_ID, CID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :cid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"
                    elif user_role == "vendor":
                        values["vid"] = user_id
                        sql = "INSERT INTO chatroom_vendor (CHAT_ID, VID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :vid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"
                elif chat_type == "admin":
                    if user_role == "customer":
                        values["cid"] = user_id
                        sql = "INSERT INTO chatroom_admin (CHAT_ID, CID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :cid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"
                    elif user_role == "admin":
                        values["aid"] = user_id
                        sql = "INSERT INTO chatroom_admin (CHAT_ID, AID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :aid, :images, :message, :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)"
                conn.execute(text(sql), values)
                conn.commit()
                return redirect(url_for("chat_bp.chat_view", chat_id=chat_id))

        except Exception as e:
            print(f"Error in POST chat handler: {e}")
            return render_template("chat.html", message="An error occurred.", previous_chats=[], selected_chat=None)

    user_email = g.User["Email"]
    user_role = g.User["Role"]

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

    if not chats:
        message = "No chats found."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    chat_id = request.form.get("chat_id") or request.args.get("chat_id")
    if not chat_id:
        try:
            chat_id = list(chats)[0]["CHAT_ID"]
        except:
            message = "No chat ID found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None)

    try:
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
            message = "Chat not found."
            return render_template("chat.html", message=message, previous_chats=chats, selected_chat=None)

        selected_chat = dict(chat_details)
        selected_chat['chat_type'] = chat_type

        messages = conn.execute(text(f"""
            SELECT * FROM chatroom_{chat_type}
            WHERE CHAT_ID = :chat_id
            ORDER BY timestamp ASC
        """), {"chat_id": chat_id}).mappings().all()

        return render_template("chat.html", messages=messages, selected_chat=selected_chat, previous_chats=chats, message=None)

    except Exception as e:
        print(f"Error: {e}")
        return render_template("chat.html", message="An error occurred.", previous_chats=[], selected_chat=None)