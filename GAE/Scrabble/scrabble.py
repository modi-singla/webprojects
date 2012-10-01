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
import os
import re
import webapp2
import jinja2
import urllib2
from google.appengine.ext import db
from xml.dom import minidom
import hmac
import hashlib
import random
from string import letters
from datetime import tzinfo, timedelta, datetime
import time
from threading import Thread
import json
from google.appengine.api import mail

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

secret = 'hithisisasecretstring'

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)
	
def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val

def make_salt(length = 5):
	return ''.join(random.choice(letters) for x in xrange(length))
		
def hash_password(password, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(password + salt).hexdigest()
	return '%s,%s' % (salt, h)
		
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
	return username and USER_RE.match(username)
		
PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
	return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
	return email and EMAIL_RE.match(email)

def get_user_by_username(username):
	if username:
		user = User.get_by_key_name(username)
		return user or False
	return False
		
def match_password(username, password, user):
	if(user):
		h = user.password
		salt = h.split(',')[0]
		return h == hash_password(password, salt)
	else:
		return False

def complete_online_users_list_in_html(search_term = ""):
	online_users = Online_User.all().filter("last_checked > ", datetime.now() - timedelta(minutes=1))
	retval = "<ul id=\"online_list\">"
	for user in online_users:
		if (user.state != 4) and ((not search_term) or (search_term in user.parent().fullname) or (search_term in user.username)):
			retval = retval + "<li class=\"opponent\" id=\"%s\">"% user.username
			if user.state==0:
				if (user.last_updated < datetime.now() - timedelta(minutes=5)):
					retval = retval + "<img src=\"static/idle.jpg\">"
				else:
					retval = retval + "<img src=\"static/available.jpg\">"
			else:
				retval = retval + "<img src=\"static/busy.jpg\">"
			retval = retval + "<div class=\"user_name\">%s</div></li>" % user.parent().fullname
	retval = retval + "</ul>"
	return retval
	
def complete_online_users_list_in_json(search_term = ""):
	online_users = Online_User.all().filter("last_checked > ", datetime.now() - timedelta(minutes=1))
	user_list = []
	for user in online_users:
		if (user.state != 4) and ((not search_term) or (search_term in user.parent().fullname) or (search_term in user.username)):
			state = 0
			if user.state==0:
				if (user.last_updated < datetime.now() - timedelta(minutes=5)):
					state=1
				else:
					state=0
			else:
				state = user.state
			user_list.append({ 'id': user.username, 'state': state, 'name': user.parent().fullname })
	json_dict = {'type' : 'user_list', 'user_list': user_list}
	return json_dict
		
class BaseHandler(webapp2.RequestHandler):
	def render(self, template, **kw):
		self.response.out.write(render_str(template, **kw))
		
	def render_json(self, json_struct):
		json_str = json.dumps(json_struct)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.write(json_str)

	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie',str('%s=%s; Path=/' % (name, cookie_val)))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)
	
	def login(self, username):
		self.set_secure_cookie('user', username)
		
	def logout(self):
		self.response.headers.add_header('Set-Cookie',str(str("user=;Path=/")))
		
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		username = self.read_secure_cookie('user')
		self.curr_user = get_user_by_username(username)

		
class MainPage(BaseHandler):
	def get(self):
		self.redirect('/')
	
class Signup(BaseHandler):

	def get(self):
		username = self.request.get('username')
		self.render("signup-form.html", username=username)

	def post(self):
		have_error = False
		fullname = self.request.get('fullname')
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')

		params = dict(username = username, email = email, fullname = fullname)

		if not fullname:
			params['error_username'] = "Please enter the name you want to be addressed by"
			have_error = True
		
		if not valid_username(username):
			params['error_username'] = "A valid username can be between 3-20 characters only"
			have_error = True
		elif get_user_by_username(username):
			params['error_username'] = "This username is already being used."
			have_error = True

		if not valid_password(password):
			params['error_password'] = "A valid password can be between 3-20 characters only"
			have_error = True
		elif password != verify:
			params['error_verify'] = "Your passwords didn't match. Are you that dumb?"
			have_error = True

		if not valid_email(email):
			params['error_email'] = "Please enter a valid email address."
			have_error = True

		if have_error:
			self.render('signup-form.html', **params)
		else:
			a = User(key_name = username, fullname = fullname, username = username, password = hash_password(password), email = email)
			a.put()
			self.login(username)
			self.redirect('/')

class Signin(BaseHandler):

	def get(self):
		self.render('signin-form.html')
		
	def post(self):
		have_error = False
		username = self.request.get('username')
		password = self.request.get('password')

		params = dict(username = username)
		user = get_user_by_username(username)
		
		if not user:
			params['error_username'] = "This username has not been registered."
			have_error = True

		elif not match_password(username, password, user):
			params['error_password'] = "The password does not match our records."
			have_error = True

		if have_error:
			self.render('signin-form.html', **params)
		else:
			self.login(username)
			self.redirect('/')

class Signout(BaseHandler):
	def get(self):
		self.logout()
		if self.curr_user:
			username = self.curr_user.username
			online_user = Online_User.get_by_key_name(username, parent = self.curr_user) or Online_User(parent = user, key_name = username, username = username)
			online_user.last_updated = datetime.now()
			online_user.last_checked = datetime.now()
			online_user.state = 4
			online_user.put()
		self.redirect('/signin')

import logging
	
class Poll(BaseHandler, Thread):
	def get(self):
		if self.curr_user:
			username = self.curr_user.username
		else:
			username = ""
		user = self.curr_user
		if valid_username(username) and user:
			online_user = Online_User.get_by_key_name(username, parent = self.curr_user) or Online_User(parent = user, key_name = username, username = username)
			current_online_users = Online_User.all().filter("last_updated > ", online_user.last_checked)
			if (current_online_users.count()):
				self.render_json(complete_online_users_list_in_json(self.request.get('search')))
			online_user.last_checked = datetime.now()
			online_user.put()
		
class Welcome(BaseHandler):
	def get(self):
		if self.curr_user:
			username = self.curr_user.username
		else:
			username = ""
		user = self.curr_user
		if valid_username(username) and user:
			self.render('welcome.html', user = user)
		else:
			self.logout()
			self.redirect('/signup')

class BuddyList(BaseHandler):
	def get(self):
		if self.curr_user:
			username = self.curr_user.username
		else:
			username = ""
		user = self.curr_user
		if valid_username(username) and user:
			online_user = Online_User.get_by_key_name(username, parent = self.curr_user) or Online_User(parent = user, key_name = username, username = username)
			online_user.last_updated = datetime.now()
			online_user.last_checked = datetime.now()
			online_user.state=0
			online_user.put()
			self.render_json(complete_online_users_list_in_json(self.request.get('search')))

class Ping(BaseHandler):
	def get(self):
		self.request.get('id')
		
			
class User(db.Model):
	username = db.StringProperty(required = True)
	fullname = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	
class Online_User(db.Model):
	username = db.StringProperty(required = True)
	state = db.IntegerProperty(required = True, default = 0)
	opponent = db.StringProperty()
	last_updated = db.DateTimeProperty()
	last_checked = db.DateTimeProperty()
						
app = webapp2.WSGIApplication([('/', Welcome),	('/signup/?', Signup), ('/signin/?', Signin), ('/signout/?', Signout), ('/buddy_list', BuddyList), ('/pull', Poll), ('/ping', Ping)], debug=True)