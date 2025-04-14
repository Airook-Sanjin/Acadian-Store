from globals import render_template, Flask, secrets, redirect, url_for, Connecttocb,text

def register_who():
    # is logic for who is registering
    # logic still not added (pending)
    
    return render_template('Register.html')

def register_view_customer():
    # USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
    #                                       values ()"""), {})
    # CUSTOMER = Connecttodb.execute(text("""INSERT INTO customer (email) 
    #                                       values ()"""),{})
    return render_template()

def register_view_vendor():
    # EMAIL = 
    # USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
    #                                       values ()"""), {})
    # VENDOR = Connecttodb.execute(text("""INSERT INTO customer (email) 
    #                                       values ()"""),{})
    return render_template()

def register_view_admin():
    # USERS = Connecttodb.execute(text("""INSERT INTO users (email,username,name,password) 
    #                                       values ()"""), {})
    # ADMIN = Connecttodb.execute(text("""INSERT INTO customer (email) 
    #                                       values ()"""),{})
    return render_template()

