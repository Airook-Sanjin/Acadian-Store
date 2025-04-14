from flask import blueprints,render_template

auth_bp = blueprints('Auth',__name__)

@auth_bp.route('/Login')
def Login():
    return 'Login'


@auth_bp.route('/Logout')
def Logout():
    return 'logout'