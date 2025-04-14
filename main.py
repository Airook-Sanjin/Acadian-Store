from flask import Flask, render_template, request, session, redirect, url_for, g
from sqlalchemy import create_engine, text, update
import secrets 

app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn_str = "mysql://root:cset155@localhost/acadiandb" # connects to DataBase
engine = create_engine(conn_str, echo=True)
conn = engine.connect()








if __name__ == '__main__':
        app.run(debug=True)
    