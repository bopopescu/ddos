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

class Drawing(db.Model):
    finished = db.BooleanProperty(default=False)
    # blob = db.BlobProperty() # used to store file picture
    count = db.IntegerProperty(default=0)
    strokeLimit = db.IntegerProperty(default=20)
    blockedList = db.StringListProperty(required=True, default=[])
    hitID = db.StringProperty(default='x')

class Stroke(db.Model):
    counter = db.ReferenceProperty(Drawing)
    lines = db.StringListProperty(required=True)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True)

#------------------------- Request Handlers ----------------------------------#

class Dashboard(webapp2.RequestHandler):
    def get(self):
        '''
        send form for creating new drawing, progess on all other drawings and
        ended jobs for viewing. the form should have a pre-filled field for the drawing id.
        '''
        q = db.GqlQuery("SELECT * FROM Drawing")
        finished = []
        in_progress = []
        for drawing in q:
            if drawing.finished == True:
                # generate/save picture
                finished.append(drawing)
            else:
                in_progress.append(drawing)

        context = {"finished":finished,"in_progress":in_progress}
        template = JINJA_ENVIRONMENT.get_template('dashboard.html')
        self.response.write(template.render(context))

class ViewDrawing(webapp2.RequestHandler):
    def get(self, drawing_id):
        '''
        simple read only view of a drawing (can be ongoing or finished)
        '''
        lines = []
        drawing = db.get(drawing_id)
        q = db.GqlQuery("SELECT lines FROM Stroke WHERE counter=:1 ORDER BY datetime",drawing)
        lines = json.dumps([ast.literal_eval(stroke.lines[0]) for stroke in q])
        context = {"drawing_id":drawing_id,"lines":lines}
        template = JINJA_ENVIRONMENT.get_template('view.html')
        self.response.write(template.render(context))

class NewDrawing(webapp2.RequestHandler):
    def post(self):
        '''
        create new drawing and kick off new HIT chain
        '''
        
        try:
            
            drawing = Drawing()
            strokeLimit = int(self.request.POST[u'strokeLimit'])
            drawing.strokeLimit = strokeLimit
            
            newHit = launchHIT(mtc, str(drawing.key()))
            drawing.hitID = newHit[0].HITId
            drawing.put()
            
        except Exception as ex:
            print 'launch hit failed'
            template = "an exception of type {0} occured. \nArguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message
        
        finally:
            self.redirect('/dashboard')

class DrawingPage(webapp2.RequestHandler):
    def get(self, drawing_id):
        '''
        send the canvas and any other strokes that have been submitted. the
        drawing id corresponds to the specific drawing that the stroke is
        assigned to
        '''
        lines = []
        drawing = db.get(drawing_id)
        q = db.GqlQuery("SELECT lines FROM Stroke WHERE counter=:1 ORDER BY datetime",drawing)
        lines = json.dumps([json.loads(stroke.lines[0]) for stroke in q])

        context = {'lines':lines, 'drawing_id':drawing_id}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

    def post(self, drawing_id):
        '''
        post the new stroke that the turker put on the canvas
        '''

        self.redirect('/thanks', permanent=True)
        drawing = db.get(drawing_id)
        dataSent = json.loads(self.request.body)
        stroke = Stroke()
        stroke.counter = drawing
        #save lines
        for line in dataSent:
            stroke.lines.append(json.dumps(dataSent[line]))
        stroke.put()

class ThanksPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('thanks.html')
        self.response.write(template.render(template_values))

#--------------------------------- Routes ------------------------------------#

app = webapp2.WSGIApplication([
    ('/dashboard', Dashboard),
    ('/new', NewDrawing),
    ('/thanks', ThanksPage),
    ('/view/([^/]+)', ViewDrawing),
    ('/([^/]+)', DrawingPage)
], debug=True)