from sqlalchemy import create_engine

def Connecttodb():
    conn_str = "mysql://root:cset155@localhost/acadiandb"  # Replace with your actual database credentials
    engine = create_engine(conn_str, echo=True)
    return engine.connect()  # Return the connection object