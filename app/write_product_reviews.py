from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from .models.reviews import Review
from .models.reviews import SellerReview
from .models.user import User
from .models.product import Product
from flask import Blueprint

bp = Blueprint('write_product_reviews', __name__)

@bp.route('/write_product_reviews/<pid>/<uid>')
def write_product_reviews(pid,uid):
    """
    Write reviews for a product
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
        
    uid = int(uid)
    pid = int(pid)
    pname = Product.get(pid).name
    if current_user.is_authenticated:
        user = User.get(current_user.id)
    else:
        name = None
    personal = True
    
    return render_template('write_product_reviews.html', personal=personal, user=user, pname=pname, pid=pid)

@bp.route('/submit_product_review', methods=['POST'])
def submit_product_review():
    """
    Submit a review for a product
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'POST':
        pid = request.form.get('product_id')  # Update to match the updated field name in the template
        if pid is not None:
            pid = int(pid)
            rating = request.form['rating']
            title = request.form['reviewTitle']
            message = request.form['reviewContent']
            review_type = 'ProductReviews'

            if rating and title and message:  # Check if the required fields are not empty
                added_review = Review.add_review(
                    buyer_id=current_user.id,
                    pid=pid,
                    title=title,
                    rating=rating,
                    message=message,
                    review_type = review_type
                )

                if added_review:
                    # Redirect to a success page or back to the review page
                    flash('Review added successfully')
                else:
                    flash('Review add failed. Please try again later.', 'error')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
            else:
                flash('One or more required fields are empty', 'error')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
    
    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))
