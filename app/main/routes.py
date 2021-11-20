from flask import render_template, redirect, url_for, current_app, session
from app.main import bp
from app.main.forms import SearchForm
import pandas as pd
from datetime import datetime, timedelta

# authlib version 13 +
from authlib.integrations.requests_client import OAuth2Session
from app import client
from bs4 import BeautifulSoup
from app.decorators import *


# curl -X POST -u 'client_a2d1bf0b6857ae01a6f9ff352f3fbd39:secret_62134ebc40d8c82372c9021c75462529' -H "Content-Type: application/x-www-form-urlencoded" -d 'grant_type=client_credentials&scope=api_listings_read' 'https://auth.domain.com.au/v1/connect/token' 

def get_token():
    scope='api_listings_read'
    authorization_response = 'https://rentprop.pythonanywhere.com'
    client = OAuth2Session(current_app.config['DOMAIN_CLIENT_ID'], current_app.config['DOMAIN_CLIENT_SECRET'], scope=scope)
    # token = client.fetch_access_token('https://auth.domain.com.au/v1/connect/token', grant_type='client_credentials')
    # now = datetime.now()
    # later = now + timedelta(seconds=token['expires_in']-900)

    resp = client.fetch_token('https://auth.domain.com.au/v1/connect/token', authorization_response=authorization_response)
    # current_app.logger.info(resp.items())
    return resp


def get_session(token):
    return OAuth2Session(current_app.config['DOMAIN_CLIENT_ID'], current_app.config['DOMAIN_CLIENT_SECRET'], token=token)


# In case key does not exist in JSON, then return an empty string
def get_data(data, key):
    if key in data:
        #print(data[key])
        return data[key]
    else:
        #print('')
        return ''

# Contact is returned in list of dictionaries, sometimes they are empty
# This functions, outputs the data in normal string format
def get_contact(contact):
    con_str = ''
    if len(contact) != 0:
        for i,c in enumerate(contact):
            # check if key exists in dictionary
            if 'name' in c:
                # if last element then dont have comma separator
                sep = ', '
                if i >= len(contact)-1:
                    sep = ''
                # if yes append value to string
                con_str = con_str + c['name'] + sep
    else:
        #list is empty
        return ''
    return con_str


@bp.route('/')
@bp.route('/index', methods=['GET','POST'])
@login_required
def index():
    form=SearchForm()
    if form.validate_on_submit():

        # if first time
        if 'domain' not in session:
            session['domain'] = get_token()

        # get token again if expired
        expiry = datetime.now() + timedelta(seconds=session['domain']['expires_in']-900)
        if datetime.now() >= expiry:
            session['domain'] = get_token()

        # build data from search filters to send to domain
        data = dict()
        min_bedrooms = int(form.min_bedrooms.data)
        min_bathrooms = int(form.min_bathrooms.data)
        max_price = int(form.max_price.data)

        #surround_suburbs = form.surround_suburbs.data
        postcode = form.postcode.data
        if (min_bedrooms != -1):
            data['minBedrooms'] = min_bedrooms
        if (min_bathrooms != -1):
            data['minBathrooms'] = min_bathrooms
        if (max_price):
            data['maxPrice'] = max_price
        if (postcode):
            loc_data = []
            loc_data.append({'postcode':postcode})
            data['locations'] = loc_data
        #if (postcode or surround_suburbs):
        #    loc_data = []
        #    if (postcode):
        #        loc_data.append({'postcode':postcode})
        #    if (surround_suburbs):
        #        loc_data.append({'includeSurroundingSuburbs':surround_suburbs})
        #    data['locations'] = loc_data
        data['page'] = 1
        data['pageSize'] = 200
        data['listingType'] = 'Rent'

        # send a post request to domain api with json data
        domain_session = get_session(session['domain'])
        resp=domain_session.post('https://api.domain.com.au/v1/listings/residential/_search',json=data)

        # construct pandas dataframe and save to csv
        df = pd.DataFrame(columns=[\
        'Property type', 'Price', 'Suburb','Postcode','Display address','Bedrooms',\
        'Bathrooms','Carspaces','Headline','Description',\
        'url','Advert type','Advert name','Advert contact'\
        ])
        json_resp = resp.json()
        for j in json_resp:
            df = df.append({\
                'Property type': get_data(data=j['listing']['propertyDetails'], key='propertyType'),\
                'Price': get_data(data=j['listing']['priceDetails'], key='displayPrice'),\
                'Suburb': get_data(data=j['listing']['propertyDetails'], key='suburb'),\
                'Postcode': get_data(data=j['listing']['propertyDetails'], key='postcode'),\
                'Display address' : get_data(data=j['listing']['propertyDetails'], key='displayableAddress'),\
                'Bedrooms': get_data(data=j['listing']['propertyDetails'], key='bedrooms'),\
                'Bathrooms': get_data(data=j['listing']['propertyDetails'], key='bathrooms'),\
                'Carspaces': get_data(data=j['listing']['propertyDetails'], key='carspaces'),\
                'Headline': get_data(data=j['listing'], key='headline'),\
                'Description': BeautifulSoup(get_data(data=j['listing'], key='summaryDescription'),'html.parser').\
                    get_text().replace('\r','').replace('\n',' '),\
                'url': 'http://www.domain.com.au/'+get_data(data=j['listing'], key='listingSlug'),\
                'Advert type': get_data(data=j['listing']['advertiser'], key='type'),\
                'Advert name': get_data(data=j['listing']['advertiser'], key='name'),\
                'Advert contact': get_contact(get_data(data=j['listing']['advertiser'], key='contacts'))\
                }, ignore_index=True)

        # get current date time for filename
        curr_dt = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = curr_dt + '_domain.csv'
        df.to_csv(current_app.config['RENTAL_FOLDER'] / filename, index=False)
        return render_template('main/results.html',data=df, filename=filename)

    return render_template('main/index.html',form=form)


@bp.route('/other', methods=['GET'])
@login_required
def other():
    # project id 417245 is the rental project in scrapy cloud
    project = client.get_project(417245)

    # get the spider which is called rental
    spider = project.spiders.get('rental')

    # get the most recent job's key
    jobs_summary = spider.jobs.iter()
    key = [j['key'] for j in jobs_summary][0]

    # get the most recent job
    job = client.get_job(key)

    # retrieve items
    items = job.items.iter()

    # construct pandas dataframe and save to csv
    df = pd.DataFrame(columns=[\
    'Suburb','Status','Price','Home Type','Available','Occupants','Description','url'
    ])

    for item in items:
        df = df.append({\
            'Suburb': item['suburb'],\
            'Status': item['status'],\
            'Price': item['price'],\
            'Home_Type': item['home_type'],\
            'Available': item['available'],\
            'Occupants': item['occupants'],\
            'Description': item['description'],\
            'url': item['url']
        }, ignore_index=True)

    df.to_csv(current_app.config['RENTAL_FOLDER'] / 'other.csv', index=False)

    return render_template('main/other.html', data=df)


@bp.route('/logout', methods=['GET'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('auth.login'))
