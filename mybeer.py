#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.dist import use_library
use_library('django','1.2')
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
import os
from google.appengine.ext.webapp import template

template.register_template_library('filters.myfilters')

class State (db.Model):
	Name = db.StringProperty(required=True)
	Acronym = db.StringProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)

class Style(db.Model):
	Name = db.StringProperty(required=True)
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
class User(db.Model):
	UserID = db.StringProperty(required=True)
	FirstName = db.StringProperty(default="")
	LastName = db.StringProperty(default="")
	DisplayName = db.StringProperty(required=True)
	Email = db.EmailProperty()
	NumberOfReviews = db.IntegerProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)

class Brewery(db.Expando):
	Name = db.StringProperty(required=True)
	Address = db.TextProperty()
	AddressPostal = db.PostalAddressProperty()
	AddressCity = db.StringProperty()
	AddressState = db.ReferenceProperty(State)
	Website = db.LinkProperty()
	Phone = db.PhoneNumberProperty()
	EstablishedYear = db.IntegerProperty()
	EstablishedMonth = db.IntegerProperty()
	OpenToPublic = db.StringProperty(choices=('Yes','No','Not Sure'))
	Notes = db.TextProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
class Beer(db.Model):
	Brewery = db.ReferenceProperty(Brewery,collection_name='Beers')
	Name = db.StringProperty()
	Style = db.ReferenceProperty(Style,collection_name='Beers')
	Family = db.StringProperty()
	ABV = db.FloatProperty()
	IBU = db.IntegerProperty()
	NumberOfReviews = db.IntegerProperty()
	AverageRating = db.FloatProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)

class BeerPhoto(db.Model):
	Beer = db.ReferenceProperty(Beer,collection_name='Photos')
	Path = db.StringProperty(required=True)
	Caption = db.StringProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
class BeerPhotoRating(db.Model):
	BeerPhoto = db.ReferenceProperty(BeerPhoto,collection_name='Ratings')
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
class BeerReview(db.Model):
	Beer = db.ReferenceProperty(Beer,collection_name='BeerReviews')
	Author = db.ReferenceProperty(User,collection_name='Reviews')
	AuthorID = db.StringProperty()
	Rating = db.IntegerProperty()
	Review = db.TextProperty()
	Source = db.StringProperty()
	PurchaseLocationState = db.ReferenceProperty(State)
	PurchaseLocationCity = db.StringProperty()
	PurchaseLocationEstablishment = db.StringProperty()
	Aroma = db.StringProperty()
	Flavor = db.StringProperty()
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
class BeerReviewRating(db.Model):
	Review = db.ReferenceProperty(BeerReview,collection_name='Ratings')
	Rating = db.IntegerProperty()
	RatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedBy = db.UserProperty(auto_current_user_add=True)
	CreatedDT = db.DateTimeProperty(auto_now_add=True)
	
# Page Classes
class Base(webapp.RequestHandler):
	def DefaultAppVars(self):
		AppName = 'Beer Engine'
		user = users.get_current_user()
		if user:
			storeduser = db.GqlQuery("SELECT * FROM User WHERE UserID = :1",users.get_current_user().user_id())
			if storeduser.count() > 0:
				uobject = storeduser[0]
			else:
				uobject = {'DisplayName':'Anonymous'}
				self.redirect('/login')
			username = user.nickname()
			SignInURL = users.create_logout_url(self.request.uri) if self.request.uri.find('profile') == -1 else users.create_logout_url('/')
			SignInText = 'Logout'
			SignedIn = True
		else:
			uobject = {'DisplayName':'Anonymous'}
			email = ''
			SignInURL = users.create_login_url("/login")
			SignInText = 'Login'
			SignedIn = False

		template_values = {
			'AppName':AppName,
			'UserObject': uobject,
			'IsAdmin':users.is_current_user_admin(),
			'SignedIn':SignedIn,
			'SignInURL':SignInURL,
			'SignInText':SignInText
		}
		
		return template_values

class Home(Base):	
	def get(self):

		template_values = self.DefaultAppVars()
		
		path = os.path.join(os.path.dirname(__file__),'home.html')
		self.response.out.write(template.render(path,template_values))

