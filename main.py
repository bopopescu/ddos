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
import urllib
import cgi
import json

import jinja2
import webapp2

from google.appengine.ext import db
#from boto.mturk.connection import MTurkConnection

#This line taken from google app engine tutorial
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Turker(db.Model): 
    lines = db.StringListProperty(required=True)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True)
    
class BlockedWorkerList(db.Model):
    blockedList = db.StringListProperty(required=True)
    
class DrawingPage(webapp2.RequestHandler):
    def get(self):
        #send list of all lines to JS - make call to database - SELECT * FROM Turkers WHERE id=job# for w/e job# we are on
        # GqlQuery interface constructs a query using a GQL query string
        '''
        q = db.GqlQuery("SELECT * FROM Turker")
        linesJson = q #need to grab just the list of json objects from each line of the q
        '''
        #template_values = {'linesFromDB':linesJson}
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(template_values))

class ThanksPage(webapp2.RequestHandler):
    def post(self):
        self.turker = Turker()
        dataSent = json.loads(self.request.body)
        for line in dataSent:
            self.turker.lines.append(json.dumps(dataSent[line]))
        
        # check here for if the turker id is on the blocked list
            #if not, procede and add to block list, if not return - display err message
        #blocking worker wont help since each hit only has 1 person doing it (blocks only apply to a single hit)
        #instead, just keep a list of the worker id's that are ppl who have worked on any of our HITs.  reject any that are already on the list
        '''
        query = db.GQL()
        blockedIDs = []
        for blockedID in query.BlockedWorkerList:
            blockedIDs.append(blockedID)
        if workerID in blockedIDs:
            #do not write the lines to the server (ie. dont put the turker object)
            #redirect to another page saying they didnt follow directions and wont be paid
            self.redirect('/brokeRules')
        else:
            self.blockedWorkerList = BlockedWorkerList()
            self.blockedWorkerList.blockedList.append(workerID)
            self.blockedWorkerList.put()
        '''
        self.turker.put()
        #self.response.write("Data Recieved in python: wrote to database")
        self.redirect('/thanks')
        
        #kick off next job
        
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('thanks.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', DrawingPage),
    ('/thanks', ThanksPage)
], debug=True)


'''

need to be able to query the DB for all lines, get them as a list, send them to javascript, then redraw them on canvas
if we want to have a branching of multiple drawings spawned from each new line added, need a way to store that info in the DB
need a way to know that they actually drew on the page (like displaying a password on the thanks page that proves they got to it)
need a way to prevent turkers from just drawing a random scribble to be done faster (maybe force them to look at the page for a few seconds before letting them draw, or telling them that
    payment is contingent upon judgement of other turkers that their line added something to the picture
need a way to display the end results in an aesthetically pleasing website (using datetimes to sort)
need to set up boto to deploy staggered jobs that ask for more lines then check if they are good

'''

