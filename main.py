import json
import ast
import os
import datetime
import time

import jinja2
import webapp2
import logging

import boto
from boto.mturk.connection import MTurkConnection
from boto_wrapper import launchHIT
from google.appengine.ext import db

DEBUG = False

#----------------------------- Config ----------------------------------------#

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

logging.getLogger().setLevel(logging.DEBUG)

#----------------------------- Models ----------------------------------------#

class Drawing(db.Model):
    finished = db.BooleanProperty(default=False, indexed=False)
    # blob = db.BlobProperty() # used to store file picture
    count = db.IntegerProperty(default=0, indexed=False)
    strokeLimit = db.IntegerProperty(default=20, indexed=False)
    blockedList = db.StringListProperty(required=True, default=[], indexed=False)
    hitID = db.StringProperty(default='x', indexed=False)
    strokeAdded = db.BooleanProperty(default=False, indexed=False)
    #added
    payment = db.FloatProperty(default=0.01, indexed=False)
    description = db.StringProperty(default='x', indexed=False)

class Stroke(db.Model):
    counter = db.ReferenceProperty(Drawing, indexed=False)
    lines = db.StringListProperty(required=True, indexed=False)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True, indexed=False)

class StrokeBuffer(db.Model):
    counter = db.ReferenceProperty(Drawing, indexed=False)
    lines = db.StringListProperty(required=True, indexed=False)
    datetime = db.DateTimeProperty(auto_now_add=True, required=True, indexed=False)
    status = db.StringProperty(default="pending approval", indexed=False)

class AMTConfig(db.Model):
    access_id = db.StringProperty(indexed=False)
    secret_key = db.StringProperty(indexed=False)

#----------------------------- MTurk Connection ------------------------------#

ACCESS_ID  = None
SECRET_KEY = None
HOST       = None
KEY        = 'ahRzfmRpc3RyaWJ1dGVkZHJhd2luZ3IWCxIJQU1UQ29uZmlnGICAgICg_YkJDA'
if DEBUG:
    ACCESS_ID  = ''
    SECRET_KEY = ''
    HOST       = 'mechanicalturk.sandbox.amazonaws.com'
else:
    ACCESS_ID  = db.get(KEY).access_id
    SECRET_KEY = db.get(KEY).secret_key
    HOST       = 'mechanicalturk.amazonaws.com'

if not boto.config.has_section('Boto'):
    boto.config.add_section('Boto')
boto.config.set('Boto', 'https_validate_certificates', 'False')

mtc = MTurkConnection(aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY, host=HOST)

#------------------------- Request Handlers ----------------------------------#

