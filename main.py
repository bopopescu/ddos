import os
import urllib
import cgi
import json
import ast

import jinja2
import webapp2

import logging

from google.appengine.ext import db

#----------------------------- Config ----------------------------------------#

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
    
logging.getLogger().setLevel(logging.DEBUG)

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
        drawing.strokeLimit = int(self.request.POST['strokeLimit'])
        drawing.put()
        key = drawing.key()
        self.redirect('/'+str(key))
    
    def get(self):
        drawing = Drawing()
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
        #drawing = db.get(drawing_id)
        #logging.debug(drawing_id)
        #q = drawing.Stroke_set
        q = db.GqlQuery("SELECT lines FROM Stroke WHERE counter = KEY('Stroke', :1) ORDER BY datetime", drawing_id)
        lines = json.dumps([ast.literal_eval(stroke.lines[0]) for stroke in q])

        context = {'lines':lines, 'drawing_id':drawing_id}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

    def post(self, drawing_id):
        stroke = Stroke()
        dataSent = json.loads(self.request.body)
        redirectString = "/thanks"

        query = db.GqlQuery("SELECT * FROM Drawing WHERE __key__ = KEY('Drawing', :1)", drawing_id)
        
        #there will always be only 1 drawing in query but this is the best way to access it
        for drawing in query:
            # need to check here if the turker has already done one for this drawing
            if dataSent['turkerID'] in drawing.blockedList:
                #reject the turker - do not approve 
                
                #maybe redirect page to some kind of err for them?
                #redirectString = "/errPage"
                pass
            else:
                #approve job
                
                #add to blocked list
                drawing.blockedList.append(dataSent['turkerID'])
                #one step closer to finishing this drawing
                drawing.count += 1
                drawing.put()
                #save lines
                for line in dataSent['lines']:
                    stroke.lines.append(json.dumps(dataSent['lines'][line]))
                stroke.put()
                
                #if drawing.count < this drawing's limit, then deploy another job
                if drawing.count < drawing.limit:
                    #boto code here to deploy next hit
                    pass
            
        #go to thanks page
        self.redirect(redirectString, permanent=True)


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