class AddBrewery(Base):
    def get(self):
	
		template_values = self.DefaultAppVars()
		states = db.GqlQuery("SELECT * FROM State ORDER BY Name")
		
		template_values["States"] = states
		
		path = os.path.join(os.path.dirname(__file__),'addbrewery.html')
		self.response.out.write(template.render(path,template_values))

class AddBreweryAction(webapp.RequestHandler):
	def post(self):
		
		state = db.get(self.request.get('AddressState')) if self.request.get('AddressState') != '' else None
		
		brewery = Brewery(Name=self.request.get('Name'),
						  Address=self.request.get('Address'),
						  AddressPostal=self.request.get('Address'),
						  AddressCity=self.request.get('AddressCity'),
						  AddressState=state,
						  Website=self.request.get('Website'),
						  Phone=self.request.get('Phone'),
						  EstablishedYear=int(self.request.get('EstablishedYear')) if self.request.get('EstablishedYear') != '' else None,
						  EstablishedMonth=int(self.request.get('EstablishedMonth')) if self.request.get('EstablishedMonth') != '' else None,
						  OpenToPublic=self.request.get('OpenToPublic'),
						  Notes=self.request.get('Notes'))

		brewery.put()
		self.redirect('/viewallbreweries')

class ViewAllBreweries(Base):
	def get(self):
		
		template_values = self.DefaultAppVars()
		
		breweries = db.GqlQuery("SELECT * FROM Brewery ORDER BY Name")
		
		template_values["Breweries"] = breweries
		
		path = os.path.join(os.path.dirname(__file__),'viewallbreweries.html')
		self.response.out.write(template.render(path,template_values))
		
class ViewBrewery(Base):
	def get(self, brewery_key):
		
		template_values = self.DefaultAppVars()
		
		brewery = db.get(brewery_key)
		beers = db.GqlQuery("SELECT * FROM Beer WHERE Brewery = :1 ORDER BY Name", brewery)
	
		template_values["Brewery"] = brewery
		template_values["Beers"] = beers
		
		path = os.path.join(os.path.dirname(__file__),'viewbrewery.html')
		self.response.out.write(template.render(path,template_values))

class AddBeer(Base):
    def get(self, brewery_key):
	
		template_values = self.DefaultAppVars()	
		
		brewery = db.get(brewery_key)
		styles = db.GqlQuery("SELECT * FROM Style ORDER BY Name")
		
		template_values["Brewery"] = brewery
		template_values["Styles"] = styles
		
		path = os.path.join(os.path.dirname(__file__),'addbeer.html')
		self.response.out.write(template.render(path,template_values))

class AddBeerAction(webapp.RequestHandler):
	def post(self, brewery_key):
		
		brewery = db.get(brewery_key)
		style = db.get(self.request.get('Style'))
		
		beer = Beer(Name=self.request.get('Name'),
					Brewery=brewery,
					Style=style,
					Family=self.request.get('Family'),
					ABV=float(self.request.get('ABV')) if self.request.get('ABV') != '' else None,
					IBU=int(self.request.get('IBU')) if self.request.get('IBU') != '' else None,
					NumberOfReviews = 0,
					AverageRating = 0.0)
		beer.put()
		self.redirect('/brewery/%s' % brewery_key)

class ViewBeer(Base):
	def get(self, beer_key):
		
		template_values = self.DefaultAppVars()
		
		beer = db.get(beer_key)
		count = 0.
		userlist = {}
		#for rev in beer.BeerReviews:
		#	count += rev.Rating
			#userrevs = db.GqlQuery("SELECT * FROM BeerReview WHERE Author = :1", rev.Author)
			#userlist[rev.Author.user_id()] = 5
		#avgrating = (count / beer.BeerReviews.count()) if beer.BeerReviews.count() > 1 else 0
		
		template_values["Beer"] = beer
		#template_values["AverageRating"] = round(avgrating,1)
		#template_values["UserList"] = userlist
		
		path = os.path.join(os.path.dirname(__file__),'viewbeer.html')
		self.response.out.write(template.render(path,template_values))