class Dashboard(webapp2.RequestHandler):
    def get(self):
        '''
        send form for creating new drawing, progess on all other drawings and
        ended jobs for viewing. the form should have a pre-filled field for the drawing id.
        '''

        #bring in this block to write new secret key and access ID
        '''
        conf = AMTConfig()
        conf.access_id = ACCESS_ID
        conf.secret_key = SECRET_KEY
        conf.put()
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
                #print 'count; ', drawing.count

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
        q = db.GqlQuery("SELECT * FROM Stroke")

        lines = []
        for stroke in q:
            if stroke.counter.key() == drawing.key():
                dt = time.mktime(stroke.datetime.timetuple())*1000
                for line in stroke.lines:
                    l = json.loads(line)
                    l[u'date'] = dt
                    lines.append(l)
        lines = json.dumps(lines)

        context = {"drawing_id":drawing_id,"lines":lines}
        template = JINJA_ENVIRONMENT.get_template('view.html')
        self.response.write(template.render(context))

class Gallery(webapp2.RequestHandler):
    def get(self):
        '''
        gallery view of all finished drawings, mouse over to animate
        '''
        qd = db.GqlQuery("SELECT * FROM Drawing")
        qs = db.GqlQuery("SELECT * FROM Stroke")
        drawings = []
        for d in qd:
            drawing = {}
            lines = []
            for stroke in qs:
                if stroke.counter.key() == d.key():
                    dt = time.mktime(stroke.datetime.timetuple())*1000
                    for line in stroke.lines:
                        l = json.loads(line)
                        l[u'date'] = dt
                        lines.append(l)
            drawing['lines'] = json.dumps(lines)
            drawing['artists'] = d.strokeLimit
            drawing['payment'] = d.payment
            drawing['description'] = d.description
            drawings.append(drawing)

        context = {"drawings":drawings}
        template = JINJA_ENVIRONMENT.get_template('gallery.html')
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
            #added
            payment = float(self.request.POST[u'payment'])
            drawing.payment = payment
            description = str(self.request.POST[u'description'])
            drawing.description = description
            #end added
            drawing.put()

            newHit = launchHIT(mtc, str(drawing.key()), float(drawing.payment), str(drawing.description))
            drawing.hitID = newHit[0].HITId
            drawing.put()

        except Exception as ex:
            print 'launch hit failed'
            template = "an exception of type {0} occured. \nArguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message

        finally:
            self.redirect('/')

class DrawingPage(webapp2.RequestHandler):
    def get(self, drawing_id):
        '''
        send the canvas and any other strokes that have been submitted. the
        drawing id corresponds to the specific drawing that the stroke is
        assigned to
        '''
        lines = []
        drawing = db.get(drawing_id)
        q = db.GqlQuery("SELECT * FROM Stroke")

        lines = []
        for stroke in q:
            if stroke.counter.key() == drawing.key():
                for line in stroke.lines:
                    lines.append(json.loads(line))
        lines = json.dumps(lines)

        context = {'lines':lines, 'drawing_id':drawing_id}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(context))

    def post(self, drawing_id):
        '''
        post the new stroke that the turker put on the canvas
        '''

        #dont need to check if they drew something bec by definition making it here means something was drawn
        self.redirect('/thanks', permanent=True)
        drawing = db.get(drawing_id)
        dataSent = json.loads(self.request.body)

        print 'set stroke added true'
        drawing.strokeAdded = True
        drawing.put()

        strokeBuffer = StrokeBuffer()
        strokeBuffer.counter = drawing
        #strokeBuffer.status is defaulted to "pending approval" bec this is only place strokeBuffer is created
        #save lines
        for line in dataSent:
            strokeBuffer.lines.append(json.dumps(dataSent[line]))
        strokeBuffer.put()

class ThanksPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('thanks.html')
        self.response.write(template.render(template_values))

class Poll(webapp2.RequestHandler):
    def get(self):
        print 'XXXXX  CRON v6  XXXXX'
        try:

            #if there is anything in reviewableHits, handle it
            reviewableHits = mtc.get_reviewable_hits()

            #may run many times (however many lines have been drawn and submitted since last poll)
            for hit in reviewableHits:
                print 'next reviewable hit'
                worker_id = None
                ass_id = None
                hitID = hit.HITId
                assignments = mtc.get_assignments(hit.HITId)
                #only runs once "guaranteed"-ish
                for assignment in assignments:
                    worker_id = assignment.WorkerId
                    ass_id = assignment.AssignmentId
                #get the list of blocked ID's from the datastore
                #query = db.GqlQuery("SELECT * FROM Drawing WHERE hitID = :1", hitID)
                query = db.GqlQuery("SELECT * FROM Drawing")
                #check if the ID of the person awaiting approval is in the list
                for drawing in query:
                    print 'next drawing'
                    #filter the drawings by hitID (since we're not doing this in the query anymore)
                    if drawing.hitID == hitID:
                        print 'found matching drawing for hitID'
                        #reject the worker if no stroke was added to the image
                        if drawing.strokeAdded == False:
                            print 'worker did not do work, relaunch hit' #no reason to block, just extra overhead without helping prevent them in future

                            q = db.GqlQuery("SELECT * FROM StrokeBuffer")
                            for strokeBuffer in q:
                                if strokeBuffer.counter.key() == drawing.key():
                                    if strokeBuffer.status == "pending approval":
                                        strokeBuffer.status = "no line drawn"
                                        strokeBuffer.put()
                                        #db.delete(strokeBuffer)

                            mtc.reject_assignment(ass_id, 'You did not follow directions: you must draw a stroke in order to be paid')
                            mtc.dispose_hit(hitID)

                            newHit = launchHIT(mtc, str(drawing.key()), float(drawing.payment), str(drawing.description))
                            print 'new hit launched'
                            #save over the old hit id with the new one
                            drawing.hitID = newHit[0].HITId
                            drawing.put()

                        #if so, reject
                        elif worker_id in drawing.blockedList:
                            print 'worker is blocked'
                            '''
                            q = db.GqlQuery("SELECT * FROM Stroke")
                            lastTime = datetime.datetime(2000,1,1, 1, 1, 1)
                            lastStroke = None
                            for stroke in q:
                                if stroke.counter.key() == drawing.key():
                                    if stroke.datetime > lastTime:
                                        lastTime = stroke.datetime
                                        lastStroke = stroke

                            lastStroke.removed = True
                            lastStroke.put()
                            result = db.delete(lastStroke)
                            '''
                            q = db.GqlQuery("SELECT * FROM StrokeBuffer")
                            for strokeBuffer in q:
                                if strokeBuffer.counter.key() == drawing.key():
                                    if strokeBuffer.status == "pending approval":
                                        strokeBuffer.status = "rejected"
                                        strokeBuffer.put()
                                        #db.delete(strokeBuffer)

                            print 'lines not added'
                            mtc.reject_assignment(ass_id, 'You can only do this job once per drawing')
                            mtc.dispose_hit(hitID)

                            newHit = launchHIT(mtc, str(drawing.key()), float(drawing.payment), str(drawing.description))
                            print 'new hit launched'
                            #save over the old hit id with the new one
                            drawing.hitID = newHit[0].HITId
                            drawing.strokeAdded = False
                            drawing.put()
                        #otherwise, approve the work and add that name to the list of blocked
                        else:
                            print 'add the buffered line to actual lines'
                            q = db.GqlQuery("SELECT * FROM StrokeBuffer")
                            numStrokesAdded = 0
                            for strokeBuffer in q:
                                if strokeBuffer.counter.key() == drawing.key():
                                    if strokeBuffer.status == "pending approval":
                                        stroke = Stroke()
                                        stroke.counter = strokeBuffer.counter
                                        stroke.lines = strokeBuffer.lines
                                        stroke.datetime = strokeBuffer.datetime
                                        stroke.put()
                                        numStrokesAdded += 1

                                        strokeBuffer.status = "approved"
                                        strokeBuffer.put()
                                        #db.delete(strokeBuffer)

                            print 'approve the work'
                            mtc.approve_assignment(ass_id)
                            mtc.dispose_hit(hitID)
                            drawing.blockedList.append(str(worker_id))
                            #increment the drawing counter and save it
                            drawing.count += numStrokesAdded
                            #if the count of the drawing that person drew to is not done, put out a new HIT
                            if drawing.count < drawing.strokeLimit:
                                print 'count: ', drawing.count
                                print 'limit: ', drawing.strokeLimit
                                newHit = launchHIT(mtc, str(drawing.key()), float(drawing.payment), str(drawing.description))
                                #save over the old hit id with the new one
                                drawing.hitID = newHit[0].HITId
                                print '++++++++++++++++++++++++++++++++++++++launched another'
                            else:
                                print 'drawing finished'
                                drawing.finished = True

                            #save all the new drawing info
                            drawing.strokeAdded = False
                            print 'stroke added false: ', drawing.strokeAdded
                            drawing.put()

        except Exception as ex:
            print 'API call failed!'
            template = "an exception of type {0} occured. arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message


        finally:
            print 'success'

#--------------------------------- Routes ------------------------------------#

app = webapp2.WSGIApplication([
    ('/', Dashboard),
    ('/new', NewDrawing),
    ('/thanks', ThanksPage),
    ('/polling', Poll),
    ('/gallery', Gallery),
    ('/view/([^/]+)', ViewDrawing),
    ('/([^/]+)', DrawingPage)
], debug=True)
