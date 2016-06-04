import os
import requests
import operator
import re
import nltk
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup
import urllib2
from rq import Queue
from rq.job import Job
from worker import conn
from flask import jsonify


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

q = Queue(connection=conn)

from models import *


def get_and_save_categories(product):
    print 'here'
    errors = []

    try:
        url  = 'http://en.wikipedia.org/wiki/' + product
        r = requests.get(url)
    except:
        errors.append(
            "Unable to get URL. Please make sure it's valid and try again."
        )
        return {"error": errors}


    # get categories
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html5lib')
    data = soup.find('div', {'class' : 'mw-normal-catlinks'})
    data = data.findAll('a')
    categories = []

    for category in data:
        categories.append((category.text).encode('ascii'))

    # save the results
    results = categories
    #print results
    try:        
        from models import Result
        result = Result(
            url=url,
            category=categories,
        )
        db.session.add(result)
        db.session.commit()
        print 'rsultid', results.id
        return results.id
    except:
            errors.append("Unable to add item to database.")
            return {"error": errors}

@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == "POST":
        # get url that the person has entered
        product = request.form['url']
        job = q.enqueue_call(
            func=get_and_save_categories, args=(product,), result_ttl=5000
        )
        print job
        print(job.get_id())

    return render_template('index.html', results=results)

@app.route('/start', methods=['POST'])
def get_counts():
    # get url
    data = json.loads(request.data.decode())
    url = data["url"]
    # start job
    job = q.enqueue_call(
        func=count_and_save_words, args=(url,), result_ttl=5000
    )
    # return created job id
    return job.get_id()


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        print 'lala'
        result = Result.query.filter_by(id=job.result).first()
        print result
        return jsonify(results)
    else:
        return "Nay!", 202

if __name__ == '__main__':
    app.run()