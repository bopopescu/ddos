import os
import urllib
import cgi
import json
import ast
import uuid
import datetime

import jinja2
import webapp2
import logging

import boto
from boto.mturk.connection import MTurkConnection
from launchHIT import launchHIT, rejectTurker, approveTurker
from google.appengine.ext import db
#----------------------------- MTurk Connection ------------------------------#

ACCESS_ID = ''
SECRET_KEY = ''
HOST = 'mechanicalturk.sandbox.amazonaws.com'

if not boto.config.has_section('Boto'):
    boto.config.add_section('Boto')
boto.config.set('Boto', 'https_validate_certificates', 'False')

mtc = MTurkConnection(aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY, host=HOST)

#----------------------------- Config ----------------------------------------#

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

logging.getLogger().setLevel(logging.DEBUG)

#----------------------------- Models ----------------------------------------#
class Poll(webapp2.RequestHandler):
    def get(self): 
        print 'XXXXX  CRON v4  XXXXX'
        
        try:
            #if the HIT is waiting for review, the call will succeed and continue (if 0 results, it will throw exception and do nothing
            reviewableHits = mtc.get_reviewable_hits()
            #from here down, assume that there is a reviewable hit in reviewableHits
            print 'size: ' + str(len(result))
            #get the list of blocked ID's from the datastore
            #check if the ID of the person awaiting approval is in the list
            #if so, reject
            #otherwise, approve the work and add that name to the list of blocked
            #put the list back in datastore
            #if the count of the drawing that person drew to is not done, put out a new HIT
            #increment the drawing counter and save it

        except Exception as e:
            print 'API call failed!'
        
        finally:
            pass
            print 'success'


#--------------------------------- Routes ------------------------------------#

app = webapp2.WSGIApplication([
    ('/polling', Poll),
], debug=True)