class ReviewBeer(Base):
	def get(self, beer_key):
		
		template_values = self.DefaultAppVars()
		
		beer = db.get(beer_key)
		states = db.GqlQuery("SELECT * FROM State ORDER BY Name")
	
		template_values["Beer"] = beer
		template_values["States"] = states
		
		path = os.path.join(os.path.dirname(__file__),'reviewbeer.html')
		self.response.out.write(template.render(path,template_values))

class ReviewBeerAction(Base):
	def post(self, beer_key):
		
		template_values = self.DefaultAppVars()
		UserObject = template_values["UserObject"]
		
		beer = db.get(beer_key)
		state = db.get(self.request.get('PurchaseLocationState')) if self.request.get('PurchaseLocationState') != '' else None
		
		#Insert Review
		review = BeerReview(Beer=beer,
							Author=UserObject,
							AuthorID=users.get_current_user().user_id(),
							Rating=int(self.request.get('RatingValue')),
							Review=self.request.get('Review'),
							Source=self.request.get('Source'),
							Aroma=self.request.get('Aroma'),
							Flavor=self.request.get('Flavor'),
							PurchaseLocationState=state,
							PurchaseLocationCity=self.request.get('PurchaseLocationCity'),
							PurchaseLocationEstablishment=self.request.get('PurchaseLocationEstablishment'))

		review.put()
		
		#Update Profile
		UserObject.NumberOfReviews += 1
		UserObject.put()
		
		#Update Beer Rating/ReviewCount
		beerrecord = db.get(beer_key) #re-get beerrecord after the above update
		beerrecord.NumberOfReviews = beerrecord.NumberOfReviews + 1
		ratingsum = 0.
		for reviews in beer.BeerReviews:
			ratingsum = ratingsum + reviews.Rating
		avgrating = (round(float(ratingsum / beerrecord.BeerReviews.count()),2)) if beerrecord.BeerReviews.count() > 0 else 0.0
		beerrecord.AverageRating = avgrating
		beerrecord.put()
		
		self.redirect('/beer/%s' % beer_key)

class Login(webapp.RequestHandler):
	def get(self):

		if users.get_current_user():
			user = db.GqlQuery("SELECT * FROM User WHERE UserID = :1",users.get_current_user().user_id())
			if user.count() == 0:
				user = User(UserID = users.get_current_user().user_id(),
						DisplayName=users.get_current_user().nickname(),
						NumberOfReviews = 0)
				user.put()
				self.redirect('/profile')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

class Profile(Base):
	def get(self):
		
		template_values = self.DefaultAppVars()
		
		path = os.path.join(os.path.dirname(__file__),'profile.html')
		self.response.out.write(template.render(path,template_values))		

class ProfileAction(webapp.RequestHandler):
	def post(self):
		
		uquery = db.GqlQuery("SELECT * FROM User WHERE UserID = :1",users.get_current_user().user_id())
		user = uquery.fetch(1)
		
		user[0].FirstName=self.request.get('FirstName')
		user[0].LastName=self.request.get('LastName')
		user[0].DisplayName=self.request.get('DisplayName')
		
		user[0].put()
		self.redirect('/profile')

class Admin(Base):
	def get(self):
		
		template_values = self.DefaultAppVars()
		
		path = os.path.join(os.path.dirname(__file__),'admin.html')
		self.response.out.write(template.render(path,template_values))
		
class ManageStyles(Base):
	def get(self):
		
		template_values = self.DefaultAppVars()
		
		styles = db.GqlQuery("SELECT * FROM Style ORDER BY Name")
		
		template_values["Styles"] = styles
		
		path = os.path.join(os.path.dirname(__file__),'managestyles.html')
		self.response.out.write(template.render(path,template_values))

class ManageStylesAction(webapp.RequestHandler):
	def post(self):
		
		style = Style(Name=self.request.get('Name'))

		style.put()
		self.redirect('/admin/managestyles')

class ManageStates(Base):
	def get(self):
		
		template_values = self.DefaultAppVars()
		
		states = db.GqlQuery("SELECT * FROM State ORDER BY Name")
		
		template_values["States"] = states
		
		path = os.path.join(os.path.dirname(__file__),'managestates.html')
		self.response.out.write(template.render(path,template_values))

