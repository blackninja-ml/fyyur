#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SECRET KEY'] = '12345678'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost:5432/fyyur'
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#Here Show acts as the parent class to configure relationaship dynamics between parents and children. It connects model venue and 
#artist together. It is the parent in this one-2-many database model.
class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    venue = db.relationship('Venue', backref=db.backref('shows'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    artist = db.relationship('Artist', backref=db.backref('shows'))
    
    def __repr__(self):
        return f'<Show {self.id} {self.venue_id} {self.artist_id} {self.start_time} >'

#Venue and Artist are the child class in this relational database model.(one to many)
#column country is added to both the Venue and Artist model because venues could be international.
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(), nullable=True)
    address = db.Column(db.String(120), nullable=False)
    #Since phone number could be international, therefore parseing them into 3 digits.
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    genres = db.Column(ARRAY(db.String()), nullable=False)
    website = db.Column(db.String())
    seeking_talent = db.Column(db.String(), default=False)
    seeking_description = db.Column(db.String(), default="We are looking for exceptional talents joining our team. Please contact us for more details.")
    
    def __repr__(self):
        return f'<Venue {self.id} {self.city} {self.state} {self.country} venue.id ={venue.id}>'

#Artist is the child class in this one-to-many relational database model
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,  nullable=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(), nullable=True)
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    twitter_link = db.Column(db.String())
    website = db.Column(db.String(), nullable=False)
    seeking_venue = db.Column(db.String())
    seeking_description = db.Column(db.String(),  default="We are looking for venues to hold our shows. Please contact us for more details.")
    instagram_link = db.Column(db.String(), nullable=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.city} {self.state} {self.country} artist.id = {artist.id}>'
    

#db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data=[]

    #Get the data of venues in city and state.
    address = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  
    venues = Venue.query.all()
    
    #After getting the venue data, appending them to the data dictionary
    #Since the venues in this model could be international, and therefore two cases would be separated.
    #venues'location would display venues within the States in terms o city, state, and country code 
    #venues outside the state would be displayed in terms of city and country only
    for a in address:
        if (Venue.state != ''):
            venues_ = db.session.query(Venue.id, Venue.name).filter(Venue.city == a[0]).filter(Venue.state == a[1])
            venues_order = venues_.order_by(Venue.name).all()
            data.append({
                "city": a[0],
                "state": a[1],
                "venues": venues_order
            })

    
    if (Venue.state == 'None'):
        cities_countries = set()
        for v in venues:
            cities_countries.add((v.city, v.country))

    #make a list to store the venues that are outside of the US and would be stored in the data dictionary.
        goup = list(cities_countries)
        goup_ = db.session.query(Venue).filter(Venue.state == '')
        gouo_order = goup_.order_by(Venue.name)
        data.append({
            #"city": goup_.city,
            "state": None,
            "country":Venue.country,
            "venues": gouo_order
        })


            
    return render_template('pages/venues.html', areas=data);

#  Search Venue
#  ----------------------------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')

  venues = Venue.query.filter(Venue.name.ilike(f'%{ search_term }%')).all()
  #use filter and do the like search for users 
  time_now = datetime.now()
  data = []

  for venue in venues:
    upcoming_shows = 0
    past_shows = 0
    current_shows = 0

    shows = Show.query.filter(Show.venue_id == venue.id).all()
    
    #looping through the show fetching from the query
    #looped shows would be categorized into upcoming shows, past shows and current shows
    #if the datetime.now is within the same day as any shows in the database then it would be considered to be in the current shows category.
    for show in shows:
        if (show.start_time > datetime.now()):
            upcoming_shows = upcoming_shows+1;

        elif(show.start_time.day == datetime.now().day):
            current_shows = current_shows + 1;
        
        else:
            past_shows = past_shows +1;

    #After the shows are added to this list and then other data would be appended to the data dictionary.

    data.append({
        "id": venue.id,
        "name": venue.name,
        "current_shows": current_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows
    })
    #presenting the result of the shows when the users do the search.
  response={
        "count": len(venues),
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "data": data
    }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

#  Show Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  list_shows = db.session.query(Show).filter(Show.venue_id == venue_id)

