from sqlalchemy import create_engine, text, update
#  function that connects to database
def Connecttodb():
    
    conn_str = "mysql://root:cset155@localhost/acadiandb" # connects to DataBase
    engine = create_engine(conn_str, echo=True)
    return engine.connect()
    
