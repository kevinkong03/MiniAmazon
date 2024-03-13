from flask import render_template, request, flash
from flask_login import current_user
from flask_paginate import Pagination
from .models.inventory import Inventory
from .models.product import Product
from .models.category import Category
from .models.user import User
from .models.cart import CartItem
from flask_wtf import FlaskForm
from wtforms import StringField

from flask import Blueprint
from flask import jsonify
from flask import redirect, url_for 

import os

bp = Blueprint('inventory', __name__)

class KForm(FlaskForm):
    keyWord = StringField('keyWord', default='')

# display all inventory items
@bp.route('/inventory', methods=['GET', 'POST'])
def inventory_items():
    """
    renders page to display all items in the seller's inventory
    """

    # Set the page, per_page, and total pages for pagination
    page = request.args.get('page', type=int, default=1)
    keyWord = request.args.get('keyWord', type=str, default='')
    per_page = 20  # 20 items per page

    form = KForm(request.form)

    # Calculate the offset 
    offset = (page - 1) * per_page

    # if the form is submitted, then update the values
    if request.args.get('keyWord') is not None:
        form.keyWord.data = keyWord
    
    # find the inventory items for current user
    if current_user.is_authenticated:
        items = Inventory.get_by_seller(current_user.id, offset, per_page, keyWord.lower())
        total = Inventory.get_total_items(current_user.id, keyWord.lower())
    else:
        items = []
        total = 0

    pagination = Pagination(page=page, per_page=per_page, total=total)
    return render_template('inventory.html', products=items, pagination=pagination, form=form)

# display edit item page
@bp.route('/inventory/edit/<int:pid>')
def edit_inventory_item(pid):
    """ 
    edit item page for a seller's product
    :param pid: product id
    """
    
    categories = None
    
    # find the inventory items for current user
    if current_user.is_authenticated:
        item = Inventory.get_by_product_and_seller(pid, current_user.id)
        id = Product.get_creator_id(pid)
        categories = Category.get_all()
        is_creator = False
        if(id == current_user.id):
            is_creator = True
    else:
        item = None
        is_creator = False
    
    return render_template('inventory_edit_item.html', item=item, is_creator=is_creator, categories=categories)


# update item details
@bp.route('/inventory/update/<int:pid>/<int:seller_id>', methods=['POST'])
def item_update_details(pid, seller_id):
    """ 
    updates a seller's product
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
        
    # retrieves product information
    product = Inventory.get_by_product_and_seller(pid, current_user.id)
    
    # retrieves quantity from form in cart.html
    unit_price = float(request.form['unit_price'])
    quantity = int(request.form['quantity'])
    description, category = product.description, product.category

    # if the seller is the creator of the product, then they can update the description and category
    id = Product.get_creator_id(pid)
    if(id == current_user.id):
        # upload image chosen for the flask form to the static/images folder
        image = request.files['image']
        image.save(os.path.join(os.getcwd() + '/app/static/images', f'{pid}.jpg'))

        description = str(request.form['description'])
        category = str(request.form['category'])
        
        cid = Category.get_cid_by_name(category)
        if Product.update_item(pid, current_user.id, description, cid, f'{pid}.jpg') and Inventory.update_item(pid, current_user.id, unit_price, quantity):

            # update product availability in products table
            Product.update_availability(pid, True)

            return redirect(url_for('inventory.inventory_items'))

    # if update is successful, redirect to inventory that reflects the price/quantity change(s)
    if Inventory.update_item(pid, current_user.id, unit_price, quantity):

        # update product availability in products table if necessary
        products = Inventory.get_by_product(pid)
        avail = any([product.quantity == 0 for product in products])
        Product.update_availability(pid, avail)

        return redirect(url_for('inventory.inventory_items'))

# delete item from inventory
@bp.route('/inventory/delete/<int:pid>/<int:seller_id>', methods=['POST'])
def item_delete(pid, seller_id):
    """ 
    deletes item from inventory
    :param pid: product id
    :param seller_id: seller id of seller selling the product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    if Inventory.delete(pid, current_user.id):
        # delete item from buyers' carts
        CartItem.delete_seller_item(pid, current_user.id)

        # update product availability in products table if necessary
        products = Inventory.get_by_product(pid)
        avail = any([product.quantity != 0 for product in products])
        Product.update_availability(pid, avail)

        return redirect(url_for('inventory.inventory_items'))

# display add existing product item page
@bp.route('/inventory/add-product')
def add_product_item():
    """
    renders page to add a current product to the seller's inventory
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    products = Product.get_all_product_list(seller=current_user.id)

    return render_template('inventory_add_product_item.html', items=products)


# display add new item page
@bp.route('/inventory/add-new')
def add_new_item():
    """
    renders page to add a new product to the seller's inventory
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    products = Product.get_all_product_list(seller=current_user.id)
    categories = Category.get_all()

    return render_template('inventory_add_new_item.html', items=products, categories=categories)

# add an existing product from db to seller's inventory
@bp.route('/inventory/add-product/existing', methods=['POST'])
def add_existing_product_to_inventory():
    """
    functionality to add an existing product to the seller's inventory
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    product_name = str(request.form['product_name'])
    quantity = str(request.form['quantity'])
    unit_price = str(request.form['unit_price'])
    pid = Product.get_by_name(product_name)

    # check if product name already exists in inventory
    if pid != None and Inventory.does_product_exist_in_inventory(pid, current_user.id):
        flash(f'{product_name} is an existing product in your inventory.', 'error')
        return redirect(url_for('inventory.inventory_items'))

    if Inventory.add_item(pid, current_user.id, unit_price, quantity):
        # on the first time a user is a seller, update is_seller to True
        if User.get(current_user.id).is_seller == False:
            User.update_is_seller(current_user.id)
        return redirect(url_for('inventory.inventory_items'))
    else:
        flash(f'{product_name} is not an existing product. Please try again on this page.', 'error')
        return redirect(url_for('inventory.add_new_item'))

# add a new product not from db to seller's inventory
@bp.route('/inventory/add-product/new', methods=['POST'])
def add_new_product_to_inventory():
    """
    functionality to add a new product to the seller's inventory
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    max_pid = Product.get_largest_pid()
    max_pid += 1
    image = request.files['image']
    image.save(os.path.join(os.getcwd() + '/app/static/images', f'{max_pid}.jpg'))
    product_name = str(request.form['product_name'])
    quantity = str(request.form['quantity'])
    unit_price = str(request.form['unit_price'])
    description = str(request.form['description'])
    category = str(request.form['category'])
    cid = Category.get_cid_by_name(category)

    # check if product name already exists in products and inventory
    pid = Product.get_by_name(product_name)
    if pid != None and Inventory.does_product_exist_in_inventory(pid, current_user.id):
        flash(f'{product_name} is an existing product in your inventory.', 'error')
        return redirect(url_for('inventory.inventory_items'))
    # check if product name already exists in products
    elif pid != None:
        flash(f'{product_name} is an existing product. Please try again on this page.', 'error')
        return redirect(url_for('inventory.add_product_item'))
    
    elif Product.add_item(cid, current_user.id, product_name, description, f'{max_pid}.jpg') and Inventory.add_item(max_pid, current_user.id, unit_price, quantity):
        # on the first time a user is a seller, update is_seller to True
        if User.get(current_user.id).is_seller == False:
            User.update_is_seller(current_user.id)
        return redirect(url_for('inventory.inventory_items'))
