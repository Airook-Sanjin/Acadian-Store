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

@chat_bp.route('/chat', methods = ["GET", "POST"])
def chat_view():
    message = None
    return render_template('chat.html', message=message)







    # if 'User' not in session:
    #     return redirect(url_for('login_bp.Login'))
    # customer_id = session['User']['ID']
    # if request.method == "GET":
    #     try:
    #         previous_chats = conn.execute(text("""SELECT DISTINCT c.CHAT_ID, c.VID, c.PID,
    #                                     v.name AS vendor_name, p.title AS product_name FROM chat c
    #                                     JOIN vendor v ON c.VID = v.VID JOIN product p ON c.PID = p.PID
    #                                     WHERE c.CID = :customer_id"""), {"customer_id": customer_id}).mappings().all()
    #         chat_id = request.args.get("chat_id")
    #         messages = []
    #         if chat_id:
    #             messages = conn.execute(text("SELECT * FROM chatroom_vendor WHERE CHAT_ID = :chat_id ORDER BY timestamp ASC"), {"chat_id": chat_id}).mappings().all()
    #             return render_template('chat.html', messages=messages, previous_chats=previous_chats)
    #     except:
    #         message = "Error fetching chats."
    #         return render_template('chat.html', message=message, previous_chats=[], messages=[])
    # elif request.method == "POST":
    #     vendor_id = request.form.get("vendor_id")
    #     product_id = request.form.get("product_id")
    #     try:
    #         vendor_exists = conn.execute(text("SELECT * FROM vendor WHERE VID = :vendor_id"), {'vendor_id': vendor_id}).fetchone()
    #         if not vendor_exists:
    #             message = "Vendor not found."
    #             return render_template('chat.html', message=message, messages=[], previous_chats=[])
    #         if not product_id:
    #             message = "Select a product."
    #             products = conn.execute(text("SELECT * FROM product WHERE VID = :vendor_id"), {'vendor_id': vendor_id}).mappings().all()
    #             return render_template('chat.html', message=message, previous_chats=[], products=products)
            
    #         product_exists = conn.execute(text("SELECT * FROM product WHERE VID = :vendor_id AND PID = :product_id"), {'vendor_id': vendor_id, 'product_id': product_id}).fetchone()
    #         if not product_exists:
    #             message = "Product not found for this vendor."
    #             return render_template('chat.html', message=message, previous_chats=[], messages=[])
            
    #         chat = conn.execute(text("SELECT * FROM chat WHERE CID = :customer_id AND VID = :vendor_id AND PID = :product_id"),
    #                             {'customer_id': customer_id, 'vendor_id': vendor_id, 'product_id': product_id}).fetchone()
    #         if not chat:
    #             conn.execute(text("INSERT INTO chat (CID, VID, PID) VALUES (:customer_id, :vendor_id, :product_id)"),
    #                         {'customer_id': customer_id, 'vendor_id': vendor_id, 'product_id': product_id})
    #             chat_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    #         else:
    #             chat_id = chat["CHAT_ID"]
    #         return redirect(url_for('chat_bp.chat_view', chat_id=chat_id))
    #     except:
    #         message = "Error during search."
    #         return render_template('chat.html', message=message, previous_chats=[], messages=[])
    # return render_template('chat.html', message=message)
