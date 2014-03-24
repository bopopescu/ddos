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
        print 'XXXXX  CRON v5  XXXXX'
        
        try:
            #if there is anything in reviewableHits, handle it
            reviewableHits = mtc.get_reviewable_hits()
            print 'here1'
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
                print 'here2'    
                #print 'size: ' + str(len(result))
                #get the list of blocked ID's from the datastore
                query = db.GqlQuery("SELECT * FROM Drawing WHERE hitID = :1", hitID)
                #check if the ID of the person awaiting approval is in the list
                print 'here3'
                for drawing in query:
                    #if so, reject
                    if worker_id in drawing.blockedList:
                        #TODO: get list of all strokes with this drawing, and throw out the most recent
                        query = db.GqlQuery("SELECT lines FROM Stroke WHERE counter=:1 ORDER BY datetime",drawing)
                        lines = json.dumps([ast.literal_eval(stroke.lines[0]) for stroke in q])
                        print lines
                        
                        mtc.reject_assignment(ass_id)
                        mtc.dispose_hit(hitID)
                        print 'here4'
                    #otherwise, approve the work and add that name to the list of blocked
                    else:
                        print 'here3.0'
                        mtc.approve_assignment(ass_id)
                        print 'here3.1'
                        mtc.dispose_hit(hitID)
                        print 'here3.2'
                        drawing.blockedList.append(str(worker_id))  
                        print 'here5'                        
                        #if the count of the drawing that person drew to is not done, put out a new HIT
                        if drawing.count < drawing.strokeLimit:
                            newHit = launchHIT(mtc, str(drawing.key))
                            print 'here6'
                            #save over the old hit id with the new one
                            drawing.hitID = newHit[0].HITId
                            print '++++++++++++++++++++++++++++++++++++++launched another'
                            #increment the drawing counter and save it
                            drawing.count+=1
                        #save all the new drawing info
                        drawing.put()
                        print 'here9'
            
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