#this route shows the venue page with a given venue id
#setting up different dictionaries here
#a user must hand type this page with given id in order to access it and change the venue data
#no buttons are available in the webpage
  today = datetime.day
  past_shows = []
  past_shows_num = 0
  upcoming_shows = []
  upcoming_shows_num = 0
  current_shows_num = 0
  current_shows = []

  #once again, same thing here
  #shows are categoized into three types
  #current shows happen within 24hour with the time when a user access the page

  for show in list_shows:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).one()
    
    showlist = {
        "venue_facebook_link": venue.facebook_link,
        "venue_website": venue.website,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime('%m/%d/%Y, %H:%M')
        }

    if (show.start_time < datetime.now()):
        past_shows.append(showlist)
        past_shows_num +=1

    elif(show.start_time.day== today):
        current_shows.appen(showlist)
        current_shows_num +=1
    else:
        upcoming_shows.append(showlist)
        upcoming_shows_num+=1

  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "country": venue.country,
      "phone": venue.phone,
      "website": venue.website,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "current_shows": current_shows,
      "past_shows_num": len(past_shows),
      "upcoming_shows_num": len(upcoming_shows),
      "current_shows_num": len(current_shows),
      "facebook_link": venue.facebook_link,
      "image_link": venue.image_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ##########################################################################################################

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


#Constructing venue forms for user who wants to post a venue on the site
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    error = False


    places = Venue(
        name = form.name.data.strip(),
        city = form.city.data.strip(),
        state = form.state.data.strip(),
        genres = form.genres.data,
        address = form.address.data,
        country =  form.country.data,
        phone = form.phone.data,
        website = form.website.data.strip(),
        image_link = form.image_link.data.strip(),
        facebook_link = form.facebook_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data.strip(),
        youtube_link = form.youtube_link.data.strip()
    
    )
    try:
        db.session.add(places)
        db.session.commit()
        
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        flash('plase come back to Venue''s page to check your listing.')
        error = False
    except:
        #warning is given when a listing is not successfully to be sent to the database.
        #error would be set to true as a flag.
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if (error == True):
        flash('An error has occured. Please come back again later')

    return render_template('pages/home.html')
##################################################################################################################

#user can only access to this page with a given id and a 'slash-delete' typing along the url of the website
#once the url is typed with /delete with id, the record will be deleted for sure.
#  Delete Venue
@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        db.session.query(Venue).filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted!')

        #warning is given when the delete is unsuccessful.
    except:
        flash('An error occurred. Venue could not be deleted. Please come back again.')
    finally:
        db.session.close()

    return redirect(url_for('venues'))
######################################################################################################################
#  Artists Page
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  #This governs the display of a list of artists' data/
  #Getting artists' id and name from the db.session.
  data=[]
  artist = db.session.query(Artist.id, Artist.name).distinct(Artist.id, Artist.name)
  artists =  artist.order_by(Artist.name).all()

# all the required items are appended to the data list
  for a in artists:
      data.append({
        "id": a[0],
        "name": a[1],
      })
  return render_template('pages/artists.html', artists=data)

#  Search Artist
#######################################################################################################################33
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '').strip()
    #user filter and like for doing artists search otherwise it won't work quite well.

    artists = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
    data = []
    artist_pool = []

    #Artits veneus are appened and categorized according to their time and will be displayed on the webpages.
    

    for artist in artists:
        upcoming_shows = 0
        past_shows = 0
        current_shows = 0
        shows = Show.query.filter(Show.artist_id==artist.id)

        for show in shows:
            if(show.start_time > datetime.now()):
                upcoming_shows += 1
            
            elif(show.start_time.day == datetime.now().date):
                current_shows +=1
            else:
                past_shows += 1

        artist_items =({
            "id": artist.id,
            "name": artist.name,
            "upcoming_shows_num": upcoming_shows,
            "past_shows_num": past_shows,
            "current_shows_num": current_shows,
        })
        artist_pool.append(artist_items)

    data = {
            "id": artist.id,
            "name": artist.name,
            "upcoming_shows_num": upcoming_shows,
            "past_shows_num": past_shows,
            "current_shows_num": current_shows,
  }
    response={
        "count": len(artists),
        "data": artist_pool
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#  Show Artist
# ########################################################################################################################3
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).one()

