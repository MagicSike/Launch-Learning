# Flask libraries
from itertools import product
import json
from math import prod
import numbers
from pickle import FALSE, TRUE
from re import A
from sre_constants import SUCCESS
from flask import Flask, make_response, redirect, render_template, request, flash, jsonify, url_for, session
from flask import g, Response, send_from_directory

import datetime
from flask_mail import Mail, Message
from password_strength import PasswordStats
import random
from password_strength import PasswordPolicy
import pandas as pd
import os
from werkzeug.utils import secure_filename

# database libraries
import sqlite3
import forms
import db_api as db_ops

# machine learning
import ml as model

# Run configurations for Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')
mail = Mail(app)

# Run configurations for Password requirements
policy = PasswordPolicy.from_names(
    length = 3,         # minimum password length = 3
    uppercase = 1,      # need minimum 1 uppercase
    numbers = 1,        # need minimum 1 number
    special = 1,        # need minimum 1 special character
    strength = 0.66     # password must score at least 0.66 to pass
)


####################### Database Connection BLOCK START #######################
def get_db_connection(): # gets a cursor for db operations
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext # destroys each connection after usage
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        print('database is closed')
        db.close()
####################### Database Connection BLOCK END #######################

@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html', title='Keyboard Tech Guides', login=session.get('user'))

####################### Switch Tester BLOCK START #######################

@app.route("/switchtester")
def switchtester():
    return render_template('switchtester.html',  title='Switch Tester - KTG', login=session.get('user'))

@app.route("/switchtesterviewall")
def switchtesterviewall():
    return render_template('switchtesterviewall.html', title='Switch Tester - KTG', login=session.get('user'))

####################### Switch Tester BLOCK END #######################    

####################### BROWSE BLOCK START #######################
@app.route('/display_image/<int:filename>', methods=['POST', 'GET'])
def display_image(filename):
    #print('display_image filename: ' + filename)
    filename_ext = str(filename) + '.jpg'

    #print(filename_ext)
    #return redirect(url_for('static', filename='upload_folder/' + str(filename) + '.jpg'))
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename_ext)


@app.route("/browse/", methods=['POST', 'GET'])
@app.route("/browse", methods=['POST', 'GET'])
def browse():
    #get initial x number of data for page 1
    conn = get_db_connection()
    query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_id ASC LIMIT 15'
    datas = db_ops.select_query(conn, query)        

    # get page_links
    query = 'SELECT COUNT(*) from PRODUCTS'
    total = db_ops.select_query(conn, query, one=True)    

     # links to other pages 
    page_links = calculate_page_links(total[0], '', 1)
    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    # default for filter_type = "date_asc"
    return render_template('browse.html', 
                            title='Browse Product - KTG', 
                            datas=datas, 
                            previous_page='#',
                            page_links=page_links, 
                            browse=-1,
                            keyboard_type=0,
                            next_page=url_for('browse_page', page_number=2, filter_type='date_asc'), 
                            total_pages=total_pages,
                            login=session.get('user'))

@app.route("/browse/<filter_type>/", methods=['POST', 'GET'])
@app.route("/browse/<filter_type>", methods=['POST', 'GET'])
def filter(filter_type):
    conn = get_db_connection()
    
    # get the filtered data from database else if will sort by oldest date added
    query = filter_type_products(filter_type, 15)
    datas = db_ops.select_query(conn, query)

    # get page_links
    query = 'SELECT COUNT(*) from PRODUCTS'
    total = db_ops.select_query(conn, query, one=True)    

     # links to other pages 
    page_links = calculate_page_links(total[0], filter_type, 1)
    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    return render_template('browse.html', 
                            title='Browse Product - KTG', 
                            datas=datas, 
                            previous_page='#', 
                            next_page=url_for('browse_page', page_number=2, filter_type=filter_type), 
                            page_links=page_links,
                            browse=-1,
                            keyboard_type=0,
                            total_pages=total_pages,
                            login=session.get('user'))

@app.route("/browse/p/<int:page_number>/", defaults={'filter_type':''},  methods=['POST', 'GET'])
@app.route("/browse/p/<int:page_number>", defaults={'filter_type':''},  methods=['POST', 'GET'])
@app.route("/browse/p/<int:page_number>/<filter_type>",  methods=['POST', 'GET'])
@app.route("/browse/p/<int:page_number>/<filter_type>/",  methods=['POST', 'GET']) # try <int: page_number> to replace p_page = int(page_number) - 1
def browse_page(page_number, filter_type):
    
    if page_number < 2: # first page link, checks to make sure negative numbers are handle
        if filter_type == '':
            return redirect(url_for('browse'))
        else:
            return redirect(url_for('filter', filter_type=filter_type))    
    
    query = filter_type_products(filter_type, -1)

    conn = get_db_connection()
    products = db_ops.select_query(conn, query)

    # get total number of products in database
    query = 'SELECT COUNT(*) from PRODUCTS'
    total = db_ops.select_query(conn, query, one=True)

    # get the x number of data for page # -- if x = 15, page 2 ---> items from 15 to 30
    # get next 15 data if filter is specified
    product_selection = []
    product_index = (page_number * 15) - 15
    for i in range(0, 15):
        if (product_index + i) < total[0]: # make sure range is not out of bound
            product_selection.append(products[product_index + i])
        else:
            break

    # previous and next page 
    p_page = page_number - 1
    n_page = page_number + 1
    
    # check that page_number does not exceed limit 
    high_index = page_number * 15
    if total[0] <= high_index:
        next_page = '#'
    else:
        next_page = url_for('browse_page', page_number=n_page, filter_type=filter_type)

    # links to other pages 
    page_links = calculate_page_links(total[0], filter_type, page_number)

    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    return render_template('browse_category.html', 
                    title='Browse Product - KTG', 
                    previous_page=url_for('browse_page', page_number=p_page, filter_type=filter_type), 
                    next_page=next_page, 
                    page_links=page_links,
                    browse=-1,
                    keyboard_type=0,
                    product_selection=product_selection, 
                    total_pages=total_pages,
                    login=session.get('user'))

@app.route("/browse/c/<product_category>/", methods=['POST', 'GET'])
@app.route("/browse/c/<product_category>", methods=['POST', 'GET'])
def category(product_category):
    category_selected = product_category.upper()
    
    # default case returns to browse
    if category_selected not in ('CASES', 'PCB', 'SWITCHES', 'KEYCAPS', 'PLATES', 'KEYBOARDS'):
        return redirect(url_for('browse'))

    # run database search for category's products and info such as price and name
    conn = get_db_connection()
    query = f'SELECT product_name, product_price, product_id from PRODUCTS WHERE product_type LIKE \'{product_category}\' ORDER BY product_id ASC LIMIT 15'
    products = db_ops.select_query(conn, query)

    # get page_links
    query = f'SELECT COUNT(*) from PRODUCTS WHERE product_type LIKE \'{product_category}\''
    total = db_ops.select_query(conn, query, one=True)    

     # links to other pages 
    page_links = calculate_page_links_category(total[0], '', 1, product_category)
    
    keyboard_type = 0
    if category_selected == 'KEYBOARDS':
        keyboard_type = 1

    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    return render_template('browse_category.html', 
                title=product_category, 
                previous_page='#',
                next_page=url_for('category_page', product_category=product_category, page_number=2, filter_type='date_asc'),
                page_links=page_links,
                browse=1,
                keyboard_type=keyboard_type,
                product_selection=products, 
                total_pages=total_pages,
                login=session.get('user'))


