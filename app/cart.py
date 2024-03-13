from flask import render_template, request, flash
from flask_login import current_user
from flask_paginate import Pagination, get_page_parameter

from .models.cart import CartItem
from .models.inventory import Inventory
from .models.balance import Balance
from .models.order import Order, OrderItem

from flask import Blueprint
from flask import jsonify
from flask import redirect, url_for 

from datetime import datetime

bp = Blueprint('cart', __name__)

@bp.route('/cart')
def cart_items():
    """ retrieves all products in the current user's cart and saved for later"""

    # Set the page, per_page, and total pages for pagination

    cart_per_page = 5
    saved_per_page = 6
    cart_page, cart_total, cart_pagination, cart_offset = get_pagination_info('cart', cart_per_page)
   
    saved_page, saved_total, saved_pagination, saved_offset = get_pagination_info('saved', saved_per_page)

    # Retrieve cart items and saved items for the current user
    cart_items = []
    saved_items = []
    subtotal = 0
    if current_user.is_authenticated:
        cart_items = CartItem.get_items_by_user(current_user.id, offset=cart_offset, num_items=cart_per_page)
        saved_items = CartItem.get_items_by_user(current_user.id, saved_for_later=True, offset=saved_offset, num_items=saved_per_page)
        subtotal = CartItem.total_cost(current_user.id)

    return render_template('cart.html', cart_items=cart_items, saved_items=saved_items, subtotal=subtotal, cart_pagination=cart_pagination, saved_pagination=saved_pagination)

def get_pagination_info(page_name, per_page):
    """ 
    helper function to get pagination information
    :param page_name: name of the page
    :param per_page: number of items per page
    """
    # Set the page, per_page, and total pages for pagination
    curr_page = request.args.get(f'{page_name}_page', type=int, default=1)
    total = CartItem.get_total_items_by_user(current_user.id, saved_for_later=(page_name == 'saved')) if current_user.is_authenticated else 0
    pagination = Pagination(cart_page = curr_page, saved_page = curr_page, page_parameter=f'{page_name}_page', per_page=per_page, total=total)
    offset = (curr_page - 1) * per_page
    return curr_page, total, pagination, offset

@bp.route('/cart/update/<int:pid>/<int:seller_id>', methods=['POST'])
def cart_update_quantity(pid, seller_id):
    """ 
    updates the quantity of a product in the user's cart 
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
        
    # retrieves product information
    product = Inventory.get_by_product_and_seller(pid, seller_id)
    quantity = int(request.form['quantity'])

    if quantity == 0:
        return cart_delete(pid, seller_id, saved_for_later=False)
    
    # if update is successful, redirect to cart that reflects the quantity change
    if CartItem.update_quantity(current_user.id, pid, seller_id, quantity):
        flash('Quantity updated successfully!')
    else:
        flash('Quantity update failed. Please try again.', 'error')
    return redirect(request.referrer)
    
@bp.route('/cart/add/<int:pid>/<int:seller_id>', methods=['POST'])
def cart_add(pid, seller_id):
    """ 
    adds a product to the user's cart 
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    # retrieves product information
    product = Inventory.get_by_product_and_seller(pid, seller_id)
    quantity = int(request.form['quantity'])

    # check if quantity is available
    if quantity > product.quantity:
        flash(f'Quantity of {product.p_name} is not available in this amount. Please try again.', 'error')
        return redirect(request.referrer)

    # check if item already exists in cart (item can exist in saved for later at the same time)
    cart_item = CartItem.get_item(current_user.id, pid, seller_id, saved_for_later=False)
    if cart_item:
        quantity += cart_item.quantity

        if quantity > product.quantity:
            flash(f'Quantity of {product.p_name} is not available in this amount, so it has been set to the max amount.', 'error')
            quantity = product.quantity

        res = CartItem.update_quantity(current_user.id, pid, seller_id, quantity)
    else: 
        date_added = datetime.now()
        res = CartItem.add_item(current_user.id, pid, seller_id, quantity, product.unit_price, date_added)
    
    if res:
        flash('Item added successfully!')
    else:
        flash('Item add failed. Please try again.', 'error')

    return redirect(request.referrer)

@bp.route('/cart/delete/<int:pid>/<int:seller_id>/<string:saved_for_later>', methods=['POST'])
def cart_delete(pid, seller_id, saved_for_later):
    """ 
    updates the quantity of a product in the user's cart or saved for later
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    :param saved_for_later: whether the product is saved for later
    """
    # if delete is successful, redirect to cart that reflects the change
    if CartItem.delete_item(current_user.id, pid, seller_id, saved_for_later=(saved_for_later == 'True')):
        flash('Item deleted successfully!')
    else:
        flash('Item deletion failed. Please try again.', 'error')
    return redirect(request.referrer)

