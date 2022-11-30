import logging as log
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        log.error('Article {} does not exist'.format(post_id))
        return render_template('404.html'), 404
    else:
        log.info('Fetched article {}'.format(post_id))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log.info('About page was retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
            log.warn('Validation error: Title is required')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            log.info('Article {} was created'.format(title))

            return redirect(url_for('index'))

    return render_template('create.html')

def validate_db_connectivity():
    # Internal method to validate a healthy connection to the database
    try:
        conn = get_db_connection()
        conn.close()
    except:
        raise Exception("Could not validate connectivity to the database")

@app.route('/healthz', methods=['GET'])
def healthz():
    response_content = {'result': 'OK - healthy'}
    response_statuscode = 200

    response = app.response_class(
        response = json.dumps(response_content),
        status = response_statuscode,
        mimetype = 'application/json')

    return response

def get_article_count(metrics):
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()
        conn.close()

        metrics['post_count'] = count[0]
        metrics['db_connection_count'] += 1
    except:
        raise Exception("Could not get database metrics due to error")

@app.route('/metrics', methods=['GET'])
def metrics():
    metrics_details = {
        'post_count': None,
        'db_connection_count': 0
    }

    get_article_count(metrics_details)

    response = app.response_class(
        response=json.dumps(metrics_details),
        status=200,
        mimetype='application/json')

    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