#with the given artists' ids, their details are displayed on the page.
    list_shows = db.session.query(Show).filter(Show.artist_id == artist_id)
    past_shows = []
    past_shows_num = 0
    upcoming_shows = []
    upcoming_shows_num = 0
    current_shows = []
    current_shows_num = 0

#Fetching data and populate them to the data dictionary tuple.
    if not artist:
        flash('Sorry this id does not contain a list of an artist''s details.')
        redirect(url_for('/artists/'))

    for show in list_shows:
        show_venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()
        venue_details = db.session.query(Venue.website, Venue.facebook_link).filter(Venue.id==show.venue_id).one()


        add_show = {
            "venue_id": show.venue_id,
            "show_name": show_venue.name,
            "venue_image_link": show_venue.image_link,
            "website":venue_details.website,
            "venue_facebook_link": venue_details.facebook_link,
            "start_time": show.start_time.strftime('%m/%d/%Y, %H:%M')
            }

        if (show.start_time < datetime.now()):
            past_shows_num += 1
            past_shows.append(add_show)

        elif(show.start_time.date == datetime.now().day):
           current_shows_num +=1
           current_shows.append(add_show)

        else:
            upcoming_shows.append(add_show)
            upcoming_shows_count +=1

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "country": artist.country,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_num": past_shows_num ,
        "upcoming_shows_num": upcoming_shows_num,
        "current_shows_num": current_shows_num,
        "twitter_link": artist.twitter_link,
        "instagram_link": artist.instagram_link,
    }

    return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  -#######################################################################################################################

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

  #this form is given to the users for listing their artists info 
  #it is added with instagram_link and twitter_link data field. Since nowadays most artists have more than one type of 
  #social medial accounts

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    error = False

    artist = Artist(
        name = form.name.data,
        genres = form.genres.data,
        city = form.city.data,
        state = form.state.data,
        country= form.country.data,
        phone = form.phone.data,
        website = form.website.data,
        facebook_link = form.facebook_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data,
        image_link = form.image_link.data.strip(),
        twitter_link = form.twitter_link.data.strip(),
        instagram_link = form.instagram_link.data.strip(),
    )
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "country": artist.country,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_num": past_shows_num ,
        "upcoming_shows_num": upcoming_shows_num,
        "current_shows_num": current_shows_num,
        "twitter_link": artist.twitter_link,
        "instagram_link": artist.instagram_link,
    }
    #if error is occured, warning is given and they will be directed to the create artist submission form session.
    if (error == True):
        flash (' An error has occured. Artist' + form.name.data + 'could not be listed for some reasons.')
        return (url_for('create_artist_submission'))

    try:
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed')
        db.session.rollback()
    finally:
        db.session.close()
    
    

    return render_template('pages/home.html')
######################################################################################################################
#  Delete Artist

#Same as delete venue, the delete action would be activated when a user input their url with artists/id/delete
#warning would be given when a delete is not succssful

@app.route('/artist/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        db.session.query(Artist).filter(Artist.id == artist_id).delete()
        db.session.commit()
        flash('Artist was successfully deleted!')
    except:
         flash('An error occurred. Artist could not be deleted.')
         db.session.rollback()
    finally:
         db.session.close()
    return redirect(url_for('artist'))
######################################################################################################################
#########  Update Artist

#the update page would only be accessible when an artist id is provided in the url with slash
#if the artist id does not exist a flash warning would be given.
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
    artist_order = db.session.query(Artist).order_by(Artist.name)
    if not artist:
        flash('The artist you entered does not exist in our database. Please come back again and check in later.')
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    form = ArtistForm(request.form)
    artist = db.session.query(Artist).filter(Artist.id == aritst_id).one()
    error = False

#Updating artist data to the DB
    updated_aritst = {
        name: form.name.data,
        genres: form.genres.data,
        #address: form.address.data,
        city: form.city.data,
        state: form.state.data,
        country: form.country.data,
        phone: form.phone.data,
        website: form.website.data,
        facebook_link: form.facebook_link.data.strip(),
        seeking_venue: form.seeking_venue.data.strip(),
        seeking_description: form.seeking_description.data.strip(),
        image_link: form.image_link.data.strip(),
        twitter_link: form.twitter_link.data.strip(),
        instagram_link: form.instagram_link.data.strip(),
    }
    try:
        db.session.query(Artist).filter(Artist.id == artist_id).update(updated_artist)
        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + form.name.data + ' could not be added')
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if (error == True):
        flash('An error has occured. Please contact the back-end developer for help')

    return redirect(url_for('show_artist', artist_id=artist_id))

