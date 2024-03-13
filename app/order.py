from flask import render_template, request, flash
from flask_login import current_user
from flask_paginate import Pagination
from flask_wtf import FlaskForm
from wtforms import StringField

from .models.order import OrderItem, Order
from .models.inventory import Inventory
from .models.reviews import SellerReview
from .models.product import Product

from flask import Blueprint
from flask import jsonify
from flask import redirect, url_for 

bp = Blueprint('orders', __name__)


@bp.route('/orders')
def user_orders():
    """ find all orders completed by current user """

    # Set the page, per_page, and total pages for pagination
    order_page = request.args.get('order_page', type=int, default=1)
    order_per_page = 10

    buy_again_page = request.args.get('buy_again_page', type=int, default=1)
    buy_again_per_page = 10

     # Calculate the offset 
    order_offset = (order_page - 1) * order_per_page
    buy_again_offset = (buy_again_page - 1) * buy_again_per_page

    orders = []
    total = 0  
    buy_again = []
    buy_again_total = 0

    if current_user.is_authenticated:
        orders = Order.get_orders_by_buyer(current_user.id, order_offset, order_per_page)
        total = Order.get_total_orders_by_buyer(current_user.id)
        buy_again = Product.get_past_orderItems(current_user.id, buy_again_offset, buy_again_per_page)
        buy_again_total = Product.get_total_past_orderItems(current_user.id)

    # print(buy_again)
    # print(buy_again_total)
    order_pagination = Pagination(order_page=order_page, per_page=order_per_page, total=total, page_parameter='order_page')
    buy_again_pagination = Pagination(buy_again_page=buy_again_page, per_page=buy_again_per_page, total=buy_again_total, page_parameter='buy_again_page')
    return render_template('order.html', orders=orders, order_pagination=order_pagination, buy_again=buy_again, buy_again_pagination=buy_again_pagination)

@bp.route('/orders/<int:order_id>')
def user_order_details(order_id):
    """ find all order items for chosen order of current user """

     # Set the page, per_page, and total pages for pagination
    page = request.args.get('page', type=int, default=1)
    per_page = 10 

     # Calculate the offset 
    offset = (page - 1) * per_page

    order_items = []
    subtotal, total = 0, 0

    order_review_info = [] # list of (order_item, seller review status) infos
    if current_user.is_authenticated:
        order_items = OrderItem.get_items_by_order(order_id, offset, per_page)
        total = OrderItem.get_total_items_by_order(order_id)
        subtotal = Order.get_order(order_id).subtotal
        for item in order_items:
            sellers_rated_before = True if SellerReview.have_rated_before(item.seller_id,current_user.id) else False
            order_review_info.append((item, sellers_rated_before))

    pagination = Pagination(page=page, per_page=per_page, total=total)

    return render_template('order_item.html', items=order_review_info, subtotal=subtotal, pagination=pagination)

def get_pagination_info(page_name, per_page, ful_or_unful, unful_name, ful_name):
    """ 
    helper function to get pagination information
    :param page_name: name of the page
    :param per_page: number of items per page
    """
    # Set the page, per_page, and total pages for pagination
    curr_page = request.args.get(f'{page_name}_page', type=int, default=1)
    if ful_or_unful == 'f':
        total = Order.get_total_orders_by_seller(current_user.id, ful_or_unful, ful_name) if current_user.is_authenticated else 0
    else:
        total = Order.get_total_orders_by_seller(current_user.id, ful_or_unful, unful_name) if current_user.is_authenticated else 0
    pagination = Pagination(ful_page = curr_page, unful_page = curr_page, page_parameter=f'{page_name}_page', per_page=per_page, total=total)
    offset = (curr_page - 1) * per_page
    return curr_page, total, pagination, offset

class Unful(FlaskForm):
    unful_name = StringField('unful_name', default='')

class Ful(FlaskForm):
    ful_name = StringField('ful_name', default='')

@bp.route('/orders/history', methods=['GET', 'POST'])
def user_order_history():
    """ display user's order history """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
        
    # Set the page, per_page, and total pages for pagination
    unful_name = request.args.get('unful_name', type=str, default='')
    ful_name = request.args.get('ful_name', type=str, default='')
    per_page = 10
    
    ful_orders = []
    unful_orders = []
    total = 0  
    unful_form = Unful(request.form)
    ful_form = Ful(request.form)

    if request.args.get('unful_name') is not None:
        unful_form.unful_name.data = unful_name

    if request.args.get('ful_name') is not None:
        ful_form.ful_name.data = ful_name

    ful_page, ful_total, ful_pagination, ful_offset = get_pagination_info('ful', per_page, 'f', unful_name.lower(), ful_name.lower())
    unful_page, unful_total, unful_pagination, unful_offset = get_pagination_info('unful', per_page, 'unf', unful_name.lower(), ful_name.lower())

    # get fulfilled and unfulfilled orders
    if current_user.is_authenticated:
        ful_orderID_items = {}
        unful_orderID_items = {}
        ful_orders = Order.get_fulfilled_orders_by_seller(current_user.id, ful_offset, per_page, ful_name.lower())
        unful_orders = Order.get_unfulfilled_orders_by_seller(current_user.id, unful_offset, per_page, unful_name.lower())
        for order in ful_orders:
            items = OrderItem.get_items_for_order(order.order_id, current_user.id)
            ful_orderID_items[order] = items
        for order in unful_orders:
            items = OrderItem.get_items_for_order(order.order_id, current_user.id)
            unful_orderID_items[order] = items

        # analytics
        monthly_sales = Inventory.get_monthly_sales_from_last_12_months(current_user.id)
        yearly_sales = Inventory.get_yearly_sales_from_last_5_years(current_user.id)
        y_sales = [y[1] for y in yearly_sales]
        sales = [m[1] for m in monthly_sales]
        monthly_unique_items = Inventory.get_unique_items_sold_from_last_12_months(current_user.id)
        unique_items = [m[1] for m in monthly_unique_items]

    return render_template('order_history.html', ful_orderID_items=ful_orderID_items, unful_orderID_items=unful_orderID_items, ful_pagination=ful_pagination, unful_pagination=unful_pagination, sales=sales, y_sales=y_sales, unique_items=unique_items, unful_form=unful_form, ful_form=ful_form)

@bp.route('/orders/<int:order_id>/<int:pid>/<int:seller_id>', methods=['GET'])
def mark_line_item(order_id, pid, seller_id):
    """ 
    marks a line item as fulfilled
    :param order_id: order id
    :param pid: product id
    :param seller_id: seller id
    """
    # update fulfillment status of item
    if  OrderItem.update_fulfillment_status(order_id, pid, seller_id, True):
        # update fulfillment status of order if all items are fulfilled by all sellers now
        if OrderItem.check_fulfillment_status(order_id):
            Order.update_order_status(order_id, True)
        return redirect(url_for('orders.user_order_history'))
        