from flask import Blueprint,render_template


admin=Blueprint('admin',__name__, url_prefix='/admin',template_folder='templates')


@admin.route('/Home')
def AdminHomePage():
    return render_template('AdminHomepage.html')