from flask import Blueprint,render_template

admin=Blueprint('admin',__name__, url_prefix='/admin')


@admin.route('/Home')
def AdminHomePage():
    return 'AdminPage'