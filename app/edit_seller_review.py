from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from .models.reviews import Review
from .models.reviews import SellerReview
from .models.user import User
from flask import Blueprint

bp = Blueprint('edit_seller_review', __name__)

@bp.route('/edit_seller_review/<int:seller_id>/<int:uid>', methods=['GET', 'POST'])
def edit_seller_review(seller_id,uid):
    """
    Edit reviews for a seller
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
    
    seller_id = int(seller_id)
    uid = int(uid)
    seller_name = User.get(seller_id).firstname + " " + User.get(seller_id).lastname
  
    if current_user.is_authenticated:
        user = User.get(current_user.id)
    else:
        seller_name = None
    personal = True
    
    review=SellerReview.get_review(seller_id,uid)
    return render_template('edit_seller_review.html', personal=personal, user=user, seller_name=seller_name, seller_id=seller_id,review=review)

@bp.route('/update_seller_review/<int:seller_id>/<int:uid>', methods=['POST'])
def update_seller_review(seller_id, uid):
    """
    Update a review for a seller
    """
    seller_id = int(seller_id)
    
    uid = int(uid)
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'POST':
        # Update to match the updated field name in the template
        if seller_id is not None:
            rating = request.form['rating']
            title = request.form['reviewTitle']
            message = request.form['reviewContent']
            if rating and title and message:  # Check if the required fields are not empty
                updated_review = SellerReview.update_review(
                    seller_id=seller_id,
                    buyer_id=uid,
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

@bp.route('/delete_seller_review/<int:seller_id>/<int:uid>', methods=['GET','POST'])
def delete_seller_review(seller_id, uid):
    """
    Delete a review for a seller
    """
    seller_id = int(seller_id)
    uid = int(uid)
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))  # Redirect to the login page if the user is not authenticated

    if request.method == 'GET':
        if seller_id is not None:
            deleted_review = SellerReview.delete_review(
                buyer_id=current_user.id,
                seller_id=seller_id
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