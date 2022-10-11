import os, logging
from datetime import datetime
import psycopg2
from flask import Flask, jsonify, request, redirect, render_template, url_for

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
    person = {'name': 'PR request 1', 'birth-year': 1979}
    return jsonify(person)

@app.route('/map')
def map():
    r = jsonify({'type':'FeatureCollection',
    'features': [
        {'type': 'Feature', 
        'geometry': {
        'type': 'Point', 
        'coordinates': [
            -122.41953280752264,
             37.776889463715875
             ]},
    'properties':{
        'title': "Shubha's House",
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

@app.route('/geoseed')
# Open a cursor to perform database operations
def geoseed():
    conn = get_db_connection()
    cur = conn.cursor()

# Execute a command: this creates a new table
    cur.execute('DROP TABLE IF EXISTS maps;')
    cur.execute('CREATE TABLE maps (id serial PRIMARY KEY,'
                                 'coordinates point NOT NULL,'
                                 'cluster boolean NOT NULL,'
                                 'event_count integer NOT NULL,'
                                 'title varchar (150) NOT NULL,'
                                 'venue varchar (150) NOT NULL,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
                                 )
    cur.execute('INSERT INTO maps (coordinates, cluster, event_count, title, venue)'
            'VALUES (%s, %s, %s, %s, %s)',
            ('-122.40688636105475,37.802538382504466',
             'FALSE',
             489,
             'North Beach',
             'Gigis')
            )
    
    conn.commit()
    cur.close()
    conn.close()
    return('success!')

@app.route('/georead')
def georead():
    Sql = """
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', jsonb_agg(features.feature)
    )
    FROM (
        SELECT jsonb_build_object(
            'type', 'Feature',
            'id', id,
            'geometry', jsonb_build_object('coordinates', coordinates),
            'properties', to_jsonb(inputs) - 'id' - 'coordinates'
    ) AS feature
    FROM (SELECT * from maps) inputs) features;
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(Sql)
    maps = cur.fetchall()
    cur.close()
    conn.close()
    r = jsonify(maps)
    r.headers.add('Access-Control-Allow-Origin', '*')
    return r

     

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