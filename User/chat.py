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
            chat_id = request.form.get("chat_id")

            if action:
                user_type = request.form.get("user_type")
                vendor_id = request.form.get("vendor_id")
                admin_id = request.form.get("admin_id")
                product_id = request.form.get("product_id")
                message_text = request.form.get("message")
                image_url = request.form.get("image_url")
                user_email = g.User["Email"]
                user_role = g.User["Role"]

                if not product_id or (user_type == "Vendor" and not vendor_id) or (user_type == "Admin" and not admin_id):
                    return render_template("chat.html", message="Please select a product and user.", previous_chats=[], selected_chat=None)

                try:
                    product_id = int(product_id)
                except (TypeError, ValueError):
                    return render_template("chat.html", message="Invalid product ID.", previous_chats=[], selected_chat=None)

                if user_role != "customer":
                    return render_template("chat.html", message="Only customers can initiate chats.", previous_chats=[], selected_chat=None)

                user_id = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).scalar()

                result = conn.execute(text("INSERT INTO chat () VALUES ()"))
                conn.commit()
                chat_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

                if not chat_id:
                    return render_template("chat.html", message="Could not create new chat ID.", previous_chats=[], selected_chat=None)

                returns = 'YES' if action == "RETURN" else 'NO'
                refund = 'YES' if action == "REFUND" else 'NO'
                warranty_claim = 'YES' if action == "WARRANTY CLAIM" else 'NO'

                if user_type == "Vendor":
                    conn.execute(text("""INSERT INTO chatroom_vendor (CHAT_ID, CID, VID, PID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :cid, :vid, :pid, :images, '* * Start of Chat * *', :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
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
                    conn.execute(text("""INSERT INTO chatroom_admin (CHAT_ID, CID, AID, PID, images, message, returns, refund, warranty_claim, timestamp) VALUES (:chat_id, :cid, :aid, :pid, :images, '* * Start of Chat * *', :returns, :refund, :warranty_claim, CURRENT_TIMESTAMP)
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

            elif chat_id:
                message_text = request.form.get("message")
                image_url = request.form.get("image_url")

                chat_type_check = conn.execute(text("""SELECT 'vendor' AS chat_type FROM chatroom_vendor WHERE CHAT_ID = :chat_id UNION
                    SELECT 'admin' AS chat_type FROM chatroom_admin WHERE CHAT_ID = :chat_id LIMIT 1"""), {"chat_id": chat_id}).mappings().first()
                chat_type = chat_type_check["chat_type"] if chat_type_check else None
                if not chat_type:
                    return render_template("chat.html", message="Invalid chat type.", previous_chats=[], selected_chat=None)

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

                flags = conn.execute(text(f"SELECT returns, refund, warranty_claim FROM chatroom_{chat_type} WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC LIMIT 1"), {"chat_id": chat_id}).mappings().first()

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

            else:
                message = "Invalid chat context."
                return render_template("chat.html", message=message, previous_chats=[], selected_chat=None)

        except Exception as e:
            print(f"Error in POST chat handler: {e}")
            return render_template("chat.html", message="An error occurred.", previous_chats=[], selected_chat=None)

    user_email = g.User["Email"]
    user_role = g.User["Role"]
    partner_username = None
    customer_name = None
    product_title = None
    vendors = conn.execute(text("SELECT vendor.VID, users.username FROM vendor JOIN users ON vendor.email = users.email")).mappings().all()
    admins = conn.execute(text("SELECT admin.AID, users.username FROM admin JOIN users ON admin.email = users.email")).mappings().all()
    all_products = conn.execute(text("SELECT PID, title, VID FROM product")).mappings().all()

    if user_role == "customer":
        customer_result = conn.execute(text("SELECT CID FROM customer WHERE email = :email"), {"email": user_email}).fetchone()
        if not customer_result:
            return render_template("chat.html", message="Customer not found.", messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)
        user_id = customer_result.CID
        user_type = "CID"
        vendor_chats = conn.execute(text("SELECT CHAT_ID, VID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        admin_chats = conn.execute(text("SELECT CHAT_ID, AID AS VID, PID, 'admin' AS chat_type FROM chatroom_admin WHERE CID = :cid"), {"cid": user_id}).mappings().all()
        chats = {chat["CHAT_ID"]: chat for chat in (vendor_chats + admin_chats)}.values()

    elif user_role == "vendor":
        vendor_result = conn.execute(text("SELECT VID FROM vendor WHERE email = :email"), {"email": user_email}).fetchone()
        if not vendor_result:
            return render_template("chat.html", message="Vendor not found.", messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)
        user_id = vendor_result.VID
        user_type = "VID"
        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID, 'vendor' AS chat_type FROM chatroom_vendor WHERE VID = :vid"), {"vid": user_id}).mappings().all()

    elif user_role == "admin":
        admin_result = conn.execute(text("SELECT AID FROM admin WHERE email = :email"), {"email": user_email}).fetchone()
        if not admin_result:
            return render_template("chat.html", message="Admin not found.", messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)
        user_id = admin_result.AID
        user_type = "AID"
        chats = conn.execute(text("SELECT DISTINCT CHAT_ID, CID, PID, 'admin' AS chat_type FROM chatroom_admin WHERE AID = :aid"), {"aid": user_id}).mappings().all()

    else:
        message = "Invalid user role."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)

    if not chats:
        message = "No chats found. Create a new chat to start."
        return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)

    chat_id = request.form.get("chat_id") or request.args.get("chat_id")
    if not chat_id:
        try:
            chat_id = list(chats)[0]["CHAT_ID"]
        except:
            message = "No chat ID found."
            return render_template("chat.html", message=message, messages=[], previous_chats=[], selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)
    chat_details = conn.execute(text("SELECT CHAT_ID, CID, VID, PID, images, message, returns, refund, warranty_claim FROM chatroom_vendor WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
    chat_type = "vendor"
    if not chat_details:
        chat_details = conn.execute(text("SELECT CHAT_ID, CID, AID, PID, images, message, returns, refund, warranty_claim, request_status FROM chatroom_admin WHERE CHAT_ID = :chat_id"), {"chat_id": chat_id}).mappings().first()
        chat_type = "admin" if chat_details else None

    if not chat_details:
        message = "Chat not found."
        return render_template("chat.html", message=message, messages=[], previous_chats=chats, selected_chat=None, vendors=vendors, admins=admins, all_products=all_products)

    selected_chat = dict(chat_details)
    selected_chat['chat_type'] = chat_type

    messages = conn.execute(text(f"SELECT * FROM chatroom_{chat_type} WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()
    product_title = conn.execute(text("SELECT title FROM product WHERE PID = :pid"), {"pid": selected_chat["PID"]}).scalar()
    customer_name = conn.execute(text("SELECT users.name FROM customer JOIN users ON customer.email = users.email WHERE CID = :cid"), {"cid": selected_chat["CID"]}).scalar()
    if chat_type == "vendor":
        partner_username = conn.execute(text("SELECT users.username FROM vendor JOIN users ON vendor.email = users.email WHERE VID = :vid"), {"vid": selected_chat["VID"]}).scalar()
    elif chat_type == "admin":
        partner_username = conn.execute(text("SELECT users.username FROM admin JOIN users ON admin.email = users.email WHERE AID = :aid"), {"aid": selected_chat["AID"]}).scalar()

    return render_template("chat.html", messages=messages, selected_chat=selected_chat, previous_chats=chats, message=None, vendors=vendors, admins=admins, all_products=all_products,
        product_title=product_title if product_title else "N/A", customer_name=customer_name if customer_name else "N/A", partner_username=partner_username if partner_username else "N/A")