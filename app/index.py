from flask import render_template, request, flash, redirect
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, BooleanField, StringField, FloatField
from wtforms.validators import DataRequired
from flask_paginate import Pagination
import random


from .models.product import Product
from .models.purchase import Purchase
from .models.inventory import Inventory
from .models.category import Category

from flask import Blueprint
bp = Blueprint('index', __name__)




class KForm(FlaskForm):
    # input form to specify sorting and filtering parameters
    pageSize = IntegerField('Top k Products by Price:')
    sortBy = SelectField('Sort By', choices=[('price', 'Price'), ('category', 'Category'), ('name', 'Name')])
    categoryType = SelectField('category', choices=[('All', 'All'),('league', 'league')])
    available = BooleanField('available products')
    minPrice = FloatField('minPrice',default=0.00)
    maxPrice = FloatField('maxPrice',default=1000000.00)
    keyWord = StringField('keyWord', default='')
    sellerName = StringField('sellerName', default='')
    minRating = IntegerField('minRating', default=0)

@bp.route('/', methods=['GET', 'POST'])
def index():
    # getting previous values to carry over between page refreshes
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('pageSize', type=int, default=20) # 5 items per page
    sort = request.args.get('sortBy', type=str, default='price')
    cat = request.args.get('categoryType', type=str, default='All')
    avail = request.args.get('available', type=bool, default=False)
    minPrice = request.args.get('minPrice', type=float, default=0.00)
    maxPrice = request.args.get('maxPrice', type=float, default=1000000.00)
    keyWord = request.args.get('keyWord', type=str, default='')
    sellerName = request.args.get('sellerName', type=str, default='')
    minRating = request.args.get('minRating', type=int, default=0)

    # getting a list of categories to put in the dropdown
    allcategories = Category.get_all()
    categorylist = [('All', 'All')]
    categorylist.extend([(category.name, category.name) for category in allcategories])
    form = KForm(request.form)
    form.categoryType.choices = categorylist
    form.process()

    # Calculate the offset 
    offset = (page - 1) * per_page


    # updating values in the forms, making sure the value stays consistent
    if request.args.get('pageSize') is not None:
        form.pageSize.data = per_page
    if request.args.get('sortBy') is not None:
        form.sortBy.data = sort
    if request.args.get('categoryType') is not None:
        form.categoryType.data = cat
    if request.args.get('available') is not None:
        form.available.data = avail
    if request.args.get('minPrice') is not None:
        form.minPrice.data = minPrice
    if request.args.get('maxPrice') is not None:
        form.maxPrice.data = maxPrice
    if request.args.get('keyWord') is not None:
        form.keyWord.data = keyWord
    if request.args.get('sellerName') is not None:
        form.sellerName.data = sellerName
    if request.args.get('minRating') is not None:
        form.minRating.data = minRating

    # if the form is submitted, then update the values
    if form.validate_on_submit():
        per_page = form.pageSize.data
        sort = form.sortBy.data
        cat = form.categoryType.data
        avail = form.available.data
        minPrice = form.minPrice.data
        maxPrice = form.maxPrice.data
        keyWord = form.keyWord.data
        sellerName = form.sellerName.data
        minRating = form.minRating.data


    # get the first and last name of the seller for filtering later
    firstName=''
    lastName=''
 

    if sellerName != '':
        if len(sellerName.split(" ")) != 2:
            flash(f'Invalid seller name length', 'error')
            return redirect(request.referrer)
        firstName = sellerName.split(" ")[0]
        lastName = sellerName.split(" ")[1]

    # verify that prices are valid (minimum price < maximum price)
    if minPrice > maxPrice:
        flash(f'Minimum Price should not exceed Maximum Price', 'error')
        return redirect(request.referrer)
    
    # get the list of products given the filtering and sorting parameters
    items = Product.get_all_product_list(sort, cat, offset, per_page, str(avail), minPrice, maxPrice, keyWord.lower(), firstName.lower(), lastName.lower(), None, minRating)

    # get a list of sellers for the dropdown
    sellers = Inventory.get_all_sellers()
    
    # get the children category objects
    if cat != 'All':
        parent = Category.get_by_name(cat)
        children = Category.get_all_children(parent.cid)
        # for child in children:
        #     items.extend(Inventory.get_all_product_list(sort, child.name, offset, per_page))


    # filtering to get products that are available with an image
    available_items_with_image = [item for item in items if item.available and item.image!='unavailableImage.jpeg']

    # Select three random products
    random_products = random.sample(available_items_with_image, min(3, len(available_items_with_image)))

    # get total number of products, set up pagination
    total = Product.get_total_products(cat,avail, minPrice, maxPrice, keyWord.lower(), firstName.lower(), lastName.lower(), minRating)
    pagination = Pagination(page=page, per_page=per_page, total=total)
    categories = Category.get_all()
    return render_template('index.html', 
                           products=items, 
                           form=form, 
                           total=total, 
                           pagination=pagination,
                           categories=categories,
                           sellers=sellers,
                           random_products=random_products)
    






