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

        q = db.GqlQuery("SELECT blockedList FROM Drawing")
        
        #check if there is no drawing object yet (this is the first person being blocked for this drawing
        if not q:
            self.drawing = Drawing()
            self.drawing.blockedList.append(dataSent['turkerID'])
            self.drawing.put()
            self.redirect('/thanks')
        else:
            for drawing in q:
                if dataSent['turkerID'] in drawing.blockedList:
                    #reject the turker - do not approve 
                    #redirect page to some kind of err for them
                    self.redirect('/thanks')
                else:
                    #approve job
                    #add to blocked list
                    drawing.blockedList.append(dataSent['turkerID'])
                    drawing.put()
                    #save lines
                    for line in dataSent['lines']:
                        self.stroke.lines.append(json.dumps(dataSent['lines'][line]))
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