@app.route("/browse/c/<product_category>/<filter_type>/", methods=['POST', 'GET'])
@app.route("/browse/c/<product_category>/<filter_type>", methods=['POST', 'GET'])
def category_filter(product_category, filter_type):
    
    conn = get_db_connection()
    
    # get the filtered data from database else if will sort by oldest date added
    query = filter_type_category(filter_type, 15, product_category)
    product_selection = db_ops.select_query(conn, query)

    # get total number of products in database
    if filter_type == 'size_small':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                            FROM PRODUCTS as T 
                            WHERE T.product_sizing LIKE \'0.4%\' or T.product_sizing LIKE \'0.2%\' or T.product_sizing = \'Pad\') 
                    ORDER BY product_name ASC"""
    elif filter_type == 'size_medium':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                        FROM PRODUCTS AS T 
                        WHERE T.product_sizing LIKE \'0.6%\' or T.product_sizing = \'0.7\') 
                    ORDER BY product_name ASC"""
    elif filter_type == 'size_full':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                        FROM PRODUCTS AS T 
                        WHERE T.product_sizing LIKE \'0.7_%\' or T.product_sizing LIKE \'0.8%\' 
                            or T.product_sizing LIKE \'0.9%\' or T.product_sizing = \'1800\' or T.product_sizing = \'TKL\')
                    ORDER BY product_name ASC"""    
    else:
        query = f'SELECT COUNT(*) from PRODUCTS WHERE product_type = \'{product_category}\''
    
    total = db_ops.select_query(conn, query, one=True)    

     # links to other pages 
    page_links = calculate_page_links_category(total[0], filter_type, 1, product_category)

    keyboard_type = 0
    if product_category.upper() == 'KEYBOARDS':
        keyboard_type = 1
    
    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    return render_template('browse_category.html', 
                title=product_category, 
                previous_page='#',
                next_page=url_for('category_page', product_category=product_category, page_number=2, filter_type=filter_type),
                page_links=page_links,
                browse=1,
                keyboard_type=keyboard_type,
                product_selection=product_selection, 
                total_pages=total_pages,
                login=session.get('user'))

@app.route("/browse/c/<product_category>/p/<int:page_number>/", defaults={'filter_type':''}, methods=['POST', 'GET'])
@app.route("/browse/c/<product_category>/p/<int:page_number>", defaults={'filter_type':''}, methods=['POST', 'GET'])
@app.route("/browse/c/<product_category>/p/<int:page_number>/<filter_type>/", methods=['POST', 'GET'])
@app.route("/browse/c/<product_category>/p/<int:page_number>/<filter_type>", methods=['POST', 'GET'])
def category_page(product_category, page_number, filter_type):
    if page_number < 2: # first page link, checks to make sure negative numbers are handle
        if filter_type == '':
            return redirect(url_for('category', product_category=product_category))
        else:
            return redirect(url_for('category_filter', product_category=product_category, filter_type=filter_type))    
    
    # get products from filters
    query = filter_type_category(filter_type, -1, product_category)

    conn = get_db_connection()
    products = db_ops.select_query(conn, query)

    # get total number of products in database
    if filter_type == 'size_small':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                            FROM PRODUCTS as T 
                            WHERE T.product_sizing LIKE \'0.4%\' or T.product_sizing LIKE \'0.2%\' or T.product_sizing = \'Pad\') 
                    ORDER BY product_name ASC"""
    elif filter_type == 'size_medium':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                        FROM PRODUCTS AS T 
                        WHERE T.product_sizing LIKE \'0.6%\' or T.product_sizing = \'0.7\') 
                    ORDER BY product_name ASC"""
    elif filter_type == 'size_full':
        query = f"""SELECT COUNT(*)
                    FROM PRODUCTS 
                    WHERE product_type = \'{product_category}\' and product_sizing in 
                        (SELECT product_sizing 
                        FROM PRODUCTS AS T 
                        WHERE T.product_sizing LIKE \'0.7_%\' or T.product_sizing LIKE \'0.8%\' 
                            or T.product_sizing LIKE \'0.9%\' or T.product_sizing = \'1800\' or T.product_sizing = \'TKL\')
                    ORDER BY product_name ASC"""    
    else:
        query = f'SELECT COUNT(*) from PRODUCTS WHERE product_type = \'{product_category}\''
    
    total = db_ops.select_query(conn, query, one=True)
    print(total[0], len(products))

    # get the x number of data for page # -- if x = 15, page 2 ---> items from 15 to 30
    # get next 15 data if filter is specified
    product_selection = []
    product_index = (page_number * 15) - 15
    for i in range(0, 15):
        if (product_index + i) < total[0]: # make sure range is not out of bound
            product_selection.append(products[product_index + i])
        else:
            break

    # previous and next page 
    p_page = page_number - 1
    n_page = page_number + 1
    
    # check that page_number does not exceed limit 
    high_index = page_number * 15
    if total[0] <= high_index:
        next_page = '#'
    else:
        next_page = url_for('category_page', product_category=product_category, page_number=n_page, filter_type=filter_type)

    # links to other pages 
    page_links = calculate_page_links_category(total[0], filter_type, page_number, product_category)    

    keyboard_type = 0
    if product_category.upper() == 'KEYBOARDS':
        keyboard_type = 1

    total_pages = int(total[0] / 15) + (total[0] % 15 > 0)

    return render_template('browse_category.html', 
                title=product_category, 
                previous_page=url_for('category_page', product_category=product_category, page_number=p_page, filter_type=filter_type),
                next_page=next_page,
                page_links=page_links,
                browse=1,
                keyboard_type=keyboard_type,
                product_selection=product_selection, 
                total_pages=total_pages,
                login=session.get('user'))


def calculate_page_links(total, filter_type, page_number):
    total_pages = int(total / 15) + (total % 15 > 0)
    page_links = []
    print(total_pages)
    # goal - eight pages total 
    if page_number <= 7:        
        for page in range(0, 8): # first eight pages
            link = {'number': (page + 1), 'link': url_for('browse_page', page_number=(page + 1), filter_type=filter_type)}
            page_links.append(link)
        link = {'number': total_pages, 'link': url_for('browse_page', page_number=total_pages, filter_type=filter_type)}    
        page_links.append(link)
    elif page_number >= (total_pages - 7): # last eight pages
        link = {'number': 1, 'link': url_for('browse_page', page_number=1, filter_type=filter_type)}    
        page_links.append(link)
        for page in range((total_pages - 8), total_pages):
            link = {'number': (page + 1), 'link': url_for('browse_page', page_number=(page + 1), filter_type=filter_type)}
            page_links.append(link)
    else:
        for page in range(page_number, (page_number + 8)): # pages in between
            link = {'number': (page + 1), 'link': url_for('browse_page', page_number=(page + 1), filter_type=filter_type)}
            page_links.append(link)
        link = {'number': total_pages, 'link': url_for('browse_page', page_number=total_pages, filter_type=filter_type)}    
        page_links.append(link)
        
    return page_links

def calculate_page_links_category(total, filter_type, page_number, category):
    total_pages = int(total / 15) + (total % 15 > 0)
    page_links = []
    # goal - eight pages total 
    if total_pages < 15:      
        for page in range(0, total_pages): # first eight pages
            link = {'number': (page + 1), 'link': url_for('category_page', product_category=category, page_number=(page + 1), filter_type=filter_type)}
            page_links.append(link)
    else:
        if page_number <= 7:        
            for page in range(0, 8): # first eight pages
                link = {'number': (page + 1), 'link': url_for('category_page', product_category=category, page_number=(page + 1), filter_type=filter_type)}
                page_links.append(link)
            link = {'number': total_pages, 'link': url_for('category_page', product_category=category, page_number=total_pages, filter_type=filter_type)}    
            page_links.append(link)
        elif page_number >= (total_pages - 7): # last eight pages
            link = {'number': 1, 'link': url_for('category_page', product_category=category, page_number=1, filter_type=filter_type)}    
            page_links.append(link)
            for page in range((total_pages - 8), total_pages):
                link = {'number': (page + 1), 'link': url_for('category_page', product_category=category, page_number=(page + 1), filter_type=filter_type)}
                page_links.append(link)
        else:
            for page in range(page_number, (page_number + 8)): # pages in between
                link = {'number': (page + 1), 'link': url_for('category_page', product_category=category, page_number=(page + 1), filter_type=filter_type)}
                page_links.append(link)
            link = {'number': total_pages, 'link': url_for('category_page',product_category=category, page_number=total_pages, filter_type=filter_type)}    
            page_links.append(link)        
        
    return page_links    


def filter_type_products(filter_type, row_count):
    if row_count == -1:
        if filter_type == 'date_desc':
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_id DESC'    
        elif filter_type == 'alpha_az':
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_name ASC'
        elif filter_type == 'alpha_za':
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_name DESC'
        elif filter_type == 'price_asc':
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_price ASC'
        elif filter_type == 'price_desc':
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_price DESC'        
        else:
            query = 'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_id ASC'
    else:
        if filter_type == 'date_desc':
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_id DESC LIMIT {row_count}'    
        elif filter_type == 'alpha_az':
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_name ASC LIMIT {row_count}'
        elif filter_type == 'alpha_za':
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_name DESC LIMIT {row_count}'
        elif filter_type == 'price_asc':
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_price ASC LIMIT {row_count}'
        elif filter_type == 'price_desc':
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_price DESC LIMIT {row_count}'        
        else:
            query = f'SELECT product_name, product_price, product_id from PRODUCTS ORDER BY product_id ASC LIMIT {row_count}'
    
    return query

def filter_type_category(filter_type, row_count, category):
    if row_count == -1:
        if filter_type == 'date_desc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_id DESC'    
        elif filter_type == 'alpha_az':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_name ASC'
        elif filter_type == 'alpha_za':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_name DESC'
        elif filter_type == 'price_asc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_price ASC'
        elif filter_type == 'price_desc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_price DESC'
        elif filter_type == 'size_small':
            query = f"""SELECT product_name, product_price, product_id FROM PRODUCTS 
                        WHERE product_type = \'{category}\' and product_sizing in 
                            (SELECT product_sizing 
                                FROM PRODUCTS as T 
                                WHERE T.product_sizing LIKE \'0.4%\' or T.product_sizing LIKE \'0.2%\' or T.product_sizing = \'Pad\') 
                        ORDER BY product_sizing ASC"""
        elif filter_type == 'size_medium':
            query = f"""SELECT product_name, product_price, product_id FROM PRODUCTS 
                        WHERE product_type = \'{category}\' and product_sizing in 
                            (SELECT product_sizing 
                            FROM PRODUCTS AS T 
                            WHERE T.product_sizing LIKE \'0.6%\' or T.product_sizing = \'0.7\') 
                        ORDER BY product_sizing ASC"""
        elif filter_type == 'size_full':
            query = f"""SELECT product_name, product_price, product_id 
                        FROM PRODUCTS 
                        WHERE product_type = \'{category}\' and product_sizing in 
                            (SELECT product_sizing 
                            FROM PRODUCTS AS T 
                            WHERE T.product_sizing LIKE \'0.7_%\' or T.product_sizing LIKE \'0.8%\' 
                                or T.product_sizing LIKE \'0.9%\' or T.product_sizing = \'1800\' or T.product_sizing = \'TKL\')
                        ORDER BY product_sizing ASC"""  
        else:
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_id ASC'
    else:
        if filter_type == 'date_desc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_id DESC LIMIT {row_count}'    
        elif filter_type == 'alpha_az':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_name ASC LIMIT {row_count}'
        elif filter_type == 'alpha_za':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_name DESC LIMIT {row_count}'
        elif filter_type == 'price_asc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_price ASC LIMIT {row_count}'
        elif filter_type == 'price_desc':
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_price DESC LIMIT {row_count}'      
        elif filter_type == 'size_small':
            query = f"""SELECT product_name, product_price, product_id FROM PRODUCTS 
                        WHERE product_type LIKE \'%{category}%\' and product_sizing in 
                            (SELECT product_sizing 
                                FROM PRODUCTS as T 
                                WHERE T.product_sizing LIKE \'0.4%\' or T.product_sizing LIKE \'0.2%\' or T.product_sizing = \'Pad\') 
                        ORDER BY product_sizing ASC LIMIT {row_count}"""
        elif filter_type == 'size_medium':
            query = f"""SELECT product_name, product_price, product_id FROM PRODUCTS 
                        WHERE product_type LIKE \'%{category}%\' and product_sizing in 
                            (SELECT product_sizing 
                            FROM PRODUCTS AS T 
                            WHERE T.product_sizing LIKE \'0.6%\' or T.product_sizing = \'0.7\') 
                        ORDER BY product_sizing ASC LIMIT {row_count}"""
        elif filter_type == 'size_full':
            query = f"""SELECT product_name, product_price, product_id 
                        FROM PRODUCTS 
                        WHERE product_type = \'{category}\' and product_sizing in 
                            (SELECT product_sizing 
                            FROM PRODUCTS AS T 
                            WHERE T.product_sizing LIKE \'0.7_%\' or T.product_sizing LIKE \'0.8%\' 
                                or T.product_sizing LIKE \'0.9%\' or T.product_sizing = \'1800\' or T.product_sizing = \'TKL\')
                        ORDER BY product_sizing ASC LIMIT {row_count}"""    
        else:
            query = f'SELECT product_name, product_price, product_id FROM PRODUCTS WHERE product_type = \'{category}\' ORDER BY product_id ASC LIMIT {row_count}'
    
    return query

####################### BROWSE BLOCK END #######################    

####################### BUILD BLOCK START #######################    
@app.route("/build", methods=['POST', 'GET'])
def build():
    #link = 'key' in html --- url_for('parts', part_name=link) works
    build_section = []
    case_id = session.get('keyboard_case_source')
    pcb_id = session.get('pcb_source')
    plates_id = session.get('plates_source')
    switches_id = session.get('switches_source')
    keycaps_id = session.get('keycaps_source')
    build_section.append(case_id)
    build_section.append(pcb_id)
    build_section.append(plates_id)
    build_section.append(switches_id)
    build_section.append(keycaps_id)

    if session.get('count') is None:
        session['count'] = 0

    count = session.get('count')
    print('count: ', count)

    query_cost_length = len(build_section)
    query = ''
    if count:
        known_product = []
        for i in range(0, query_cost_length):
            if build_section[i] is not None:
                known_product.append(build_section[i])
        
        query = '('
        known_length = len(known_product)
        for i in range(0, known_length):
            if (i + 1) == known_length:
                query = query + str(known_product[i]) + ')'
                break
            query = query + str(known_product[i]) + ', ' 

    # get product details
    total = 0
    conn = get_db_connection()
    if count:
        query = f'SELECT product_price FROM PRODUCTS WHERE product_id in {query}'
        total_price = db_ops.select_query(conn, query)
        
        for price in total_price:
            total = total + price['product_price']
    total = round(total, 2)
    total_string = f"{total:.2f}"

    compability_size = []
    products_detail = []
    for i in range (0, query_cost_length):
        if build_section[i] is not None:
            query = f'SELECT product_name, product_type, product_sizing, product_price FROM PRODUCTS WHERE product_id = {build_section[i]}'
            detail = db_ops.select_query(conn, query, one=True)
            if detail['product_sizing'] != 'Unknown' or detail['product_sizing'] != 'Other':
                if detail['product_type'] in "Cases":
                    compability_size.append({'name': detail['product_type'], 'size': detail['product_sizing'] })
                elif detail['product_type'] in "PCB":
                    compability_size.append({'name': detail['product_type'], 'size': detail['product_sizing'] })
                elif detail['product_type'] in "Plates":
                    compability_size.append({'name': detail['product_type'], 'size': detail['product_sizing'] })

            products_detail.append({'name': detail['product_name'], 'id': build_section[i], 'price': detail['product_price'], 'size': detail['product_sizing']})
        else:
            products_detail.append({'name': None, 'id': build_section[i]})

    comp=None
    if len(compability_size) > 1:
        for check in range (1, len(compability_size)):
            if compability_size[0]['size'] != compability_size[check]['size']:
                comp = f"""{compability_size[0]['name']} and {compability_size[check]['name']}"""
                break


    return render_template('build.html', title='Builder - KTG', login=session.get('user'), products_detail=products_detail, total=total_string, comp=comp)

@app.route("/build/select/<part_name>/",  methods=['POST', 'GET'])
@app.route("/build/select/<part_name>",  methods=['POST', 'GET'])
def select(part_name):
    # make recommendations and get the materials from database
    size_small = None
    size_medium = None
    size_full = None
    low_cost = None
    medium_cost = None
    high_cost = None

    if request.method == "POST":
        size_small = request.form.get('size_small')
        size_medium =request.form.get('size_medium')
        size_full = request.form.get('size_full')
        low_cost = request.form.get('low_cost')
        medium_cost = request.form.get('medium_cost')
        high_cost = request.form.get('high_cost')

    query_conditions_size = []
    # filter conditions for query
    if size_small:
        query_size_small = 'T.product_sizing LIKE \'0.4%\' or T.product_sizing LIKE \'0.2%\' or T.product_sizing = \'Pad\''
        query_conditions_size.append(query_size_small)

    if size_medium:
        query_size_medium = 'T.product_sizing LIKE \'0.6%\' or T.product_sizing = \'0.7\''
        query_conditions_size.append(query_size_medium)

    if size_full:
        query_size_full = 'T.product_sizing LIKE \'0.7_%\' or T.product_sizing LIKE \'0.8%\' or T.product_sizing LIKE \'0.9%\' or T.product_sizing = \'1800\' or T.product_sizing = \'TKL\''
        query_conditions_size.append(query_size_full)

    query_conditions_cost = []
    if low_cost:
        query_low_cost = 'S.product_price BETWEEN 0 and 100'
        query_conditions_cost.append(query_low_cost)

    if medium_cost:
        query_medium_cost = 'S.product_price BETWEEN 101 and 200'
        query_conditions_cost.append(query_medium_cost)
    
    if high_cost:
        query_high_cost = 'S.product_price > 200'
        query_conditions_cost.append(query_high_cost)

    query_size_length = len(query_conditions_size)
    query_cost_length = len(query_conditions_cost)

    query_selections_size = ''
    if query_size_length:
        for i in range(0, query_size_length):
            if (i + 1) == query_size_length:
                query_selections_size = query_selections_size + query_conditions_size[i]
                break
            
            query_selections_size = query_selections_size +  query_conditions_size[i] + ' or '

    query_selections_cost = ''
    if query_cost_length:
        for i in range(0, query_cost_length):
            if (i + 1) == query_cost_length:
                query_selections_cost = query_selections_cost + query_conditions_cost[i]
                break
            
            query_selections_cost = query_selections_cost +  query_conditions_cost[i] + ' or '

    query_selections = ''
    if query_size_length or query_cost_length:
        if query_size_length and query_cost_length:
            query_selections = f'and product_sizing in (SELECT product_sizing FROM PRODUCTS as T WHERE {query_selections_size}) and product_price in (SELECT product_price FROM PRODUCTS as S WHERE {query_selections_cost})'
        elif query_size_length:
            query_selections = f'and product_sizing in (SELECT product_sizing FROM PRODUCTS as T WHERE {query_selections_size})'
        elif query_cost_length:
            query_selections = f'and product_price in (SELECT product_price FROM PRODUCTS as S WHERE {query_selections_cost})'
    
    # recommendations from builds saved or random from top selling
    conn = get_db_connection()
    current_user = session.get('user')
    select_recommendation = None
    if current_user is not None:
        query = f'SELECT * FROM BUILDS WHERE build_user_id = {current_user}'
        user_builds = db_ops.select_query(conn, query)
        user_builds_length = len(user_builds)
        if user_builds_length > 0:
            select_number = random.randint(0, user_builds_length - 1)
            if 'Cases' in part_name:
                select_recommendation = user_builds[select_number]['cases_id']
            if 'PCB' in part_name:
                select_recommendation = user_builds[select_number]['pcb_id']
            if 'Plates' in part_name:
                select_recommendation = user_builds[select_number]['plates_id']
            if 'Switches' in part_name:
                select_recommendation = user_builds[select_number]['switches_id']
            if 'Keycaps' in part_name:
                select_recommendation = user_builds[select_number]['keycaps_id']

    if select_recommendation is None:
        if 'Cases' in part_name:
            query = 'SELECT * FROM PRODUCTS WHERE product_type = \'Cases\' and product_top = 1'
        if 'PCB' in part_name:
            query = 'SELECT * FROM PRODUCTS WHERE product_type = \'PCB\' and product_top = 1'
        if 'Plates' in part_name:
            query = 'SELECT * FROM PRODUCTS WHERE product_type = \'Plates\' and product_top = 1'
        if 'Switches' in part_name:
            query = 'SELECT * FROM PRODUCTS WHERE product_type = \'Switches\' and product_top = 1'
        if 'Keycaps' in part_name:
            query = 'SELECT * FROM PRODUCTS WHERE product_type = \'Keycaps\' and product_top = 1'

        top_products = db_ops.select_query(conn, query)   
        top_products_length = len(top_products)
        select_top_number = random.randint(0, top_products_length - 1)
        select_recommendation = top_products[select_top_number]['product_id']    


    if 'Cases' in part_name:
        df = pd.read_sql_query("SELECT * FROM PRODUCTS WHERE product_type = \'Cases\'", conn)
        product_recs = model.similar_model(select_recommendation, df)
    if 'PCB' in part_name:
        df = pd.read_sql_query("SELECT * FROM PRODUCTS WHERE product_type = \'PCB\'", conn)
        product_recs = model.similar_model(select_recommendation, df)
    if 'Plates' in part_name:
        df = pd.read_sql_query("SELECT * FROM PRODUCTS WHERE product_type = \'Plates\'", conn)
        product_recs = model.similar_model(select_recommendation, df)
    if 'Switches' in part_name:
        df = pd.read_sql_query("SELECT * FROM PRODUCTS WHERE product_type= \'Switches\'", conn)
        product_recs = model.similar_model(select_recommendation, df)
    if 'Keycaps' in part_name:
        df = pd.read_sql_query("SELECT * FROM PRODUCTS WHERE product_type= \'Keycaps\'", conn)
        product_recs = model.similar_model(select_recommendation, df)

    # get recommendations and the rest of the data for the category
        
    query_condition = f"""({product_recs.iloc[0]}, {product_recs.iloc[1]}, {product_recs.iloc[2]}, {product_recs.iloc[3]}, {product_recs.iloc[4]})"""

    # remembers the recommendations to not be recommended
    query = f"""SELECT product_id, product_name, product_material, product_price, product_mount, product_sizing, product_profile 
                FROM PRODUCTS WHERE product_id in {query_condition} {query_selections}
                ORDER BY product_name ASC"""     
    recommendations = db_ops.select_query(conn, query)

    query = f"""SELECT product_id, product_name, product_material, product_price, product_mount, product_sizing, product_profile 
                FROM PRODUCTS 
                WHERE product_id not in {query_condition} and product_type = \'{part_name}\' {query_selections}
                ORDER BY product_name ASC LIMIT 10"""
    products = db_ops.select_query(conn, query) 

    # remembers the query for all the products
    session['next_product_query'] = f"""SELECT product_id, product_name, product_material, product_price, product_mount, product_sizing, product_profile 
                FROM PRODUCTS 
                WHERE product_id not in {query_condition} and product_type = \'{part_name}\' {query_selections}
                ORDER BY product_name ASC"""

    #get total
    query =  f"""SELECT COUNT(*) FROM PRODUCTS 
                WHERE product_id not in {query_condition} and product_type = \'{part_name}\' {query_selections}
                ORDER BY product_name ASC"""

    # remember the checkboxes made by user
    session['next_page_query'] = query

    total = db_ops.select_query(conn, query, one=True)
    page_links = calculate_page_links_build(total[0], 1, part_name)

    keep_profile = 0
    keep_size = 1
    if 'Switches' in part_name or 'Keycaps' in part_name:
        keep_size = 0
        keep_profile = 1

    total_pages = int(total[0] / 10) + (total[0] % 10 > 0)

    return render_template('build_pick_part.html', 
                            title="Select - KTG", 
                            part_title=part_name, 
                            product_recs=recommendations, 
                            keep_size=keep_size,
                            keep_profile=keep_profile,
                            previous_page='#',
                            next_page=url_for('select_page', part_name=part_name, page_number=2),
                            page_number=1,
                            page_links=page_links, 
                            products=products,
                            total_pages=total_pages,
                            login=session.get('user'))

@app.route("/build/select/<part_name>/p/<int:page_number>/",  methods=['POST', 'GET'])
@app.route("/build/select/<part_name>/p/<int:page_number>",  methods=['POST', 'GET'])
def select_page(part_name, page_number):
    if page_number < 2:
        return redirect(url_for('select', part_name=part_name))
    
    # get products
    conn = get_db_connection()
    query = session.get('next_product_query')
    products = db_ops.select_query(conn, query) 

    #get total
    query = session.get('next_page_query')
    total = db_ops.select_query(conn, query, one=True)

    # get the x number of data for page # -- if x = 15, page 2 ---> items from 15 to 30
    # get next 10 data if filter is specified
    product_selection = []
    product_index = (page_number * 10) - 10
    for i in range(0, 10):
        if (product_index + i) < total[0]: # make sure range is not out of bound
            product_selection.append(products[product_index + i])
        else:
            break

    # previous and next page 
    p_page = page_number - 1
    n_page = page_number + 1
    
    # check that page_number does not exceed limit 
    high_index = page_number * 10
    if total[0] <= high_index:
        next_page = '#'
    else:
        next_page = url_for('select_page', part_name=part_name, page_number=n_page)

    # links to other pages 
    page_links = calculate_page_links_build(total[0], page_number, part_name)

    keep_profile = 0
    keep_size = 1
    if 'Switches' in part_name or 'Keycaps' in part_name:
        keep_size = 0
        keep_profile = 1
    
    total_pages = int(total[0] / 10) + (total[0] % 10 > 0)

    return render_template('build_pick_part.html', 
                            title="Select - KTG", 
                            part_title=part_name, 
                            keep_size=keep_size,
                            keep_profile=keep_profile,
                            previous_page=p_page,
                            next_page=next_page,
                            page_number=page_number,
                            page_links=page_links, 
                            products=product_selection,
                            total_pages=total_pages,
                            login=session.get('user'))


def calculate_page_links_build(total, page_number, category):
    total_pages = int(total / 10) + (total % 10 > 0)
    page_links = []
    # goal - eight pages total 
    if total_pages < 15:      
        for page in range(0, total_pages): # first eight pages
            link = {'number': (page + 1), 'link': url_for('select_page', part_name=category, page_number=(page + 1))}
            page_links.append(link)
    else:
        if page_number <= 7:        
            for page in range(0, 8): # first eight pages
                link = {'number': (page + 1), 'link': url_for('select_page', part_name=category, page_number=(page + 1))}
                page_links.append(link)
            link = {'number': total_pages, 'link': url_for('select_page', part_name=category, page_number=total_pages)}    
            page_links.append(link)
        elif page_number >= (total_pages - 7): # last eight pages
            link = {'number': 1, 'link': url_for('select_page', part_name=category, page_number=1)}    
            page_links.append(link)
            for page in range((total_pages - 8), total_pages):
                link = {'number': (page + 1), 'link': url_for('select_page', part_name=category, page_number=(page + 1))}
                page_links.append(link)
        else:
            for page in range(page_number, (page_number + 8)): # pages in between
                link = {'number': (page + 1), 'link': url_for('select_page', part_name=category, page_number=(page + 1))}
                page_links.append(link)
            link = {'number': total_pages, 'link': url_for('select_page',part_name=category, page_number=total_pages)}    
            page_links.append(link)        
        
    return page_links    


@app.route("/selected_part/<part_type>/<int:part_number>")
def set_build_part(part_type, part_number):
    # check which part was selected by the user and the product id
    if 'Cases' in part_type:
        session['keyboard_case_source'] = part_number
        session['count'] = session['count'] + 1
    
    if 'PCB' in part_type:
        session['pcb_source'] = part_number
        session['count'] = session['count'] + 1
    
    if 'Plates' in part_type:
        session['plates_source'] = part_number
        session['count'] = session['count'] + 1
    
    if 'Switches' in part_type:
        session['switches_source'] = part_number
        session['count'] = session['count'] + 1
    
    if 'Keycaps' in part_type:
        session['keycaps_source'] = part_number
        session['count'] = session['count'] + 1
        
    return redirect(url_for('build'))

@app.route("/build_save", methods=['POST', 'GET'])
def build_save():
    if session.get('count') is not None or session.get('count') == 5 and session.get('user') is not None:
        conn = get_db_connection()
        query = 'SELECT COUNT(*) FROM BUILDS'
        new_build_id = db_ops.select_query(conn, query, one=True)
        new_id = new_build_id[0]
        build_user_id = session.get('user') 
        cases_id = session.get('keyboard_case_source')
        pcb_id = session.get('pcb_source')
        plates_id = session.get('plates_source')
        switches_id = session.get('switches_source')
        keycaps_id = session.get('keycaps_source')

        query = f'INSERT INTO BUILDS VALUES ({new_id}, {build_user_id}, {cases_id}, {pcb_id}, {plates_id}, {switches_id}, {keycaps_id}, 1)' 
        if db_ops.UID_query(conn, query):
            print('Build saved success')

    return redirect(url_for('build'))


@app.route("/build_clear", methods=['POST', 'GET'])
def build_clear():
    session.pop("keyboard_case_source", None) 
    session.pop("pcb_source", None) 
    session.pop("plates_source", None) 
    session.pop("switches_source", None) 
    session.pop("keycaps_source", None) 
    session['count'] = 0
                
    return redirect(url_for('build'))


@app.route("/my_builds", methods=['POST', 'GET'])
def user_builds():
    conn = get_db_connection()
    current_id = session.get('user')
    query = f'SELECT * FROM BUILDS WHERE build_user_id = {current_id} and removed_status=1'
    all_builds = db_ops.select_query(conn, query)
    
    total_count = []
    counter = 1
    for build in all_builds:
        total_count.append(counter)
        counter = counter + 1

    return render_template('builts_saved.html', title='Builds - KTG', all_builds=all_builds, total_count=total_count, login=session.get('user'), zip=zip)

@app.route("/my_builds/remove/<int:build_id>", methods=['POST', 'GET'])
def remove_builder(build_id):
    current_id = session.get('user')
    if current_id == None:
        redirect('login')
        
    query = f'SELECT * FROM BUILDS WHERE build_user_id = {current_id} and build_id = {build_id} and removed_status=1'
    conn = get_db_connection()
    check_status = db_ops.select_query(conn, query)

    if check_status is not None:
        query = f'UPDATE BUILDS SET removed_status=0 WHERE build_id = {build_id}'
        if db_ops.UID_query(conn, query):
            print('Remove Success')
    
    return redirect(url_for('user_builds'))


@app.route("/my_builds/<int:build_id>", methods=['POST', 'GET'])
def add_to_builder(build_id):
    conn = get_db_connection()
    current_id = session.get('user')
    query = f'SELECT * FROM BUILDS WHERE build_user_id = {current_id} and build_id = {build_id} and removed_status=1'
    add_build = db_ops.select_query(conn, query, one=True)

    if add_build is not None:
        session['keyboard_case_source'] = add_build['cases_id']
        session['pcb_source'] = add_build['pcb_id']
        session['plates_source'] = add_build['plates_id']
        session['switches_source'] = add_build['switches_id']
        session['keycaps_source'] = add_build['keycaps_id']
        session['count'] = 5

    return redirect(url_for('build'))
####################### BUILD BLOCK END #######################    

####################### SEARCH BLOCK START #######################

@app.route("/search", methods= ['POST', 'GET'])
def search():
    form = forms.SearchForm()
    if form.validate_on_submit():
        print('Search request') 

        #get data from database 
        conn = get_db_connection()
        query = f'SELECT P.product_name, P.product_price, P.product_type, P.product_id FROM PRODUCTS as P WHERE P.product_name LIKE \'%{form.search.data}%\''
        results = db_ops.select_query(conn, query)

        # number of results
        query = f'SELECT COUNT(*) as N FROM PRODUCTS as P WHERE P.product_name LIKE \'%{form.search.data}%\''
        result_rows = db_ops.select_query(conn, query, one=True)
        result_numbers = result_rows['N']
        return render_template('search.html',  title='Search - KTG', form=form, results=results, result_numbers=result_numbers, login=session.get('user'))
    
    return render_template('search.html',  title='Search - KTG', form=form, result_numbers=-1, login=session.get('user'))

@app.route("/results/<user_input>")
def result(user_input):

    # get data from database
    conn = get_db_connection()
    query = f'SELECT P.product_name FROM PRODUCTS as P WHERE P.product_name LIKE \'%{user_input}%\''
    products = db_ops.select_query(conn, query)

    return render_template('search_results.html',  title=f'{user_input} - Search', login=session.get('user'), products=products)    

####################### SEARCH BLOCK END #######################

####################### PRODUCT PAGE BLOCK START #######################
@app.route("/item/<product_name>", methods=['GET', 'POST'])
def item_page(product_name):
    form = forms.ProductComment()
    # run a database search for the product with product_name/product_id
    conn = get_db_connection()

    #query = f'SELECT product_id, product_type, product_price, product_material, product_sizing, product_link FROM PRODUCTS WHERE product_name = \'{product_name}\''
    query = f'SELECT * FROM PRODUCTS WHERE product_name = \'{product_name}\''
    product_id = db_ops.select_query(conn, query, one=True)

    # insert new comment
    if form.validate_on_submit():
        if session.get('user') is not None: # checks that user is logged in
            query = f'select max(post_id) + 1 from POSTS'
            new_id = db_ops.select_query(conn, query, one=True)
            user_id = session.get('user')

            post_date = datetime.datetime.now()
            post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
            query = f"""INSERT INTO POSTS (post_id, u_id, p_text, type_of_text, p_post_date) 
                        VALUES({new_id[0]}, {user_id}, '{form.comment.data}', 'COMMENT', '{post_date}')"""
            
            if db_ops.UID_query(conn, query):
                query = f"""INSERT INTO COMMENTS VALUES({product_id['product_id']}, {new_id[0]})"""
                db_ops.UID_query(conn, query)
            
            form.comment.data = ""


    # get info about the product such as the tags, materials, and comments to generate the page
    product = {'type':product_id['product_type'], 
            'material':product_id['product_material'], 
            'size': product_id['product_sizing'], 
            'price': product_id['product_price'], 
            'color': product_id['product_color'],
            'brand': product_id['product_brand'],
            'mount': product_id['product_mount'],
            'switch_type': product_id['product_switch_type'],
            'hsf': product_id['product_hsf']
            }

    # get comments
    query = f"""SELECT U.users_name, P.p_text, P.type_of_text, P.p_post_date
            from POSTS as P join COMMENTS as C on P.post_id = C.p_id join USERS as U on U.users_id = P.u_id
            where C.pro_id = {product_id['product_id']}
            ORDER BY P.p_post_date DESC"""
    users = db_ops.select_query(conn, query)

    return render_template('item_page.html', 
                        title='Item - KTG', 
                        product_id = product_id['product_id'], 
                        product_name=product_name, 
                        users=users, 
                        product=product,
                        product_link=product_id['product_link'],
                        update_comment = url_for('item_page', product_name=product_name), 
                        form=form, 
                        login=session.get('user'))

@app.route("/item/<int:product_id>", methods=['GET', 'POST'])
def item_number(product_id):
    # run a database search for the product with product_id
    conn = get_db_connection()

    query = f'SELECT product_id, product_name FROM PRODUCTS WHERE product_id = \'{product_id}\''
    product_id = db_ops.select_query(conn, query, one=True)
    if product_id is not None:
        return redirect(url_for('item_page', product_name=product_id['product_name']))
    else:
        return redirect('build')

####################### PRODUCT PAGE BLOCK END #######################

@app.route("/recommendation")
def recommendation():
    # run a recommendation check for the top recommendations
    
    # run a database search to get the product's details (price)

    # construct the html(inculde the page link) 
    # either here or sent the required data to js to build the html
    
    return render_template('recommendation.html', title='Recommendations', login=session.get('user'))

@app.route("/get_data", methods=['POST'])
def get_data():
    # run a recommendation check if needed

    # run database search to get the product's details (price)
    conn = get_db_connection()
    products = db_ops.select_query(conn, 'SELECT product_name, product_id FROM PRODUCTS')

    # construct the html(inculde the page link) 
    # either here or sent the required data to js to build the html
    links = [url_for('item_page', product_name=products[0][0]), 
            url_for('item_page', product_name=products[1][0]), 
            url_for('item_page', product_name=products[2][0]) ]

    html_build = f"""<br> <br> <br> 
    <div class="row"> 
    <div class="col-sm" id="{products[0][1]}"> <a href="{links[0]}"> <img src="/static/images/keyboard4.jpg"> <br> {products[0][0]} </a> </div> 
    <div class="col-sm" id="{products[1][1]}"> <a href="{links[1]}"> <img src="/static/images/keyboard4.jpg"> <br> {products[1][0]} </a> </div> 
    <div class="col-sm" id="{products[2][1]}"> <a href="{links[2]}"> <img src="/static/images/keyboard4.jpg"> <br> {products[2][0]} </a> </div> 
    </div>"""
    res = make_response(jsonify({"name": html_build}), 200)
    return res

####################### PROFILE BLOCK START #######################
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)           

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and session.get('user') is not None:
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = get_db_connection()
            user_id = session.get('user')
            query = f'UPDATE USERS SET profile_pic_name = \'{filename}\' WHERE users_id = {user_id}'
            if db_ops.UID_query(conn, query):
                print("Upload Profile Success")
    
    return redirect(url_for('profile'))


@app.route("/user_profile", methods=['POST', 'GET'])
def profile():
    # make sure that profile returns an error if user is not logged in

    user_form = forms.ProfileChangeName()
    pass_form = forms.ProfileChangePassword()
    email_form = forms.ProfileChangeEmail()
    about_form = forms.ProfileChangDescription()
    user_id = session['user']

    # get info on user
    description = {'name': '', 'about':''}
    conn = get_db_connection()
    query = f'SELECT users_name, profile_description, profile_pic_name, user_email FROM USERS WHERE users_id = {user_id}'
    info = db_ops.select_query(conn, query, one=True)
    description['name'] = info['users_name']
    description['about'] = info['profile_description']
    description['email'] = info['user_email']

    if user_form.validate_on_submit():
        # check if username already exist within the db - will not update if it is
        user_check = check_db(conn, user_form.username.data, 'users_name', 'USERS')

        # check to see if username is unique
        if not user_check:
            query = f'UPDATE USERS SET users_name = \'{user_form.username.data}\' WHERE users_id = {user_id}'
            db_ops.UID_query(conn, query)
        return redirect(url_for('profile'))
    else:
        print('Validation: User_Failure')

    if email_form.validate_on_submit():
        # check if username already exist within the db - will not update if it is
        email_check = check_db(conn, email_form.change_email.data, 'user_email', 'USERS')

        # check to see if username is unique
        if not email_check:
            query = f'UPDATE USERS SET user_email = \'{email_form.change_email.data}\' WHERE users_id = {user_id}'
            db_ops.UID_query(conn, query)
        return redirect(url_for('profile'))
    else:
        print('Validation: Email_Failure')

    if pass_form.validate_on_submit():
        # update password
        stats = PasswordStats(pass_form.password.data)
        if stats.strength() > 0.80:
            query = f'UPDATE USERS SET user_password = \'{pass_form.password.data}\' WHERE users_id = {user_id}'
            db_ops.UID_query(conn, query)
        else:
            print('Password is not strong enough')

        return redirect(url_for('profile'))
    else:
        print('Validation: Password_Failure')    

    if about_form.validate_on_submit():
        # update about
        about_string = f"""{about_form.about.data}"""
        about_string = about_string.replace('\n', '').replace('\r', '')

        query = f'UPDATE USERS SET profile_description = \'{about_string}\' WHERE users_id = {user_id}'
        db_ops.UID_query(conn, query)

        return redirect(url_for('profile'))
    else:
        print('Validation: About_Failure')             
        
    return render_template('profile.html', 
                        title='Profile - KTG',
                        user_form=user_form, 
                        pass_form=pass_form, 
                        email_form=email_form, 
                        about_form=about_form, 
                        description=description, 
                        user_pic=info['profile_pic_name'],
                        login=session.get('user')
                        )
####################### PROFILE BLOCK END #######################

# check against database for a specific string (check_name)
def check_db(connection, check_name, column, table):
    query = f'SELECT {column} FROM {table} WHERE {column} = \'{check_name}\' '
    #print(query)
    db_data = db_ops.select_query(connection, query, one=True)

    run_check = 0
    if db_data is not None: 
        run_check = 1
    #for data in db_data:
        #print(data[column])
        #if data[column] == check_name:
            #run_check = 1
            #break
    return run_check

####################### LOGIN/Register BLOCK START #######################
@app.route("/register", methods=['POST', 'GET'])
def register():
    session.pop("user", None)
    
    form = forms.RegistrationForm()
    username = form.username.data
    password = form.password.data
    email = form.email.data
    print(username)
    print(password)
    print(email)
    error_message = ''
    if request.method == 'POST':
        stats = PasswordStats(password)
        #print(policy.test(password))

        #Checking password requirements
        length = PasswordStats(password).length
        uppercase = PasswordStats(password).letters_uppercase
        numbers = PasswordStats(password).numbers
        special_char = PasswordStats(password).special_characters

        print("Length:", length)
        print("Uppercases:", uppercase)
        print("Numbers:", numbers)
        print("Special Characters:", special_char)

        if uppercase < 1 or numbers < 1 or special_char < 1:
            flash("Password needs at least 1 uppercase letter, 1 number and 1 special character!!")
        if stats.strength() < 0.80:
            print(stats.strength())
            error_message = "Password is not strong enough!"
            flash(error_message) #check if need a redirect/render template
        else:
            print(stats.strength())
            pass
    
    if form.validate_on_submit():
        conn = get_db_connection()
        query1 = 'SELECT MAX(users_id)+1 FROM USERS'
        max_users = db_ops.select_query(conn, query1, one = True)
        query2 = f'INSERT INTO USERS (users_id, users_name, user_password, user_email) VALUES ({max_users[0]}, \'{username}\', \'{password}\', \'{email}\')'
        if stats.strength() > 0.80:
            if db_ops.UID_query(conn, query2): #separate user/email later and make redirect work
                return redirect(url_for('login'))

    return render_template('register.html', title='Register - KTG', form=form, error_message=error_message, login=session.get('user'))


@app.route("/login", methods=['POST', 'GET'])
def login():
    form = forms.LoginForm()
    
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        print(form.validate_on_submit())

        if form.validate_on_submit():
            conn = get_db_connection()
            query = f'select users_id, users_name, user_password from USERS where users_name = \'{username}\' AND user_password = \'{password}\''

            users = db_ops.select_query(conn, query, one = TRUE)

            if users is not None:
                print("Success-login")

                # Configurations for session timer
                session.permanent = True
                app.permanent_session_lifetime = datetime.timedelta(minutes = 3)

                user = users['users_id']
                session['user'] = user
                return redirect(url_for('user'))
            else:
                flash("Incorrect username or password. Please try again.")
                return redirect(url_for('user'))
    
    return render_template('login.html',title='Login - KTG', form=form, login=session.get('user'))    


@app.route("/user")
def user():
    form = forms.LoginForm()
    print(form.validate_on_submit())
    if "user" in session and form.validate_on_submit:
        #user = session["user"]
        #flash('You were successfully logged in', SUCCESS)
        return redirect(url_for('index'))
    else:
        return redirect(url_for("login"))    

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("User logged out", SUCCESS)
    return redirect(url_for("login"))    

####################### LOGIN/Register BLOCK END #######################

####################### FORGOT PASSWORD BLOCK START #######################
@app.route("/forgot", methods=('GET', 'POST'))
def forgot():
    form = forms.ForgotForm()
    username = form.username.data
    email = form.email.data

    if request.method == 'POST':
        conn = get_db_connection()
        query1 = f'select users_name, user_email, users_id from USERS where user_email = \'{email}\' and users_name = \'{username}\''
        users = db_ops.select_query(conn, query1, one = TRUE)
    
        if users is not None:
            # Establishing session for password reset
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes = 15)
            
            user = users['users_name']
            session['user'] = user
            
            # Generating random password code
            forgot_code = random.randint(10000, 99999)
            print(forgot_code)
           
            # Creating code_timer for reset code
            code_timer = datetime.date.today()
            print(code_timer)

            user_id = users['users_id']
            query3 = f'INSERT INTO FORGOT (u_id, forgot_code, code_timer) VALUES ({user_id}, {forgot_code}, \'{code_timer}\')'
            db_ops.UID_query(conn, query3)

            # Creating email message
            msg = Message("Request to reset password", sender='noreply@demo.com', recipients=[email])
            msg.body = f"Your reset code is {forgot_code} ."
            mail.send(msg)
            flash('The reset passcode has been sent to your email.')
            return redirect(url_for('forgot_passcode'))
        else:
            flash('Email or Username does not exist!')
            return redirect(url_for('forgot'))
    
    return render_template('forgot_password.html', form=form)


@app.route("/forgot_passcode", methods = ('GET', 'POST'))
def forgot_passcode():
    form = forms.ForgotCode()
    #username = form.username.data
    password = form.password.data

    if request.method == 'POST':
        conn = get_db_connection()
        today_date = datetime.date.today()
        query2 = f'select u.users_name, f.forgot_code, f.code_timer from FORGOT as f JOIN USERS as u on u.users_id = f.u_id where f.forgot_code = {password} AND f.code_timer = \'{today_date}\''
        users = db_ops.select_query(conn, query2, one = True)
        #print(users['users_name'])

        if users is not None:
            print(users['users_name'])
            return redirect(url_for('reset_password'))
        else:
            flash('Passcode invalid or has expired!')
            return redirect(url_for('forgot_passcode'))
            
    return render_template('forgot_passcode.html', form=form)


@app.route("/reset_password", methods=('GET', 'POST')) #make sure they can't enter link
def reset_password():
    form = forms.ResetForm()
    username = form.username.data
    password = form.password.data

    if request.method == 'POST':
        stats = PasswordStats(password)
        
        length = PasswordStats(password).length
        uppercase = PasswordStats(password).letters_uppercase
        numbers = PasswordStats(password).numbers
        special_char = PasswordStats(password).special_characters

        print("Length:", length)
        print("Uppercases:", uppercase)
        print("Numbers:", numbers)
        print("Special Characters:", special_char)

        if uppercase < 1 or numbers < 1 or special_char < 1:
            flash("Password needs at least 1 uppercase letter, 1 number and 1 special character!!")
        if stats.strength() < 0.66:
            print(stats.strength())
            flash("Password is not strong enough!")
            return redirect(url_for("reset_password"))
        else:
            print(stats.strength())
            pass

        conn = get_db_connection()
        query = f'select users_name from USERS where users_name = \'{username}\''
        users = db_ops.select_query(conn, query, one = TRUE)
        
        if users is not None:
            query2 = f'update USERS set user_password = \'{password}\' where users_name = \'{username}\''
            db_ops.UID_query(conn, query2)
            flash('Password has been reset')
            return redirect(url_for('login'))
        else:
            flash('Username invalid!')
            return redirect(url_for('reset_password'))
            
    return render_template('reset_password.html', form=form)

####################### FORGOT PASSWORD BLOCK END #######################

####################### Community BLOCK END #######################

@app.route("/community", methods=['POST', 'GET'])
def community():
    form = forms.CreatePost()
    upload_form = forms.UploadForm()
    
    # database connection
    conn = get_db_connection()
    user_id = session.get('user')
    # check if new submission was made
    if form.validate_on_submit():
        query = f'SELECT max(post_id) + 1 FROM POSTS'
        new_id = db_ops.select_query(conn, query, one=True)

        get_string = f"""{form.text.data}"""

        post_date = datetime.datetime.now()
        post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
        query = f"""INSERT INTO POSTS VALUES({new_id[0]}, {user_id}, \'{form.title.data}\', \'{get_string}\', \'COMMUNITY\', \'{post_date}\')"""
        if db_ops.UID_query(conn, query):
            print('New post has been inserted')
        form.text.data = ""
        form.title.data = ""
    
    elif upload_form.validate_on_submit():
        filename = secure_filename(upload_form.file.data.filename)
        upload_form.file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        query = f'SELECT max(post_id) + 1 FROM POSTS'
        new_id = db_ops.select_query(conn, query, one=True)

        post_date = datetime.datetime.now()
        post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
        query = f"""INSERT INTO POSTS VALUES({new_id[0]}, {user_id}, \'{upload_form.title.data}\', \'{filename}\', \'COMMUNITY_IMAGE\', \'{post_date}\')"""
        if db_ops.UID_query(conn, query):
            print("Upload Image Success")
        

    # get the name, title, content, profile_link, time_stamp, and check for if image or not from database
    query = f'SELECT post_id, u_id, p_title, p_text, type_of_text, p_post_date FROM POSTS WHERE type_of_text = \'COMMUNITY\' or type_of_text = \'COMMUNITY_IMAGE\' ORDER BY p_post_date DESC'
    post_db = db_ops.select_query(conn, query)
    
    # convert into json_items else if database already store everything, just use the table provided by the database 
    # (remember to switch things like post.name to post['name'] in the html file if you use the table provided by the database)
    # append everything to posts
    posts = []
    
    # append data from database,
    current_post_time = datetime.datetime.now()
    for p in post_db:
        query = f"""SELECT users_name, profile_pic_name FROM USERS WHERE users_id={p['u_id']}"""
        user_name = db_ops.select_query(conn, query, one=True)
        query = f"""SELECT COUNT(*) FROM LIKE_DISLIKE WHERE community_post_id = {p['post_id']} and like_dislike = 1"""

        # caculate total upvotes
        total_likes = db_ops.select_query(conn, query, one=True)
        query = f"""SELECT COUNT(*) FROM LIKE_DISLIKE WHERE community_post_id = {p['post_id']} and like_dislike = 2"""
        total_dislikes = db_ops.select_query(conn, query, one=True)
        total_votes = total_likes[0] - total_dislikes[0]
        if p['type_of_text'] == 'COMMUNITY_IMAGE':
            new_post = generate_json(p['post_id'], 
                                    user_name['users_name'], 
                                    user_name['profile_pic_name'], 
                                    p['p_title'], 
                                    p['p_text'], 
                                    url_for('user_view', user_name=user_name['users_name']), 
                                    p['p_post_date'], 
                                    current_post_time, 
                                    total_votes, 1)
        else:
            new_post = generate_json(p['post_id'], 
                                    user_name['users_name'], 
                                    user_name['profile_pic_name'], 
                                    p['p_title'], 
                                    p['p_text'], 
                                    url_for('user_view', user_name=user_name['users_name']), 
                                    p['p_post_date'], 
                                    current_post_time, 
                                    total_votes, 0)
        posts.append(new_post)

    # get user image
    if user_id is not None:
        query = f'SELECT profile_pic_name, users_name FROM USERS WHERE users_id = {user_id}'
        user_pic = db_ops.select_query(conn, query, one=True)
        return render_template('community.html', posts=posts, user_pic=user_pic[0], users_name=user_pic[1], form=form, upload_form=upload_form, title='Community - KTG', login=session.get('user'))
    else:
        return render_template('community.html', posts=posts, user_pic=None, form=form, upload_form=upload_form, title='Community - KTG', login=session.get('user'))


@app.route("/community/like/<int:community_id>", methods=['POST', 'GET'])
def like(community_id):
    conn = get_db_connection()
    current_user_id = session.get('user')
    if current_user_id is None:
        return redirect(url_for('community'))

    # 1 is like --- 2 is dislike
    query = f'SELECT * FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    check_interaction = db_ops.select_query(conn, query, one=True)

    if check_interaction is not None:
        query = f'UPDATE LIKE_DISLIKE SET like_dislike = 1 WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    else:
        query = f'INSERT INTO LIKE_DISLIKE VALUES({community_id}, {current_user_id}, 1)'

    if db_ops.UID_query(conn, query):
        print('Like Success')
    
    return redirect(url_for('community'))


@app.route("/community/dislike/<int:community_id>", methods=['POST', 'GET'])
def dislike(community_id):
    conn = get_db_connection()
    current_user_id = session.get('user')
    if current_user_id is None:
        return redirect(url_for('community'))

    query = f'SELECT * FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    check_interaction = db_ops.select_query(conn, query, one=True)

    if check_interaction is not None:
        query = f'UPDATE LIKE_DISLIKE SET like_dislike = 2 WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    else:
        query = f'INSERT INTO LIKE_DISLIKE VALUES({community_id}, {current_user_id}, 2)'

    if db_ops.UID_query(conn, query):
        print('Dislike Success')
    
    return redirect(url_for('community'))


@app.route("/community/reply/like/<int:community_id>", methods=['POST', 'GET'])
def reply_like(community_id):
    conn = get_db_connection()
    current_user_id = session.get('user')
    if current_user_id is None:
        return redirect(url_for('reply', community_id=community_id))

    # 1 is like --- 2 is dislike
    query = f'SELECT * FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    check_interaction = db_ops.select_query(conn, query, one=True)

    if check_interaction is not None:
        query = f'UPDATE LIKE_DISLIKE SET like_dislike = 1 WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    else:
        query = f'INSERT INTO LIKE_DISLIKE VALUES({community_id}, {current_user_id}, 1)'

    if db_ops.UID_query(conn, query):
        print('Like Success')
    
    return redirect(url_for('reply', community_id=community_id))


@app.route("/community/reply/dislike/<int:community_id>", methods=['POST', 'GET'])
def reply_dislike(community_id):
    conn = get_db_connection()
    current_user_id = session.get('user')
    if current_user_id is None:
        return redirect(url_for('reply', community_id=community_id))

    query = f'SELECT * FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    check_interaction = db_ops.select_query(conn, query, one=True)

    if check_interaction is not None:
        query = f'UPDATE LIKE_DISLIKE SET like_dislike = 2 WHERE community_post_id = {community_id} and interact_user_id = {current_user_id}'
    else:
        query = f'INSERT INTO LIKE_DISLIKE VALUES({community_id}, {current_user_id}, 2)'

    if db_ops.UID_query(conn, query):
        print('Dislike Success')
    
    return redirect(url_for('reply', community_id=community_id))    

@app.route("/community/reply/<community_id>", methods=['POST', 'GET'])
def reply(community_id):
    form = forms.ReplyForm()

    # database connection
    conn = get_db_connection()

    # check if new reply was made and user is logged in
    if form.validate_on_submit() and session.get('user') is not None:
        query = f'select max(post_id) + 1 from POSTS'
        new_id = db_ops.select_query(conn, query, one=True)
        user_id = session.get('user')

        get_string = f"""{form.replyText.data}"""
        post_date = datetime.datetime.now()
        post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
        query = f"""INSERT INTO POSTS (post_id, u_id, p_text, type_of_text, p_post_date) 
                    VALUES({new_id[0]}, {user_id}, '{get_string}', 'COMMENT', '{post_date}')"""

        queries = f"""INSERT INTO POSTS (post_id, u_id, p_text, type_of_text, p_post_date) VALUES({new_id[0]}, {user_id}, '{get_string}', 'COMMENT', '{post_date}');
                    INSERT INTO REPLY VALUES({community_id}, {new_id[0]});"""

        if db_ops.UID_many_query(conn, queries):
            #query = f"""INSERT INTO REPLY VALUES({community_id}, {new_id[0]})"""
            #db_ops.UID_query(conn, query)
            print('New reply has been inserted')
        form.replyText.data = ""

    # get the name, title, content, profile_link, time_stamp, and check for if image or not from database
    query = f'SELECT post_id, u_id, p_title, p_text, type_of_text, p_post_date FROM POSTS WHERE post_id = {community_id}'
    post_db = db_ops.select_query(conn, query, one=True)
    
    # convert into json_items else if database already store everything, just use the table provided by the database 
    # (remember to switch things like post.name to post['name'] in the html file if you use the table provided by the database)
    # append everything to posts
    
    # append post data from database, profile_link = # and is_image = 0 as of now
    query = f"""SELECT users_name, profile_pic_name FROM USERS WHERE users_id={post_db['u_id']}"""
    user_name = db_ops.select_query(conn, query, one=True)
    current_post_time = datetime.datetime.now()
    
    
    # calculate total upvotes
    query = f"""SELECT COUNT(*) FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and like_dislike = 1"""
    total_likes = db_ops.select_query(conn, query, one=True)
    query = f"""SELECT COUNT(*) FROM LIKE_DISLIKE WHERE community_post_id = {community_id} and like_dislike = 2"""
    total_dislikes = db_ops.select_query(conn, query, one=True)
    total_votes = total_likes[0] - total_dislikes[0]

    if post_db['type_of_text'] == 'COMMUNITY_IMAGE':
        new_post = generate_json(post_db['post_id'], 
                                user_name['users_name'], 
                                user_name['profile_pic_name'], 
                                post_db['p_title'], 
                                post_db['p_text'], 
                                url_for('user_view', user_name=user_name['users_name']), 
                                post_db['p_post_date'], 
                                current_post_time, 
                                total_votes, 1)
    else:
        new_post = generate_json(post_db['post_id'], 
                                user_name['users_name'], 
                                user_name['profile_pic_name'], 
                                post_db['p_title'], 
                                post_db['p_text'], 
                                url_for('user_view', user_name=user_name['users_name']), 
                                post_db['p_post_date'], 
                                current_post_time, 
                                total_votes, 0)

    # get replies
    query = f"""SELECT U.users_name, U.profile_pic_name, P.p_text, P.type_of_text, P.p_post_date
            from POSTS as P join REPLY as C on P.post_id = C.reply_post_id join USERS as U on U.users_id = P.u_id
            WHERE P.type_of_text = \'COMMENT\' and C.community_post_id = {community_id} ORDER BY P.p_post_date DESC"""
    users = db_ops.select_query(conn, query) 

    replies = []

    for reply in users:
        new_reply = generate_reply_json(reply['users_name'], 
                                        reply['profile_pic_name'], 
                                        reply['p_text'], 
                                        url_for('user_view', user_name=reply['users_name']), 
                                        reply['p_post_date'], 
                                        current_post_time, 0)
        replies.append(new_reply)

    return render_template('post.html', form=form, title='Reply - KTG', community_id=community_id, post=new_post, replies=replies, login=session.get('user'))

# calculate time for post_dates
def calculate_time(time_stamp, current_time):
    #current_now = datetime.datetime.now()
    #second_time = posts[0]['time_stamp']
    post_time = datetime.datetime.strptime(time_stamp,'%Y-%m-%d %H:%M:%S')
    diff_time = current_time - post_time
    total_seconds = int(diff_time.total_seconds())
    total_minutes = int(total_seconds / 60)
    total_hours = int(total_minutes / 60)
    total_days = int(total_hours / 24)
    total_weeks = int(total_days / 7)
    total_months = int(total_days / 30)
    total_years = int(total_months / 12)
    if total_seconds < 60:
        time_string = 'a few seconds ago'
    elif total_minutes < 60:
        time_string = f'{total_minutes} minutes ago'
    elif total_hours < 24:
        time_string = f'{total_hours} hours ago'
    elif total_days < 8:
        time_string = f'{total_days} days ago'
    elif total_weeks < 5:
        time_string = f'{total_weeks} weeks ago'
    elif total_months < 13:
        time_string = f'{total_months} months ago'             
    else:
        time_string = f'{total_years} years ago'             

    return time_string

# generate a json item such that we can do variable_name.name, variable_name.title, etc
def generate_json(post_id, name, picture, title, content, profile_link, time_stamp, current_time, upvotes, is_image):
    
    post_time = calculate_time(time_stamp, current_time)
    json_item = {
        'post_id': post_id,
        'name': name,
        'user_pic': picture,
        'title': title,
        'content': content,
        'profile_link': profile_link,
        'time_stamp': post_time,
        'upvotes': upvotes,
        'is_image': is_image
    }
    return json_item

# generate a json item for replies
def generate_reply_json(name, picture, reply_content, profile_link, time_stamp, current_time, reply_is_image):
    post_time = calculate_time(time_stamp, current_time)
    reply_json_item = {
        'name': name,
        'user_pic': picture,
        'reply_content': reply_content,
        'profile_link': profile_link,
        'time_stamp': post_time,
        'reply_is_image': reply_is_image
    }
    return reply_json_item
####################### Community BLOCK END #######################    


####################### User view BLOCK START #######################    
@app.route("/user/<user_name>", methods=['POST', 'GET'])
def user_view(user_name):
    conn = get_db_connection()
    query = f'SELECT * FROM USERS WHERE users_name = \'{user_name}\''
    check_user = db_ops.select_query(conn, query, one=True)

    if check_user is not None:
        query = f'SELECT user_email, profile_pic_name, profile_description, users_name FROM USERS WHERE users_name = \'{user_name}\''
        user_info = db_ops.select_query(conn, query, one=True)
        query = f'SELECT COUNT(*) FROM POSTS as P join USERS as U on P.u_id = U.users_id WHERE users_name = \'{user_name}\''
        post_count = db_ops.select_query(conn, query, one=True)
    else:
        return redirect(url_for('index'))


    return render_template('user_view.html', post_count = post_count[0], user_info=user_info,  title='User - KTG', login=session.get('user'))


####################### User view BLOCK END #######################    

if __name__ == "__main__":
    app.run()
