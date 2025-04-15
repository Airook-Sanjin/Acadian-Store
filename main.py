from flask import Flask, redirect, url_for
from Auth.Login import login_bp
from Auth.Register import register_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)

@app.route('/')
def start():
    return redirect(url_for("login_bp.Login"))

if __name__ == '__main__':
        app.run(debug=True)  