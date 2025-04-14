from globals import Flask, secrets, redirect, url_for, Connecttodb, text
from Auth import login_bp
app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn = Connecttodb()


app.register_blueprint(login_bp)

@app.route('/')
def start():
    return redirect(url_for("login_bp.Login"))




if __name__ == '__main__':
        app.run(debug=True)