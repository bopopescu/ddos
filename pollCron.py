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

ACCESS_ID = 'AKIAJGYLVFH5HSDGHVZQ'
SECRET_KEY = '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'
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
        #check if the HIT is submitted (do HTTP get request)
        #if not, do nothing
        #if it is:
            #get the list of blocked ID's from the datastore
            #check if the ID of the person awaiting approval is in the list
            #if so, reject
            #otherwise, approve the work and add that name to the list of blocked
            #put the list back in datastore
            #if the count of the drawing that person drew to is not done, put out a new HIT
            #increment the drawing counter and save it
        #delete this hit
            
        print 'XXXXX  CRON v3  XXXXX'
        
        try:
            result = mtc.get_reviewable_hits()
            print 'size: ' + str(len(result))
            print result[0]

        except Exception as e:
            print 'API call failed!'
        
        finally:
            pass
            print 'success'
            #if data != []:
                #return json.loads(data)


#--------------------------------- Routes ------------------------------------#

app = webapp2.WSGIApplication([
    ('/polling', Poll),
], debug=True)