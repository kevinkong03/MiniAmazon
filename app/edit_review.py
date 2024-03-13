from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from .models.reviews import Review
from .models.reviews import SellerReview
from .models.user import User
from flask import Blueprint
from .models.product import Product

bp = Blueprint('edit_review', __name__)

@bp.route('/edit_review/<int:pid>/<int:uid>', methods=['GET', 'POST'])
def edit_review(pid, uid):
    """
    Edit reviews for a seller
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
    
    pname = Product.get(pid).name
    pid = int(pid)
    uid = int(uid)
    
    if current_user.is_authenticated:
        user = User.get(current_user.id)
    else:
        name = None
    personal = True

    review=Review.get_review(pid,uid)

    return render_template('edit_review.html', personal=personal, user=user, pid=pid,pname=pname,review=review)

@bp.route('/update_product_review/<int:pid>/<int:uid>', methods=['POST'])
def update_product_review(pid, uid):
    """
    Update a review for a product
    """
    pid = int(pid)
    uid = int(uid)

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'POST':
        # Update to match the updated field name in the template
        if pid is not None:
            rating = request.form['rating']
            title = request.form['reviewTitle']
            message = request.form['reviewContent']
            if rating and title and message:  # Check if the required fields are not empty
                updated_review = Review.update_review(
                    buyer_id=current_user.id,
                    pid=pid,
                    title=title,
                    rating=rating,
                    message=message
                )

                if updated_review:
                    # Redirect to a success page or back to the review page
                    flash('Review updated successfully')
                else:
                    flash('Review update failed. Please try again later.', 'error')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
            else:
                flash('One or more required fields are empty', 'error')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
    
    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))

@bp.route('/delete_product_review/<int:pid>/<int:uid>', methods=['GET','POST'])
def delete_product_review(pid, uid):
    """
    Delete a review for a product
    """
    pid = int(pid)
    uid = int(uid)
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'GET':
        if pid is not None:
            deleted_review = Review.delete_review(
                buyer_id=current_user.id,
                pid=pid
                )

            if deleted_review:
                # Redirect to a success page or back to the review page
                flash('Review deleted successfully')
            else:
                flash('Review delete failed. Please try again later.', 'error')
            return redirect(url_for('reviews.reviews', uid=current_user.id))
        else:
            flash('One or more required fields are empty', 'error')
            return redirect(url_for('reviews.reviews', uid=current_user.id))
    
    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))

