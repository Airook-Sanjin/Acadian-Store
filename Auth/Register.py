from globals import render_template, Connecttodb, text, request

def register_who():
    # is logic for who is registering
    # logic still not added (pending)
    
    return render_template('Register.html')

def register_view_customer():
    EMAIL = request.form.get("email")
    USERNAME = request.form.get("username")
    FULL_NAME = request.form.get("fname")
    PASSWORD = request.form.get("password")
    
    USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
                                          values (email,username,name,password)"""),
                                                    {'email': EMAIL,
                                                     'username': USERNAME,
                                                     'name': FULL_NAME,
                                                     'password':PASSWORD})
    
    CUSTOMER = Connecttodb.execute(text("""INSERT INTO customer (email) 
                                          values (email)"""),{'email':EMAIL})
    return render_template()

def register_view_vendor():
    # EMAIL = 
    # USERNAME = 
    # NAME = 
    # PASSWORD = 
    # USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
    #                                       values ()"""), {})
    # VENDOR = Connecttodb.execute(text("""INSERT INTO customer (email) 
    #                                       values ()"""),{})
    return render_template()

def register_view_admin():
    # EMAIL = 
    # USERNAME = 
    # NAME = 
    # PASSWORD = 
    
    # USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
    #                                       values ()"""), {})
    # ADMIN = Connecttodb.execute(text("""INSERT INTO customer (email) 
    #                                       values ()"""),{})
    return render_template()