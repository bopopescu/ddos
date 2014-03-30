ddos | Distributed Drawing of Strokes
=====================================
* Thomas Klingshirn, Eduardo Cirilo, Garrett Listi
* live site: http://distributeddrawing.appspot.com/dashboard

To Test/Deploy
--------------
This application was built using the Google App Engine SDK. Using the latest SDK:
* change the DEBUG flag at line 16 of main.py to TRUE
* insert your AMT credentials on lines 63 & 64
* change the HOST flag to be mechanicalturk.sandbox.amazonaws.com or mechanicalturk.amazonaws.com
* deploy to your own GAE instance at https://appengine.google.com/

Once deployed:
* navigate to /dashboard
* enter a desired stroke limit, HIT title, and payment per HIT

After creating the drawing on the dashboard, the HIT chain will begin. The drawing will be viewable throughout the process. Once the drawing has been completed, it will move to the Completed Drawings table, and be viewable in the Gallery. 

Mousing over the canvas in both the gallery and the individual views will trigger an animated drawing of the strokes in the order they were submited. Mousing out will return the canvas to the drawing's finished state. 

Proposal
========

Motivation
----------
This project takes uses an aggregation of turkers collaborative drawing abilities by bringing them together for a single image.  We believe it to be interesting to see how complex and original a drawing with many different artists can be.

Goal
----
The goal is to generate a single drawing from many different collaborators.  We expect to create a version-controlled drawing application.

Design rationale
----------------
Turkers working on our HITs will require literally no skill; all they have to do is draw a single line. We aren’t worried about quality, but to avoid confusion on the turker’s end, we will provide explicit instruction for the task that they are to perform. Also to make sure that our results are somewhat valid, after a set number of strokes on the canvas, we will aggregate a vote to either keep or remove certain strokes (in order to prevent trolls).

How do you plan to build it?
----------------------------
Using HTML5’s canvas and JavaScript, we will create a webpage where turkers will only be allowed to draw a single stroke on a canvas. We will then store every stroke created by the different turkers in the order that each stroke was drawn. These strokes will then be aggregated as a time lapse showcasing the evolution of the canvas. 
