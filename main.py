from globals import Flask, secrets, redirect, url_for, Connecttocb,text
from Auth import auth_bp
from dbconnect import Connecttocb
app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn = Connecttocb()


app.register_blueprint(auth_bp)

@app.route('/')
def start():
    return redirect(url_for("auth_bp.Login"))




if __name__ == '__main__':
        app.run(debug=True)
    