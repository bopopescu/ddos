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

class Drawing(db.Model):
    count = db.IntegerProperty(default=0)
    blockedList = db.StringListProperty(required=True)

class Stroke(db.Model):
    counter = db.ReferenceProperty(Drawing)
    lines = db.StringListProperty(required=True)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True)

#------------------------- Request Handlers ----------------------------------#

class Dashboard(webapp2.RequestHandler):
    def get(self):
        '''
        send form for creating new drawing. the form should have a pre-filled
        field for the drawing id.
        '''
        pass

    def post(self):
        '''
        accept the drawing creation form. create a new job and initialize the
        drawing counter
        '''
        pass

class DrawingPage(webapp2.RequestHandler):
    def get(self, drawing_id):
        '''
        send the canvas and any other strokes that have been submitted. the
        drawing id corresponds to the specific drawing that the stroke is
        assigned to
        '''
        lines = []
        q = db.GqlQuery("SELECT lines FROM Stroke ORDER BY datetime")
        lines = json.dumps([ast.literal_eval(stroke.lines[0]) for stroke in q])

        context = {'lines':lines, 'drawing_id':drawing_id}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

    def post(self, drawing_id):
        self.stroke = Stroke()
        dataSent = json.loads(self.request.body)
        for line in dataSent:
            self.stroke.lines.append(json.dumps(dataSent[line]))

        # check here for if the stroke id is on the blocked list
            #if not, procede and add to block list, if not return - display err message
        #blocking worker wont help since each hit only has 1 person doing it (blocks only apply to a single hit)
        #instead, just keep a list of the worker id's that are ppl who have worked on any of our HITs.  reject any that are already on the list
        '''
        query = db.GQL()
        blockedIDs = []
        for blockedID in query.BlockedWorkerList:
            blockedIDs.append(blockedID)
        if workerID in blockedIDs:
            #do not write the lines to the server (ie. dont put the stroke object)
            #redirect to another page saying they didnt follow directions and wont be paid
            self.redirect('/brokeRules')
        else:
            self.blockedWorkerList = BlockedWorkerList()
            self.blockedWorkerList.blockedList.append(workerID)
            self.blockedWorkerList.put()
        '''
        self.stroke.put()
        self.redirect('/thanks')

class ThanksPage(webapp2.RequestHandler):
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
