Group Members:
Tonya Hu - Users Guru
Kevin Kong - Sellers Guru
Emily Sun - Products Guru
Connie Xu - Carts Guru
Jenny Yan - Social Guru

Tonya, Kevin, and Emily worked on the Figma mockups. Connie and Jenny did the database design. 
Every member was added to a shared gitlab repository and was able to run the project locally.

Repository Link: https://gitlab.oit.duke.edu/ejs83/mini-amazon-skeleton/-/tree/main

Standard Project

Team Name: KISS

README.txt for Milestone #3

For all endpoints:
base.html
__init__.py

Files for Users Guru endpoint:
apps/models/order.py
apps/order.py
order.html

Files for Products Guru endpoint:
apps/models/inventory.py
index.html
apps/index.py
apps/models/product.py

Files for Sellers Guru endpoint:
apps/models/inventory.py
inventory.hmtl
apps/inventory.py

Files for Carts Guru endpoint:
apps/models/cart.py
cart.html 
apps/cart.py

Files for Social Guru endpoint:
apps/models/reviews.py
reviews.html 
apps/reviews.py

Video Link for Milestone 3 Demo:
https://drive.google.com/file/d/1QzeAJrC98IDPBmSKBKVaCLNGcIELLVCt/view?usp=sharing

README.txt for Milestone #4

Code for generating and populating our databases:
db/generated/gen.py

Video Link for Milestone 4 Demo:
https://drive.google.com/file/d/1fw_1tj9Aq3NQ1qMKOVs_QjwZl1gcMXl6/view?usp=sharing

Summary of Milestone 4 features:
Users: Made main account page where you can access balance history, order history, and public profile.
Implemented balance history and pagination to show all previous transactions (withdrawals and reloads). Functionality for transactions is now working.
Order history that also links to more details for a specific order.
Display information for public profile, including reviews if a user is a seller.

Products: Formatted main products display page to include paginated list of products.
Created cards for each product listing the image, name, lowest price, category, and average rating.
Implemented basic sorting and filtering features that control the number of products per page, sorting by name, price, or category, and filtering by category.
Created ProductView page for specific products that list more details as well as all the sellers and reviews for a product.
ProductView page has buttons to add specific quantities to cart and add reviews for a product.

Carts: Formatted carts page, including pagination of items. Implemented updating quantity and deleting 
items from the cart. Implemented submit order functionality, which performs all constraint checks and
appears to correctly update balance, inventories, cart, and order. Formatted orders and order details pages. 

Sellers: Added pagination list of inventory items for current seller. Implemented "edit product" 
functionality to update database with the new unit price and quantity of an inventory item, 
including a delete button to remove the item from the seller's inventory. Added front-end for
"add product" button. 

Social: Added tabs for different category of reviews and added pagination for reviews for each category. 
Incorporated upvote that updates upvote count. Created write product review page that add new reviews for product.
Created write seller review page that allow users to rate sellers whom they have purhcased from. 

README.txt for Final Submission 

Complete Final Submission Video: https://drive.google.com/file/d/1J942O2wFYWY_Sd7XyCcMQ3LoJyScE8LA/view?usp=sharing

We would like to be scored as a team. 
