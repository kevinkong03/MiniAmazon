\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
-- since id is auto-generated; we need the next command to adjust the counter
-- for auto-generation so next INSERT will not clash with ids loaded above:
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Categories FROM 'Categories.csv' WITH DELIMITER ',' NULL '' CSV

\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_pid_seq',
                         (SELECT MAX(pid)+1 FROM Products),
                         false);

\COPY CartItem FROM 'Carts.csv' WITH DELIMITER ',' NULL '' CSV                         
\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV    
\COPY Orders FROM 'Orders.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.orders_order_id_seq',
                         (SELECT MAX(order_id)+1 FROM Orders),
                         false);  
\COPY OrderItem FROM 'OrderItems.csv' WITH DELIMITER ',' NULL '' CSV   

-- \COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
-- SELECT pg_catalog.setval('public.purchases_id_seq',
--                          (SELECT MAX(id)+1 FROM Purchases),
--                          false);

\COPY Wishlist FROM 'Wishlist.csv' WITH DELIMITER ',' NULL '' CSV

\COPY ProductReviews FROM 'ProductReviews.csv' WITH DELIMITER ',' NULL '' CSV
\COPY SellerReviews FROM 'SellerReviews.csv' WITH DELIMITER ',' NULL '' CSV

\COPY Balances FROM 'Balances.csv' WITH DELIMITER ',' NULL '' CSV

