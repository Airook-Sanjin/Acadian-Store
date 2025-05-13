from globals import Flask, redirect, url_for,render_template,session,g,Connecttodb,text,request

def checkAndUpdateOrder():
    try:
        conn=Connecttodb()
        
        result1= conn.execute(text("""
            UPDATE orders as o set status = 'Shipping', DateShipped = CURRENT_TIMESTAMP
            WHERE EXISTS(Select 1 from cart as c WHERE c.ORDER_ID = o.ORDER_ID
            GROUP BY c.ORDER_ID
            HAVING COUNT(*) = SUM(CASE WHEN c.ItemStatus != 'Pending' THEN 1 ELSE 0 END))
            AND o.status != 'Shipping'
                          """))
        row1 = result1.rowcount
        conn.commit()
        result2= conn.execute(text("""
            UPDATE cart set ItemStatus = 'Delivered'
            WHERE CURDATE() > DATE_ADD(DateShipped, INTERVAL 5 DAY)
                          """))
        row2 = result2.rowcount
        conn.commit()
        print(f"Updated {row1} orders to Shipping")
        print(f"Updated {row2} cart items to Delivered")
    except Exception as e:
        print(f'Error Updating Item Status: {e}')
        
def CheckOrderDelivered():
    try:
        conn=Connecttodb()
        
        result = conn.execute(text("""
            UPDATE orders set status = 'Delivered'
            WHERE CURDATE() > DATE_ADD(DateShipped, INTERVAL 5 DAY)
            AND status = 'Shipping'
                          """))
        rowsOrder = result.rowcount
        conn.commit()
        print(f"Updated {rowsOrder} orders to Delivered")
    except Exception as e:
        print(f'Error Updating order Status {e}')