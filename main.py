import os
import urllib
import cgi
import json
import ast

import jinja2
import webapp2

from google.appengine.ext import db
#from boto.mturk.connection import MTurkConnection

#----------------------------- Config ----------------------------------------#

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#----------------------------- Models ----------------------------------------#

class DrawingCounter(db.Model):
    count = db.IntegerProperty(default=0)

class Turker(db.Model):
    counter = db.ReferenceProperty(DrawingCounter)
    lines = db.StringListProperty(required=True)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True)

class BlockedWorkerList(db.Model):
    blockedList = db.StringListProperty(required=True)

#------------------------- Request Handlers ----------------------------------#

class Dashboard(webapp2.RequestHandler):
    def get(self):
        pass

class DrawingPage(webapp2.RequestHandler):
    def get(self, id):
        '''
        q = db.GqlQuery("SELECT * FROM Turker")
        linesJson = q #need to grab just the list of json objects from each line of the q
        '''
        lines = []
        q = db.GqlQuery("SELECT lines FROM Turker ORDER BY datetime")
        lines = json.dumps([ast.literal_eval(turker.lines[0]) for turker in q])

        context = {'lines':lines}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

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
        self.redirect('/thanks')

        #kick off next job

    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('thanks.html')
        self.response.write(template.render(template_values))

#--------------------------------- Routes ------------------------------------#

app = webapp2.WSGIApplication([
    ('/dashboard', Dashboard),
    ('/(\d+)', DrawingPage),
    ('/thanks', ThanksPage)
], debug=True)