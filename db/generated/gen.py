from werkzeug.security import generate_password_hash
import csv
import requests
from faker import Faker
from PIL import Image
import random
from datetime import datetime
import re

num_users = 100
num_purchases = 2500
num_categories = 10
num_balances = 1000
max_reviews_per_user = 20
num_orders = 1000
max_items_per_order = 20

Faker.seed(0)
fake = Faker()


def get_csv_writer(f):
    return csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

# parse real_amazon.csv
def parse_amazon_csv():
    """
    each row in real_amazon.csv is [product_id, product_name, category, discounted_price, actual_price, discount_percentage, rating, rating_count, about_product, user_id, user_name, review_id, review_title, review_content, img_link, product_link]
    """
    product_names = []
    image_names = []
    descriptions = []
    categories = []
    product_reviews = dict() # pid to dict of review info
    with open('../real_amazon.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == 'product_id':
                continue

            product_name, about_product, category, review_title, review_content, img_link = row[1], row[8], row[2], row[12], row[13], row[14]
            if product_name not in product_names:
                product_names.append(product_name)
                image_names.append(img_link)
                descriptions.append(about_product if about_product != '' else 'No description available')
                category_with_formatting = re.sub(r'(?<!^)(?=[A-Z&])', ' ', category)
                categories.append(category_with_formatting)
            if product_name not in product_reviews:
                product_reviews[product_name] = []
            product_reviews[product_name].append({'review_title': review_title, 'review_content': review_content})

    # nested category initialization 
    parent_categories = set()
    sub_categories = {}
    for c in categories:
        split = c.split('|')
        parent_category = split[0]
        parent_categories.add(parent_category)
        sub_category = split[1] if len(split) > 1 else ''
        if parent_category not in sub_categories:
            sub_categories[parent_category] = set()
        sub_categories[parent_category].add(sub_category)
    return list(product_names), list(image_names), list(descriptions), categories, parent_categories, sub_categories, product_reviews

# parse seller_reviews.csv
def parse_seller_reviews_csv():
    """
    each row in seller_reviews.csv is [review, rating]
    """
    seller_reviews = [] 
    seller_ratings = []
    with open('../seller_reviews.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == 'review':
                continue
            review, rating = row[0], row[1]
            review = review.replace('Etsy', 'Mini-Amazon') 
            seller_reviews.append(review)
            seller_ratings.append(rating)
    return seller_reviews, seller_ratings


# each row should be [id, email, password, firstname, lastname, address, is_seller]
def gen_users(num_users):
    sellers = dict()
    all_uids = []
    with open('Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for uid in range(num_users):
            all_uids.append(uid)
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            profile = fake.profile()
            email = profile['mail']
            plain_password = f'pass{uid}'
            password = generate_password_hash(plain_password)
            name_components = profile['name'].split(' ')
            firstname = name_components[0]
            lastname = name_components[-1]
            address = profile['address']
            is_seller = fake.random_element(elements=('true', 'false'))
            if is_seller == 'true':
                sellers[uid] = []
            writer.writerow([uid, email, password, firstname, lastname, address, is_seller])
        print(f'{num_users} generated ({len(sellers)} sellers)')
    return sellers

def gen_products(num_products, sellers, product_names, image_names, descriptions, categories, category_cids):
    """
    each row in Products.csv should be [pid, cid, creator_id, name, description, image, available]

    :param num_products: number of products to generate
    :param sellers: dict of seller ids to list of dicts of product info
    :param product_names: list of product names to choose from
    :param image_names: list of image names to choose from
    :param descriptions: list of descriptions to choose from
    :param categories: categories passed in from csv
    :param category_cids: dict of product ids to cids
    :return: list of available product ids
    """
    available_pids = []
    creators = dict() 

    with open('Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for pid in range(num_products):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            # print(categories[pid].split('|'))
            cat_name = categories[pid].split('|')[1]
            cid = category_cids[cat_name]
            # cid = fake.random_int(max=num_categories-1) # cid must exist in Categories.csv
            creator_id = fake.random_element(elements=sellers.keys()) # creator_id must exist in Users.csv and must be a seller 
            name = product_names[pid]
            description = descriptions[pid]


            # copying over unavailableImage to make file paths simpler
            with open('../../app/static/unavailableImage.jpeg', 'rb') as src_file:
                content = src_file.read()
                with open('../../app/static/images/unavailableImage.jpeg', 'wb') as dest_file:
                    dest_file.write(content)


            # making request for image - if failed, then write file path to the unavailableImage image
            if image_names[pid] != '':
                image_url = image_names[pid]
                image = requests.get(image_url)

                if image.status_code == 200:
                    with open(f'../../app/static/images/{pid}.jpg', 'wb') as f:
                        f.write(image.content)
                    image_name = f'{pid}.jpg'
                else:
                    # print(f'Error downloading image: {image.status_code}')
                    image_name = 'unavailableImage.jpeg'
            else:
                image_name = 'unavailableImage.jpeg'

            # image.save(f'../../app/static/images/{pid}.jpg', 'JPEG')
            available = fake.random_element(elements=('true', 'false', 'true', 'true'))
            if available == 'true':
                available_pids.append(pid)

            creators[pid] = creator_id
        
            writer.writerow([pid, cid, creator_id, name, description, image_name, available])
        print(f'{num_products} generated; {len(available_pids)} available')
    return available_pids, creators



def gen_categories(parents, children):
    """
    each row in Categories.csv should be [cid, name, parent_id]
    for fake data, parent_id will be NULL 
    :param parents: set of parent categories
    :param children: dictionary of categories where key is parent and value is set of children
    :return: dictionary of category names with corresponding parents
    """
    with open('Categories.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Categories...', end=' ', flush=True)
        cids = {}
        cid = 0
        for parent in parents:
            if cid % 10 == 0:
                print(f'{cid}', end=' ', flush=True)
            name = parent
            parent_id = ''
            cids[name] = cid
            writer.writerow([cid, name, parent_id])
            cid += 1
            for child in children[parent]:
                if cid % 10 == 0:
                    print(f'{cid}', end=' ', flush=True)
                name = child
                parent_id = cids[parent]
                writer.writerow([cid, name, parent_id])
                cids[name] = cid
                cid += 1
        
        print(f'{cid} categories generated')
    return cids

def gen_inventory(num_products, available_pids, sellers, creators):
    """
    each row in Inventory.csv should be [pid, seller_id, unit_price, quantity]

    :param available_pids: list of available product ids
    :param sellers: dict of seller ids to list of dicts of product info
    """
    total_inventory = 0
    with open('Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Inventory...', end=' ', flush=True)
        for pid in range(num_products):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            num_sellers = fake.random_int(min=1, max=len(sellers.keys()) // 5)
            product_seller_ids = set() # to avoid duplicate sellers for same product
            for i in range(num_sellers):
                if i == 0 and pid in creators:
                    seller_id = creators[pid] # creator of product must be a seller
                else:
                    seller_id = fake.random_element(elements=list(sellers.keys())) # seller_id must exist in Users.csv and must be a seller 
                if seller_id in product_seller_ids: # cannot have duplicate sellers for same product
                    continue
                product_seller_ids.add(seller_id)

                unit_price = f'{str(fake.random_int(max=200))}.{fake.random_int(max=99):02}'
                quantity = fake.random_int(max=20) if pid in available_pids else 0
                sellers[seller_id].append({'pid': pid, 'price': unit_price, 'quantity': quantity})
                writer.writerow([pid, seller_id, unit_price, quantity])
            
            total_inventory += len(product_seller_ids)
            
        print(f'{total_inventory} generated for {len(available_pids)} products')

def gen_carts(num_users, sellers, available_pids):
    """
    each row in CartItems.csv should be [uid, pid, seller_id, quantity, unit_price, date_added, saved_for_later]

    :param num_users: number of users to choose from
    :param sellers: dict of seller ids to list of dicts of product info
    :param available_pids: list of available product ids
    """
    total_cart_items = 0
    sellers_with_avail_products = [seller_id for seller_id in sellers.keys() if len(sellers[seller_id]) > 0] 

    with open('Carts.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Carts...', end=' ', flush=True)
        for uid in range(num_users):
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            num_cart_items = fake.random_int(max=min(len(available_pids), 20)) 

            products = set() # to avoid duplicate products in cart
            for i in range(num_cart_items):
                seller_id = fake.random_element(elements=sellers_with_avail_products) # seller_id must exist in Users.csv and must be a seller 
                if seller_id == uid: # seller cannot be buyer of their own product
                    continue
                
                product = fake.random_element(elements=sellers[seller_id])
                pid = product['pid']
                if product['pid'] in products: # cannot have duplicate products in cart
                    continue

                unit_price = product['price']

                if product['quantity'] == 0: # cannot add product to cart if quantity is 0
                    continue 
            
                quantity = fake.random_int(min=1, max=product['quantity'])
                date_added = fake.date_time_between(end_date=datetime.now())
                saved_for_later = fake.random_element(elements=('true', 'false'))

                products.add(product['pid'])
                writer.writerow([uid, pid, seller_id, quantity, unit_price, date_added, saved_for_later])
            
            total_cart_items += len(products)
        
        print(f'{total_cart_items} generated for {num_users} users')

def gen_productreviews_fake(max_reviews_per_user, num_products, num_users):
    """
    each row in ProductReviews.csv should be [buyer_id, pid, title, rating, message, upvote_count, timestamp]

    :param max_reviews_per_user: maximum number of reviews per user
    :param num_products: number of products to choose from
    :param num_users: number of users to choose from
    """
    total_reviews = 0
    with open('ProductReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('ProductReviews...', end=' ', flush=True)
        for buyer_id in range(num_users):
            if buyer_id % 10 == 0:
                print(f'{buyer_id}', end=' ', flush=True)
            num_reviews = fake.random_int(max=max_reviews_per_user)
            products = set() # to avoid duplicate reviews for same product
            for i in range(num_reviews):
                pid = fake.random_int(max=num_products-1)
                if pid in products: # cannot have duplicate reviews for same product
                    continue
                products.add(pid)

                title = fake.sentence(nb_words=4)[:-1]
                rating = fake.random_int(min=1, max=5)
                message = fake.paragraph(nb_sentences=3)
                upvote_count = fake.random_int(max=1000)
                timestamp = fake.date_time()
                writer.writerow([buyer_id, pid, title, rating, message, upvote_count, timestamp])
            total_reviews += len(products)
        print(f'{total_reviews} generated for {num_users} users')

def gen_productreviews_realistic(product_names, reviews, num_users):
    """
    each row in ProductReviews.csv should be [buyer_id, pid, title, rating, message, upvote_count, timestamp]

    :param product_names: list of product names to choose from
    :param reviews: dict of product names to list of dicts of review info
    :param num_users: number of users to choose from
    """
    total_reviews = 0
    with open('ProductReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('ProductReviews...\n', end=' ', flush=True)
        for product in reviews:
            pid = product_names.index(product)
            
            buyers = set() # to avoid duplicate reviews for same product
            for review_info in reviews[product]:
                buyer_id = fake.random_int(max=num_users-1)
                while buyer_id in buyers:
                    buyer_id = fake.random_int(max=num_users-1)
                buyers.add(buyer_id)
                
                title = review_info['review_title'].split(',')[0]
                lowercase = title.lower()
                if 'good' in lowercase or 'great' in lowercase or 'excellent' in lowercase or 'amazing' in lowercase or 'awesome' in lowercase:
                    rating = fake.random_int(min=4, max=5)
                elif 'bad' in lowercase or 'terrible' in lowercase or 'horrible' in lowercase or 'awful' in lowercase or 'worst' in lowercase:
                    rating = fake.random_int(min=1, max=2)
                else:
                    rating = fake.random_int(min=1, max=5)
                message = review_info['review_content']
                upvote_count = fake.random_int(max=1000)
                timestamp = fake.date_time()
                writer.writerow([buyer_id, pid, title, rating, message, upvote_count, timestamp])

def gen_sellerreviews_fake(max_reviews_per_user, num_users, sellers, orders, buyer_to_order):
    """
    each row in SellerReviews.csv should be [buyer_id, seller_id, title, rating, message, upvote_count, timestamp]

    :param max_reviews_per_user: maximum number of reviews per user
    :param num_users: number of users to choose from
    :param sellers: dict of seller ids to list of dicts of product info that they sell
    :param orders: dict of order ids to seller ids of sellers whose products are in the order
    :param buyer_to_order: dict of buyer ids to order ids
    """
    total_reviews = 0
    with open('SellerReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('SellerReviews...', end=' ', flush=True)
        for buyer_id in range(num_users):
            if buyer_id % 10 == 0:
                print(f'{buyer_id}', end=' ', flush=True)
            num_reviews = fake.random_int(max=max_reviews_per_user)
            
            buyer_orders = buyer_to_order[buyer_id] # orders of buyer

            possible_sellers = set() # sellers that buyers have bought from / can review
            for order_id in buyer_orders:
                possible_sellers.update(set(orders[order_id]))

            sellers_reviewed = set()
            for i in range(num_reviews):
                seller_id = fake.random_element(elements=list(possible_sellers))
                
                if seller_id in sellers_reviewed:
                    continue
                sellers_reviewed.add(seller_id)

                title = fake.sentence(nb_words=4)[:-1]
                rating = fake.random_int(min=1, max=5)
                message = fake.paragraph(nb_sentences=3)
                upvote_count = fake.random_int(max=1000)
                timestamp = fake.date_time()

                writer.writerow([buyer_id, seller_id, title, rating, message, upvote_count, timestamp])
            total_reviews += len(sellers_reviewed)
        
        print(f'{total_reviews} generated for {num_users} users')

def gen_sellerreviews_realistic(seller_reviews, seller_ratings, num_users, sellers, orders, buyer_to_order):
    """
    each row in SellerReviews.csv should be [buyer_id, seller_id, title, rating, message, upvote_count, timestamp]

    :param seller_reviews: list of seller reviews to choose from
    :param seller_ratings: list of seller ratings to choose from
    :param num_users: number of users to choose from
    :param sellers: dict of seller ids to list of dicts of product info that they sell
    :param orders: dict of order ids to seller ids of sellers whose products are in the order
    :param buyer_to_order: dict of buyer ids to order ids
    """
    total_reviews = 0
    with open('SellerReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('SellerReviews...', end=' ', flush=True)

        buyer_seller_pair = set()
        for i in range(len(seller_reviews)):
            if i % 100 == 0:
                print(f'{i}', end=' ', flush=True)
            
            found_buyer = False
            count = 0 
            while found_buyer is False and count < len(sellers.keys()):
                buyer_id = fake.random_int(max=num_users-1)
                buyer_orders = buyer_to_order[buyer_id] # orders of buyer
                possible_sellers = set() # sellers that buyers have bought from / can review
                for order_id in buyer_orders:
                    possible_sellers.update(set(orders[order_id]))
        
                seller_id = fake.random_element(elements=list(possible_sellers))
                if (buyer_id, seller_id) not in buyer_seller_pair:
                    found_buyer = True
                count += 1

            buyer_seller_pair.add((buyer_id, seller_id))

            title = re.split(r'[?.,!]', seller_reviews[i])[0]
            rating = seller_ratings[i]
            message = seller_reviews[i]
            upvote_count = fake.random_int(max=1000)
            timestamp = fake.date_time()
            writer.writerow([buyer_id, seller_id, title, rating, message, upvote_count, timestamp])
        print(f'{len(seller_reviews)} generated')

def gen_orders(num_orders, num_users):
    """
    each row in Orders.csv should be [order_id, buyer_id, order_status, order_date]

    :param max_orders_per_user: maximum number of orders per user
    :param num_users: number of users to choose from
    :return list of unfulfilled order ids
    :return dict of buyer ids to list of order ids
    """
    unfulfilled_orders = []
    order_dates = dict()
    buyer_to_order = dict()
    order_to_buyer = dict()

    with open('Orders.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Orders...', end=' ', flush=True)
        for order_id in range(num_orders):
            if order_id % 100 == 0:
                print(f'{order_id}', end=' ', flush=True)
            buyer_id = fake.random_int(max=num_users-1)
            order_status = fake.random_element(elements=('false', 'true'))
            order_date = fake.date_time_between(start_date="-1y", end_date="now")
            if order_status == 'false':
                unfulfilled_orders.append(order_id)
            order_dates[order_id] = order_date
            
            if buyer_id not in buyer_to_order:
                buyer_to_order[buyer_id] = []

            buyer_to_order[buyer_id].append(order_id)
            order_to_buyer[order_id] = buyer_id

            writer.writerow([order_id, buyer_id, order_status, order_date])
        print(f'{num_orders} generated')
    return unfulfilled_orders, order_dates, buyer_to_order, order_to_buyer

def gen_orderitems(unfulfilled_orders, order_date, order_to_buyer, num_orders, sellers, num_products, max_items_per_order):
    """
    each row in OrderItems.csv should be [order_id, pid, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date]

    :param unfulfilled_orders: list of unfulfilled order ids
    :param order_dates: dict of order ids to order dates
    :param buyer_to_order: dict of buyer ids to order ids
    :param num_orders: number of orders to choose from
    :param sellers: dict of seller ids to list of dicts of product info
    :param num_products: number of products to choose from
    :param max_items_per_order: maximum number of items per order
    :return dict of order ids to list of seller ids whose products are in the order
    """
    total_items = 0
    orders = dict() 
    with open('OrderItems.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('OrderItems...', end=' ', flush=True)
        for order_id in range(num_orders):
            if order_id % 100 == 0:
                print(f'{order_id}', end=' ', flush=True)
           
            num_items = fake.random_int(min=1, max=max_items_per_order)
            products = set()
            for i in range(num_items):

                # remove seller if this current order belongs to them because they cannot sell to themselves
                buyer_id = order_to_buyer[order_id]
                sellers_with_avail_products = [seller_id for seller_id in sellers.keys() if len(sellers[seller_id]) > 0 and seller_id != buyer_id] 

                seller_id = fake.random_element(elements=sellers_with_avail_products)
                product = fake.random_element(elements=sellers[seller_id])

                pid = product['pid']
                if pid in products:
                    continue
                products.add(pid)

                quantity = fake.random_int(max=100)
                unit_price = f'{str(fake.random_int(max=200))}.{fake.random_int(max=99):02}'

                # fulfillment status must be true if order is fulfilled
                fulfillment_status = fake.random_element(elements=('false', 'true')) if order_id in unfulfilled_orders else 'true'
                # fulfillment date must be after order date
                fulfillment_date = fake.date_time_between(start_date=order_dates[order_id]) if fulfillment_status == 'true' else None

                if order_id not in orders:
                    orders[order_id] = []
                orders[order_id].append(seller_id)

                writer.writerow([order_id, pid, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date])
            total_items += len(products)

        print(f'{total_items} generated for {num_orders} orders')
    return orders


def gen_purchases(num_purchases, available_pids):
    with open('Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        for id in range(num_purchases):
            if id % 100 == 0:
                print(f'{id}', end=' ', flush=True)
            uid = fake.random_int(min=0, max=num_users-1)
            pid = fake.random_element(elements=available_pids)
            time_purchased = fake.date_time()
            writer.writerow([id, uid, pid, time_purchased])
        print(f'{num_purchases} generated')
    return

def gen_balances(num_balances, num_users, num_orders):
    with open('Balances.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Balances...', end=' ', flush=True)
        for id in range(num_balances):
            if id % 100 == 0:
                print(f'{id}', end=' ', flush=True)
            uid = fake.random_int(min=0, max=num_users-1)
            timestamp = fake.date_time()
            amount = f'{str(fake.random_int(max=10000))}.{fake.random_int(max=99):02}'

            transactions = ['Withdraw', 'Reload', 'Buy', 'Sell']
            transaction = random.choice(transactions)

            related_order_id = None
            if transaction == 'Buy':
                related_order_id = fake.random_int(min=0, max=num_orders-1)

            writer.writerow([uid, timestamp, amount, transaction, related_order_id])
        print(f'{num_balances} generated')
    return

def gen_wishlist(num_items, available_pids, num_users):
    """
    each row in Wishlist.csv should be [uid, pid, time_added]
    :param num_items: number of items to generate
    :param available_pids: list of available product ids
    :param num_users: number of users to choose from
    """
    with open('Wishlist.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Wishlist Items...', end=' ', flush=True)
        combos = set()
        for wishlist_item in range(num_items):
            if wishlist_item % 100 == 0:
                print(f'{wishlist_item}', end=' ', flush=True)
            uid = fake.random_int(min=0, max=num_users-1)
            pid = fake.random_element(elements=available_pids)
            if (uid,pid) in combos:
                continue
            combos.add((uid,pid))
            time_added = fake.date_time()
            writer.writerow([uid, pid, time_added])
        print(f'{num_items} generated')
    return

# parse real_amazon.csv
product_names, image_names, descriptions, categories, parent_categories, sub_categories, product_reviews = parse_amazon_csv()
num_products = len(product_names)
print(f'{num_products} products, {len(image_names)} images, {len(categories)} categories, {len(descriptions)} descriptions')

# parse seller_reviews.csv
seller_reviews, seller_ratings = parse_seller_reviews_csv()

sellers = gen_users(num_users)
cid_list = gen_categories(parent_categories, sub_categories)
available_pids, creators = gen_products(num_products, sellers, product_names, image_names,descriptions, categories, cid_list)
gen_inventory(num_products, available_pids, sellers, creators)
gen_carts(num_users, sellers, available_pids)
unfulfilled_orders, order_dates, buyer_to_order, order_to_buyer = gen_orders(num_orders, num_users)
orders = gen_orderitems(unfulfilled_orders, order_dates, order_to_buyer, num_orders, sellers, num_products, max_items_per_order)
# gen_productreviews_fake(max_reviews_per_user, num_products, num_users)
gen_productreviews_realistic(product_names, product_reviews, num_users)
# gen_sellerreviews_fake(max_reviews_per_user, num_users, sellers, orders, buyer_to_order)
gen_sellerreviews_realistic(seller_reviews, seller_ratings, num_users, sellers, orders, buyer_to_order)
gen_balances(num_balances, num_users, num_orders)
gen_wishlist(num_products, available_pids, num_users)
