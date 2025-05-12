from globals import Flask, redirect, url_for,render_template,session,g,Connecttodb,text,request

def checkAndUpdateOrder():
    try:
        conn=Connecttodb()
        
        conn.execute(text("""
            UPDATE orders as o set status = 'Shipping'
            WHERE EXISTS(Select 1 from cart as c WHERE c.ORDER_ID = o.ORDER_ID
            GROUP BY c.ORDER_ID
            HAVING COUNT(*) = SUM(CASE WHEN c.ItemStatus != 'Pending' THEN 1 ELSE 0 END))
            AND o.status != 'Shipping'
                          """))
        conn.commit()
    except Exception as e:
        print(f'Error Updating order Status')