##########################################################################################################################3
#  Update Venue


#update venue page is only accessible when a veneu id is atthced with a slash on the url of the webpage.
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter(Venue.id == venue_id).one()

    if not venue:
        flash('Sorry. This venue id does not exist.')


    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  #updating the veneu information
  #new_list dictionary is created for more information needed 
    new_list = {
        instagram: "Should be added",
        youtube_link: "please provide if available",
        availability : "Not updated",
    }
    #Getting data from an existing database
    form = VenueForm(request.form)
    venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
    error = False
    new_venue_list=[]
    genres_pool=[]

    new_venue= {
        name: form.name.data,
        genres: form.genres.data,
        address: form.address.data,
        city: form.city.data,
        state: form.state.data,
        country: form.country.data,
        phone: form.phone.data,

        website: form.website.data,
        facebook_link: form.facebook_link.data,
        seeking_talent: form.seeking_talent.data,
        seeking_description: form.seeking_description.data,
        image_link: form.image_link.data,
    }
    #A list of geners would be added to the dictionary for future data analysis on which types of music would be popular
    for g in genres:
        ggg =  db.session.query(venue.genres).order_by(venue.genres)
        print(ggg)
        genres_pool.append(ggg)


    try:
        db.session.query(Venue).filter(Venue.id == venue_id).update(new_venue)
        db.session.commit()
        flash('Venue' + form.name.data + ' was successfully updated!')
    except:
        flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error == True:
        flash('An error occured. Please contact the back-end developer for help.')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows Page
#  #################################################################################################################

#this page displays a list of shows 
@app.route('/shows')
def shows():
    data = []
    links = []
    shows = db.session.query(Show.artist_id, Show.venue_id, Show.start_time).all()

    for show in shows:
        social_media = db.session.query(Artist.facebook_link, Artist.twitter_link).filter(Artist.id == show[0]).one()
        artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show[0]).one()
        venue = db.session.query(Venue.name, Venue.id).filter(Venue.id == show[1]).one()
        
        link.append({
            "facebook_link": social_media[0],
            "twitter_link": social_media[1],

        })

        data.append({
            "venue_id": venue[1],
            "venue_name": venue[0],
            "artist_id": show[0],
            "artist_name": artist[0],
            "artist_image_link": artist[1],
            "start_time": format_datetime(str(show.start_time)),
            "twitter_link": social_media[1],
            "facebook_link":social_media[0],
        })

    return render_template('pages/shows.html', shows=data)

# ------------------------------------------------------------------------------------------------------------
#Delete Shows

#shows could be deleted if both the ids of venue and artists are given in the url
#the delete would only be working for shows it would not delete records of artists or venues
app.route('/shows/delete/<int:venue_id>/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        db.session.query(Show).filter(artist_id==venue_id).delete()
        db.session.commit()
        flash('The show was successfully cancelled.')
    except:
         flash('An error occurred. The show cannot be cancelled. Please come back again later')
         db.session.rollback()
    finally:
         db.session.close()
    return redirect(url_for('shows'))

# ___________________________________________________________________________________________________________
# Update shows
@app.route('/shows/create')
def create_shows():
  #this page allows user to give artist id and venue id to create a show
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

#new show data would be submitted to the database and a show.id would be created as well.
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    error = False

    show = Show(
        venue_id = form.venue_id.data.strip(),
        artist_id = form.artist_id.data,
        start_time = form.start_time.data.strip()
    )

    try:
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed')
    except:
        flash('An error occurred. Show ' + show.name + ' could not be added')
        db.session.rollback()
    finally:
        db.session.close()
    
    if (error == True):
        flash('An error has occured. Please contact our back end developer for more details')
    return render_template('pages/home.html')

###########################################################################################################
######THE END###########



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''