import os, logging
from datetime import datetime
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

@app.errorhandler(500)
def general_app_error(e):
    """ General Error Hanlder
        returns 500 on invocation
    """
    return jsonify(error=str(e)), 500

@app.route('/')
def appRoot():
    person = {'name': 'PR request 1', 'birth-year': 1978}
    return jsonify(person)

@app.route('/map')
def map():
    r = jsonify({'type':'FeatureCollection',
    'features': [
        {'type': 'Feature', 
        'geometry': {
        'type': 'Point', 
        'coordinates': [
            -122.47466532112183,
             37.83810157315523
             ]},
    'properties':{
        'title': 'Omars House',
        'cluster': False,
        'venue': 'blackcat',
        'event_count': 10
    }
    }]})
    r.headers.add('Access-Control-Allow-Origin', '*')
    return r

@app.route('/healthz')
def healthcheck():
    now = datetime.now()

    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    return jsonify({"message": "Hello From  Flask App, Current Date is : {} ".format(dt_string)})

def get_db_connection():
    conn = psycopg2.connect(host=os.environ['PGHOST'],
                            database=os.environ['PGDATABASE'],
                            user=os.environ['PGUSER'],
                            password=os.environ['PGPASSWORD'])
    return conn


@app.route('/read')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books;')
    books = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(books)

@app.route('/seed')
def seed():
    conn = get_db_connection()
    cur = conn.cursor()
# Open a cursor to perform database operations
        

# Execute a command: this creates a new table
    cur.execute('DROP TABLE IF EXISTS books;')
    cur.execute('CREATE TABLE books (id serial PRIMARY KEY,'
                                 'title varchar (150) NOT NULL,'
                                 'author varchar (50) NOT NULL,'
                                 'pages_num integer NOT NULL,'
                                 'review text,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
                                 )

# Insert data into the table

    cur.execute('INSERT INTO books (title, author, pages_num, review)'
            'VALUES (%s, %s, %s, %s)',
            ('A Tale of Two Cities',
             'Charles Dickens',
             489,
             'A great classic!')
            )


    cur.execute('INSERT INTO books (title, author, pages_num, review)'
            'VALUES (%s, %s, %s, %s)',
            ('Anna Karenina',
             'Leo Tolstoy',
             864,
             'Another great classic!')
            )

    conn.commit()

    cur.close()
    conn.close()
    return('success!')

@app.route('/post', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        pages_num = int(request.form['pages_num'])
        review = request.form['review']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author, pages_num, review)'
                    'VALUES (%s, %s, %s, %s)',
                    (title, author, pages_num, review))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('success!'))

    return render_template('success!')

if __name__ == "__main__":

    if os.getenv('ENVIRONMENT') is not None:
        app.config['environment'] = os.getenv('ENVIRONMENT')
    else:
        app.config['environment'] = "dev"

    app.run(debug=False, host='0.0.0.0', port=os.getenv("PORT", default=5000))