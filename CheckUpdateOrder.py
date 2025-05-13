from globals import Flask, redirect, url_for,render_template,session,g,Connecttodb,text,request

def checkAndUpdateOrder():
    try:
        conn=Connecttodb()
        # Debug query to check eligible orders
        debug_orders = conn.execute(text("""
            SELECT o.ORDER_ID, o.status,
                   COUNT(*) as total_items,
                   SUM(CASE WHEN c.ItemStatus = 'Delivered' THEN 1 ELSE 0 END) as delivered_items
            FROM orders o
            JOIN cart c ON c.ORDER_ID = o.ORDER_ID
            WHERE o.status = 'Shipping'
            GROUP BY o.ORDER_ID, o.status
        """))
        print("\nEligible orders before update:")
        for row in debug_orders:
            print(f"Order {row.ORDER_ID}: Status={row.status}, Delivered={row.delivered_items}/{row.total_items}")

        # Update orders to Shipping
        result1 = conn.execute(text("""
            UPDATE orders as o 
            SET status = 'Shipping', 
                DateShipped = CURRENT_TIMESTAMP
            WHERE EXISTS (
                SELECT 1 FROM cart as c 
                WHERE c.ORDER_ID = o.ORDER_ID
                GROUP BY c.ORDER_ID
                HAVING COUNT(*) = SUM(CASE WHEN c.ItemStatus != 'Pending' THEN 1 ELSE 0 END)
            )
            AND o.status = 'Pending'
        """))
        row1 = result1.rowcount
        conn.commit()
        
       # Update cart items to Delivered (fixed query)
        result2 = conn.execute(text("""
            UPDATE cart c
            INNER JOIN orders o ON c.ORDER_ID = o.ORDER_ID
            SET c.ItemStatus = 'Delivered'
            WHERE o.status = 'Shipping'
            AND c.DateShipped IS NOT NULL
            AND DATEDIFF(CURRENT_TIMESTAMP,c.DateShipped) >= 5
            AND c.ItemStatus = 'Shipping'
        """))
        row2 = result2.rowcount
        conn.commit()

        print(f"Updated {row1} orders to Shipping")
        print(f"Updated {row2} cart items to Delivered")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error Updating Item Status: {e}')
    finally:
        if conn:
            conn.close()
        
def CheckOrderDelivered():
    try:
        conn=Connecttodb()
        
        result = conn.execute(text("""
            UPDATE orders as o 
            SET status = 'Delivered'
            WHERE EXISTS (
                SELECT 1 FROM cart as c 
                WHERE c.ORDER_ID = o.ORDER_ID
                GROUP BY c.ORDER_ID
                HAVING COUNT(*) = SUM(CASE WHEN c.ItemStatus = 'Delivered' THEN 1 ELSE 0 END)
            )
            AND o.status = 'Shipping'
        """))
        
        updated = result.rowcount
        conn.commit()
        print(f"\nUpdated {updated} orders to Delivered status")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error Updating order Status {e}')
    finally:
        if conn:
            conn.close()