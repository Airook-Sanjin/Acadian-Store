from flask import Blueprint
from globals import Flask, secrets, redirect, url_for, Connecttodb,text,render_template, execute
from .Register import register_who

auth_bp = Blueprint('auth_bp',__name__,url_prefix='/auth',template_folder='templates')

@auth_bp.route('/Login')
def Login():
    conn = Connecttodb()
    # Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    
    return render_template('login.html')

@auth_bp.route('/Logout')
def Logout():
    return 'logout'

auth_bp.add_url_rule('/register', view_func=register_who, endpoint='register')

@auth_bp.route('/register')
def redirect_to_register_view():
    return redirect(url_for('register_who'))





