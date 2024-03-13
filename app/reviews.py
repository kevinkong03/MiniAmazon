from flask import current_app as app
from flask import render_template, request, redirect, url_for,Blueprint, flash, jsonify
from flask_login import current_user
from flask_paginate import Pagination
from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms import SelectField

from .models.reviews import Review
from .models.reviews import SellerReview
from .models.user import User
from .models.product import Product
from .models.order import OrderItem

bp = Blueprint('reviews', __name__)

class KForm(FlaskForm):
    sortBy = SelectField('Sort By', choices=[('upvotes', 'Upvotes'), ('time', 'Time')])

@bp.route('/reviews/<uid>', methods=['GET', 'POST'])
def reviews(uid):
    """
    Display public view of a user, including reviews for products and sellers
    """
    sort = request.args.get('sortBy', type=str, default='time')
    uid = int(uid)
    if current_user.is_authenticated:
        current_uid = int(current_user.id)
    else:
        current_uid = None

    form = KForm(request.form)
    form.process()

    if request.args.get('sortBy') is not None:
        form.sortBy.data = sort

    if form.validate_on_submit():
        sort = form.sortBy.data

    # Set the page, per_page, and total pages for pagination
    product_page = request.args.get('product_page', type=int, default=1)
    seller_page = request.args.get('seller_page', type=int, default=1)
    my_product_page = request.args.get('my_product_page', type=int, default=1)
    my_page = request.args.get('my_page', type=int, default=1)
    per_page = 5  # 5 reviews per page

    # Calculate the offset 
    product_offset = (product_page - 1) * per_page
    seller_offset = (seller_page - 1) * per_page
    my_product_offset = (my_product_page - 1) * per_page
    my_offset = (my_page - 1) * per_page

    # Set the uid to the current user's id if the uid is -1
    uid = uid if uid != -1 else current_user.id

    # check if the reviews are for the current user
    personal = True if uid == current_uid else False 


    seller_rated_before = False
    purchased_from_seller_before = False
    if current_user.is_authenticated and current_user.id != uid:
        # Assuming you have a method to check if the current user has rated the specified user
        # product_rated_before = Review.have_rated_before(pid, current_user.id)
        purchased_from_seller_before = True if OrderItem.get_items_by_buyer_and_seller(current_user.id, uid) else False
        seller_reviews = SellerReview.have_rated_before(uid,current_user.id)
        
        if seller_reviews:  # This checks if seller_reviews is not None and not an empty list
            seller_rated_before = True

    # average ratings
    purchase_average_rating = Review.average_rating(uid)
    seller_average_rating = SellerReview.average_rating(uid)
    my_average_rating = Review.average_rating_by_seller(uid)
    product_average_rating = SellerReview.average_rating_by_seller(uid)

    # gather reviews with pagination
    ProductTotal = Review.get_total_reviews_by_user(uid)
    MyProductTotal = Review.get_total_reviews_by_seller(uid)
    SellerTotal = SellerReview.get_total_reviews_by_user(uid)
    MyTotal = SellerReview.get_total_reviews_by_seller(uid)
    if sort == 'time':
        ProductReviews = Review.get_recent_reviews_by_user(uid, product_offset, per_page)
        MyProductReviews = Review.get_recent_reviews_by_seller(uid, my_product_offset, per_page)
        SellerReviews = SellerReview.get_recent_reviews_by_user(uid,seller_offset, per_page)
        MyReviews = SellerReview.get_recent_reviews_by_seller(uid, my_offset, per_page)
        user = User.get(uid)

    else:
        ProductReviews = Review.get_top_reviews_by_user(uid, product_offset, per_page)
        MyProductReviews = Review.get_top_reviews_by_seller(uid, my_product_offset, per_page)
        SellerReviews = SellerReview.get_top_reviews_by_user(uid,seller_offset, per_page)
        MyReviews = SellerReview.get_top_reviews_by_seller(uid, my_offset, per_page)
        user = User.get(uid)

    # Create the pagination object within the view function
    ProductPagination = Pagination(page=product_page, per_page=per_page, total=ProductTotal)
    SellerPagination = Pagination(page=seller_page, per_page=per_page, total=SellerTotal)
    MyProductPagination = Pagination(page=my_product_page, per_page=per_page, total=MyProductTotal)
    MyPagination = Pagination(page=my_page, per_page=per_page, total=MyTotal)

    def get_name(seller_id):
        person = User.get(seller_id).firstname + " " + User.get(seller_id).lastname
        return person
    

    return render_template('review.html', avail_product_reviews=ProductReviews, avail_seller_reviews=SellerReviews, 
                                        avail_my_product_reviews=MyProductReviews, 
                                        avail_my_reviews=MyReviews, 
                                        personal=personal, 
                                        user=user, 
                                        ProductPagination=ProductPagination, 
                                        SellerPagination=SellerPagination,
                                        MyProductPagination=MyProductPagination,
                                        MyPagination=MyPagination,
                                        form=form,
                                        purchased_from_seller_before=purchased_from_seller_before,
                                        seller_rated_before=seller_rated_before,
                                        purchase_average_rating=purchase_average_rating,
                                        seller_average_rating=seller_average_rating,
                                        my_average_rating=my_average_rating,
                                        product_average_rating=product_average_rating,
                                        get_name=get_name)
   

@bp.route('/update_upvote', methods=['POST'])
def update_upvote():
    """
    Update the upvote count for a product review
    """
    data = request.json
    uid = data.get('uid')
    pname = data.get('pname')
    upvoteCount = int(data.get('upvoteCount'))

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    if pname is not None:

        updated_upvoteCount = Review.update_upvote(
            uid=uid,
            pname=pname,
            upvote_count=upvoteCount
        )

        if updated_upvoteCount:
            # Redirect to a success page or back to the review page
            flash('Upvote successful')
        else:
            flash('Upvote unsuccessful. Please try again later.')
        return redirect(url_for('reviews.reviews', uid=current_user.id))
    else:
        # Handle the case where required fields are empty
        flash('One or more required fields are empty', 'error')

    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))



@bp.route('/update_seller_upvote', methods=['POST'])
def update_seller_upvote():
    """
    Update the upvote count for a seller review
    """
    data = request.json  # Retrieve JSON data from the request
    seller_name = data.get('pname')
    uid = data.get('uid')
    upvoteCount = int(data.get('upvoteCount'))

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    if seller_name is not None:

        if seller_name:  # Check if the required fields are not empty
            updated_upvoteCount = SellerReview.update_upvote(
                uid=uid,
                seller_name=seller_name,
                upvote_count=upvoteCount
            )
            if updated_upvoteCount:
                # Redirect to a success page or back to the review page
                flash('Upvote successful')
            else:
                flash('Upvote unsuccessful. Please try again later.')
            return redirect(url_for('reviews.reviews', uid=current_user.id))
        else:
            flash('One or more required fields are empty', 'error')
            return redirect(url_for('reviews.reviews', uid=current_user.id))

    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))

