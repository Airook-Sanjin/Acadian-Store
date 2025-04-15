from flask import Blueprint,render_template
from User.chat import chat_bp


admin=Blueprint('admin',__name__, url_prefix='/admin',template_folder='templates') # * init blueprint
admin.register_blueprint(chat_bp)

@admin.route('/Home')
def AdminHomePage():
    return render_template('AdminHomepage.html')