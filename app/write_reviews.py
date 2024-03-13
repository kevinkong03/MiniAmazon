from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from .models.reviews import Review
from .models.user import User
from .models.reviews import SellerReview  # Import SellerReview model
from flask import Blueprint

bp = Blueprint('write_reviews', __name__)

@bp.route('/write_reviews/<uid>')
def write_reviews(uid):
    """
    Write reviews for a seller
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
    
    uid = int(uid)
    user, name, sellerList = None, None, None
    if current_user.is_authenticated:
        user = User.get(current_user.id)
        seller_name = User.get(uid).firstname + " " + User.get(uid).lastname
    personal = True
    return render_template('write_reviews.html', uid=uid,personal=personal, user=user, seller_name=seller_name)


@bp.route('/submit_review/<int:uid>', methods=['POST'])
def submit_review(uid):
    """
    Submit a review for a seller
    """
    uid=int(uid)

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'POST':
        rating = request.form['rating']
        title = request.form['reviewTitle']
        message = request.form['reviewContent']
        
        if uid is not None:
            added_review = SellerReview.add_review(
                buyer_id=current_user.id,
                seller_id=uid,  # Use the selected seller ID
                title=title,
                rating=rating,
                message=message
            )

            if added_review:
                # Redirect to a success page or back to the review page
                flash('Review added successfully')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
            else:
                flash('Review add failed. Please try again later.', 'error')
                return redirect(url_for('reviews.reviews', uid=current_user.id))
    
    flash('Invalid request', 'error')
    return redirect(url_for('reviews.reviews', uid=current_user.id))

