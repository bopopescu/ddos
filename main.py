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
    strokeLimit = db.IntegerProperty(default=20)
    blockedList = db.StringListProperty(required=True)

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
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('dashboard.html')
        self.response.write(template.render(template_values))

class NewDrawing(webapp2.RequestHandler):
    def post(self):
        '''
        create new drawing and kick off new HIT chain
        '''
        print "++++++" + self.request.POST['strokeLimit']
        drawing = Drawing()
        drawing.strokeLimit = int(self.request.POST('strokeLimit'))
        drawing.put()
        key = drawing.key()
        self.redirect('/'+str(key))

class DrawingPage(webapp2.RequestHandler):
    def get(self, drawing_id):
        '''
        send the canvas and any other strokes that have been submitted. the
        drawing id corresponds to the specific drawing that the stroke is
        assigned to
        '''
        lines = []
        drawing = db.get(drawing_id)
        q = drawing.Stroke_set
        # q = db.GqlQuery("SELECT lines FROM Stroke ORDER BY datetime")
        lines = json.dumps([ast.literal_eval(stroke.lines[0]) for stroke in q])

        context = {'lines':lines, 'drawing_id':drawing_id}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

    def post(self, drawing_id):
        '''
        post the new stroke that the turker put on the canvas
        '''
        stroke = Stroke()
        dataSent = json.loads(self.request.body)
        for line in dataSent:
            stroke.lines.append(json.dumps(dataSent[line]))
        stroke.put()
        self.redirect('/thanks', permanent=True)

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
    ('/([^/]+)?', DrawingPage)
], debug=True)