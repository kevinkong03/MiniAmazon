from flask import render_template, request, flash
from flask_login import current_user
from flask_paginate import Pagination, get_page_parameter
from flask_wtf import FlaskForm

from .models.product import Product
from .models.inventory import Inventory
from .models.category import Category
from .models.reviews import Review
from .models.user import User

from flask import Blueprint
bp = Blueprint('productView', __name__)

@bp.route('/productView/<int:pid>')
def productView(pid):
    # Set the page, per_page, and total pages for pagination
    sellers_page = request.args.get('sellers_page', 1, type=int)
    reviews_page = request.args.get('reviews_page', 1, type=int)
    reviews_per_page = 3  # 3 reviews per page
    sellers_per_page = 5 # 5 sellers per page

    # Calculate the offset 
    sellers_offset = (sellers_page - 1) * sellers_per_page
    reviews_offset = (reviews_page - 1) * reviews_per_page
    
    user = None 

    # ensure that user is authenticated to add to cart
    if current_user.is_authenticated:
        current_uid = int(current_user.id)
        user= User.get(current_user.id)
    else:
        current_uid = None
    
    # gather product information
    product = Product.get(pid)
    # gather categories
    categories = Category.get_all_parents(product.cid)
    categories.extend(Category.get_by_cid(product.cid))
    
    # gather sellers with pagination
    total_sellers = Inventory.get_total_sellers(pid)
    sellers = Inventory.get_by_product(pid, sellers_offset, sellers_per_page)
    sellers_pagination = Pagination(sellers_page=sellers_page, per_page=sellers_per_page, total=total_sellers, page_parameter='sellers_page')
    # gather reviews with pagination
    total_reviews = Review.get_total_reviews_by_product(pid)
    reviews_for_product = Review.get_all_review_for_product(pid, reviews_offset, reviews_per_page)
    reviews_pagination = Pagination(reviews_page=reviews_page, per_page=reviews_per_page, total=total_reviews, page_parameter='reviews_page')

    
    product_rated_before = False
    if current_user.is_authenticated :
            # Assuming you have a method to check if the current user has rated the specified user
            product_rating = Review.have_rated_before(pid, current_user.id)
            if product_rating:
                product_rated_before= True

    def get_name(uid):
        person = User.get(uid).firstname + " " + User.get(uid).lastname
        return person

    return render_template('productView.html', 
                           user=user,
                           product=product, 
                           categories=categories, 
                           reviews=reviews_for_product,
                           sellers=sellers,
                           product_rated_before=product_rated_before,
                           next=request.url,
                           sellers_pagination=sellers_pagination,
                           reviews_pagination=reviews_pagination,
                           get_name=get_name)
