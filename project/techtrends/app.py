import sqlite3
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash, make_response
from werkzeug.exceptions import abort
import logging

db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    db_connection_count += 1
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
        app.logger.info("This article does not exist. Please try again.")
        return render_template('404.html'), 404
    else:
        app.logger.info("Article \"" + post['title'] + "\" retrieved!")
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("About Us page retrieved!")
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info("Article \"" + title + "\" created!")
            return redirect(url_for('index'))

    return render_template('create.html')

# Define the health of the application
@app.route("/healthz")
def status():
    data = {
        'message': 'result: OK - healthy'
    }
    app.logger.info('Healthz endpoint successful')
    return make_response(jsonify(data), 200)

# Define the metrics of the application
@app.route("/metrics")
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    data = {
        'db_connection_count': db_connection_count,
        'post_count': len(posts)
    }
    app.logger.info('Metrics request successful')
    connection.close()
    return make_response(jsonify(data), 200)

# start the application on port 3111
if __name__ == "__main__":
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    handlers = [stderr_handler, stdout_handler]
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers)
    app.run(host='0.0.0.0', port='3111', debug=True)
