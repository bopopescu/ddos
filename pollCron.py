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

import main
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
        print 'XXXXX  CRON v6  XXXXX'

        try:
            #if there is anything in reviewableHits, handle it
            reviewableHits = mtc.get_reviewable_hits()
            #from here down, assume that there is a reviewable hit in reviewableHits
            #may run many times (however many lines have been drawn and submitted since last poll)
            for hit in reviewableHits:
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
                    #filter the drawings by hitID (since we're not doing this in the query anymore)
                    if drawing.hitID != hitID: pass

                    #reject the worker if no stroke was added to the image
                    elif drawing.strokeAdded == False:
                        print 'worker did not do work, relaunch hit' #no reason to block, just extra overhead without helping prevent them in future
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
                        #TODO: get list of all strokes with this drawing, and throw out the most recent
                        q = db.GqlQuery("SELECT lines FROM Stroke")
                        strokesList = list(q)
                        sortedStrokesList = sorted(strokesList, key=lambda strokesList: strokesList.datetime)
                        sortedStrokesList.reverse()
                        #for i in xrange(1, len(q)):
                        for stroke in sortedStrokesList:
                            print stroke
                            result = db.delete(stroke)
                            print result
                            break

                        print 'lines deleted'
                        mtc.reject_assignment(ass_id, 'You can only do this job once per drawing')
                        mtc.dispose_hit(hitID)
                        #change
                        newHit = launchHIT(mtc, str(drawing.key()), float(drawing.payment), str(drawing.description))
                        print 'new hit launched'
                        #save over the old hit id with the new one
                        drawing.hitID = newHit[0].HITId
                        drawing.put()
                    #otherwise, approve the work and add that name to the list of blocked
                    else:
                        mtc.approve_assignment(ass_id)
                        mtc.dispose_hit(hitID)
                        drawing.blockedList.append(str(worker_id))
                        #increment the drawing counter and save it
                        drawing.count+=1
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
    ('/polling', Poll),
], debug=True)