@bp.route('/cart/save_for_later/<int:pid>/<int:seller_id>', methods=['POST'])
def cart_save_for_later(pid, seller_id):
    """ 
    moves the product from the user's cart to saved for later
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    # if item already exists in saved for later, update quantity of item in saved for later and delete item from cart
    saved_item = CartItem.get_item(current_user.id, pid, seller_id, saved_for_later=True)
    if saved_item:
        cart_item = CartItem.get_item(current_user.id, pid, seller_id)
        new_quantity = cart_item.quantity + saved_item.quantity
        res1 = CartItem.update_quantity(current_user.id, pid, seller_id, new_quantity, saved_for_later=True)
        res2 = CartItem.delete_item(current_user.id, pid, seller_id)
        if res1 and res2:
            flash('Item saved for later successfully!')
        else:
            flash('Item save failed. Please try again.', 'error')
    else:
        # if save is successful, redirect to cart that reflects the change
        if CartItem.update_saved_for_later(current_user.id, pid, seller_id, saved_for_later=False, new_saved_for_later=True):
            flash('Item saved for later successfully!')
        else:
            flash('Item save failed. Please try again.', 'error')
    
    return redirect(request.referrer)

@bp.route('/cart/move_to_cart/<int:pid>/<int:seller_id>', methods=['POST'])
def cart_move_to_cart(pid, seller_id):
    """ 
    moves the product from saved for later to the user's cart
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    # if item already exists in cart, update quantity of item in cart and delete item from saved for later
    cart_item = CartItem.get_item(current_user.id, pid, seller_id)
    if cart_item:
        saved_item = CartItem.get_item(current_user.id, pid, seller_id, saved_for_later=True)
        new_quantity = cart_item.quantity + saved_item.quantity

        if new_quantity > cart_item.max_quantity:
            flash(f'Quantity of {cart_item.p_name} is not available in this amount, so it has been set to the max amount.', 'error')
            new_quantity = cart_item.max_quantity
        
        res1 = CartItem.update_quantity(current_user.id, pid, seller_id, new_quantity)
        res2 = CartItem.delete_item(current_user.id, pid, seller_id, saved_for_later=True)
        if res1 and res2:
            flash('Item moved to cart successfully!')
        else:
            flash('Item move failed. Please try again.', 'error')
    else:
        # if move is successful, redirect to cart that reflects the change
        if CartItem.update_saved_for_later(current_user.id, pid, seller_id, saved_for_later=True, new_saved_for_later=False):
            flash('Item moved to cart successfully!')
        else:
            flash('Item move failed. Please try again.', 'error')
    return redirect(request.referrer)

@bp.route('/cart/place_order', methods=['POST'])
def cart_place_order():
    """ 
    submits the order for user's cart
    """
    seller_profits = dict()
    line_items = CartItem.get_items_by_user(current_user.id, saved_for_later=False)

    # check if cart is empty
    if len(line_items) == 0:
        flash('Cart is empty.', 'error')
        return redirect(url_for('cart.cart_items'))

    for line_item in line_items:
        seller_id, quantity, unit_price = line_item.seller_id, line_item.quantity, line_item.inv_unit_price
        max_quantity = Inventory.get_by_product_and_seller(line_item.pid, line_item.seller_id).quantity
        
        # check if quantity is available
        if quantity > max_quantity or max_quantity == 0:
            flash(f'Quantity of {line_item.p_name} is not available in this amount. Please try again.', 'error')
            return redirect(url_for('cart.cart_items'))

        # track seller profits
        if line_item.seller_id not in seller_profits:
            seller_profits[line_item.seller_id] = 0.0
        seller_profits[line_item.seller_id] += quantity * unit_price

    # retrieve subtotal 
    subtotal = CartItem.total_cost(current_user.id, saved_for_later=False)

    # check if subtotal <= balance
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_balance = Balance.get_current_balance_by_uid(current_user.id)
    if subtotal > user_balance:
        flash('Insufficient balance. Please try again.', 'error')
        return redirect(url_for('cart.cart_items'))

    # update seller's balance
    for seller_id, profit in seller_profits.items():
        balance = Balance.get_current_balance_by_uid(seller_id)
        balance += profit 
        Balance.add_balance(seller_id, timestamp, balance, 'SELL', None)

    # update seller's inventory
    for line_item in line_items:
        inventory_item = Inventory.get_by_product_and_seller(line_item.pid, line_item.seller_id)
        Inventory.update_item(line_item.pid, line_item.seller_id, inventory_item.unit_price,  inventory_item.quantity - line_item.quantity)
    
    # update buyer's order
    order_id = Order.add_order(current_user.id, timestamp)

    # update buyer's balance
    user_balance -= subtotal 
    Balance.add_balance(current_user.id, timestamp, user_balance, 'Buy', order_id)

    # update buyer's order details
    for line_item in line_items:
        OrderItem.add_order_details(order_id, line_item.pid, line_item.seller_id, line_item.quantity, line_item.inv_unit_price)

    # delete all items from cart
    CartItem.delete_all(current_user.id, saved_for_later=False)

    flash('Order submitted successfully!')
    return redirect(url_for('orders.user_orders'))
