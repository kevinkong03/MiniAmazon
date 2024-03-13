from flask import render_template, request, flash
from flask_login import current_user
from flask_paginate import Pagination
import datetime
from humanize import naturaltime

from .models.product import Product
from .models.wishlist import WishlistItem
from .models.inventory import Inventory
from .models.user import User

from flask import Blueprint
from flask import jsonify
from flask import redirect, url_for 

bp = Blueprint('wishlist', __name__)

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)


@bp.route('/wishlist/<int:uid>')
def wishlist(uid):
    
    # Set the page, per_page, and total pages for pagination
    page = request.args.get('page', type=int, default=1)
    per_page = 10  # 10 reviews per page

    # Calculate the offset 
    offset = (page - 1) * per_page
    # Check if the user is authenticated

    wishlistitems = []
    
    # gathering all wishlist items for specfic user
    wishlistitems = WishlistItem.get_by_user(uid, offset, per_page)
    total = WishlistItem.get_total_by_user(uid)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # getting user's name
    name_parts = User.get_name(uid)
    name_parts = [list(part)[0] for part in name_parts]
    fullname = ' '.join(name_parts)

    # rendering
    return render_template('wishlist.html',
                        items=wishlistitems,
                        pagination=pagination,
                        humanize_time=humanize_time,
                        name=fullname,
                        wishlistuid=uid)
                        

    
@bp.route('/wishlist/add/<int:pid>', methods=['POST'])
def wishlist_add(pid):
    """ 
    adds items into the user's wishlist
    :param pid: product id
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    # adds item to wishlist
    if WishlistItem.add_wishlist(current_user.id, pid):
        flash('Item added successfully!')
    else:
        flash('Item already in wishlist!', 'error')
    return redirect(request.referrer)

@bp.route('/wishlist/delete/<int:pid>/<int:uid>', methods=['POST'])
def wishlist_delete(pid, uid):
    """ 
    deletes items from the user's wishlist
    :param pid: product id
    :param uid: user id
    """

    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    # delete specific item from wishlist
    if WishlistItem.delete_item(uid, pid):
        flash('Item deleted successfully!')
    else:
        flash('Unable to delete', 'error')
    return redirect(request.referrer)

@bp.route('/wishlist/delete_all/<int:uid>', methods=['POST'])
def wishlist_delete_all(uid):
    """ 
    clears all items from the user's wishlist
    :param uid: user id
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
        
    # clearing an entire wishlist for a specified used
    WishlistItem.delete_all(uid)
    return redirect(url_for('wishlist.wishlist', uid=uid))