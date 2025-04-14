from flask import Blueprint
from globals import Flask, secrets, redirect, url_for, Connecttodb,text,render_template
from .Register import register_who

login_bp = Blueprint('login_bp',__name__,url_prefix='/login',template_folder='templates')

@login_bp.route('/Login')
def Login():
    conn = Connecttodb()
    # Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    
    return render_template('login.html')

@login_bp.route('/Logout')
def Logout():
    return 'logout'

login_bp.add_url_rule('/register', view_func=register_who, endpoint='register')

@login_bp.route('/register')
def redirect_to_register_view():
    return redirect(url_for('register_who'))