class ManageStatesAction(webapp.RequestHandler):
	def post(self):
	
		states = [{'Name':'Alabama','Acronym':'AL'},{'Name':'Alaska','Acronym':'AK'},{'Name':'Arizona','Acronym':'AZ'},{'Name':'Arkansas','Acronym':'AR'},{'Name':'California','Acronym':'CA'},{'Name':'Colorado','Acronym':'CO'},{'Name':'Connecticut','Acronym':'CT'},{'Name':'Delaware','Acronym':'DE'},{'Name':'Florida','Acronym':'FL'},{'Name':'Georgia','Acronym':'GA'},{'Name':'Hawaii','Acronym':'HI'},{'Name':'Idaho','Acronym':'ID'},{'Name':'Illinois','Acronym':'IL'},{'Name':'Indiana','Acronym':'IN'},{'Name':'Iowa','Acronym':'IA'},{'Name':'Kansas','Acronym':'KS'},{'Name':'Kentucky','Acronym':'KY'},{'Name':'Louisiana','Acronym':'LA'},{'Name':'Maine','Acronym':'ME'},{'Name':'Maryland','Acronym':'MD'},{'Name':'Massachusetts','Acronym':'MA'},{'Name':'Michigan','Acronym':'MI'},{'Name':'Minnesota','Acronym':'MN'},{'Name':'Mississippi','Acronym':'MS'},{'Name':'Missouri','Acronym':'MO'},{'Name':'Montana','Acronym':'MT'},{'Name':'Nebraska','Acronym':'NE'},{'Name':'Nevada','Acronym':'NV'},{'Name':'New Hampshire','Acronym':'NH'},{'Name':'New Jersey','Acronym':'NJ'},{'Name':'New Mexico','Acronym':'NM'},{'Name':'New York','Acronym':'NY'},{'Name':'North Carolina','Acronym':'NC'},{'Name':'North Dakota','Acronym':'ND'},{'Name':'Ohio','Acronym':'OH'},{'Name':'Oklahoma','Acronym':'OK'},{'Name':'Oregon','Acronym':'OR'},{'Name':'Pennsylvania','Acronym':'PA'},{'Name':'Rhode Island','Acronym':'RI'},{'Name':'South Carolina','Acronym':'SC'},{'Name':'South Dakota','Acronym':'SD'},{'Name':'Tennesee','Acronym':'TN'},{'Name':'Texas','Acronym':'TX'},{'Name':'Utah','Acronym':'UT'},{'Name':'Vermont','Acronym':'VT'},{'Name':'Virginia','Acronym':'VA'},{'Name':'Washington','Acronym':'WA'},{'Name':'West Virginia','Acronym':'WV'},{'Name':'Wisconsin','Acronym':'WI'},{'Name':'Wyoming','Acronym':'WY'}]
		
		for state in states:
			State(Name=state['Name'],
				  Acronym=state['Acronym']).put()
		
		self.redirect('/admin/managestates')

class UpdateDB(webapp.RequestHandler):
	def get(self):
		print 'No Action'
		review = db.GqlQuery("SELECT * FROM BeerReview")
		#results = review.fetch(10)
		#cali = db.get("agZteWJlZXJyCwsSBVN0YXRlGCMM")
		#print cali
		#for r in results:
		#	r.AuthorID = '185804764220139124118'
		#	print r.AuthorID
		#	r.put()
		#	delattr(r,'AddressState')
		#	r.put()

def main():

	application = webapp.WSGIApplication([('/', Home),
											('/admin/addbeer/([\w]+)', AddBeer),
											('/admin/addbeeraction/([\w]+)', AddBeerAction),
											('/admin/addbrewery', AddBrewery),
											('/admin/addbreweryaction', AddBreweryAction),
											('/brewery/([\w]+)', ViewBrewery),
											('/viewallbreweries', ViewAllBreweries),
											('/beer/review/([\w]+)', ReviewBeer),
											('/beer/reviewaction/([\w]+)', ReviewBeerAction),
											('/beer/([\w]+)', ViewBeer),
											('/login', Login),
											('/profile', Profile),
											('/profileaction', ProfileAction),
											('/admin', Admin),
											('/admin/managestyles', ManageStyles),
											('/admin/managestylesaction', ManageStylesAction),
											('/admin/managestates', ManageStates),
											('/admin/managestatesaction', ManageStatesAction),
											('/admin/updateDB', UpdateDB)],
                                         debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
