import uuid
import datetime
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import QuestionContent,Question,QuestionForm,Overview,AnswerSpecification,SelectionAnswer,FormattedContent,FreeTextAnswer,ExternalQuestion

def launchHIT(mtc, drawing_id, payment, title):

  #title = 'Add a single line to this drawing: easy!'
  description = ('We need your help to make the best art possible!')
  keywords = 'drawing, web, art, research, paint, creative, easy, simple, fast'
  choices = [('done','done')]
  drawing_id = "http://distributeddrawing.appspot.com/" + drawing_id
  #------------------- Overview ---------------------
  overview_content = ("<p>Your task is to follow the link and draw a single line stroke in the box shown.  It's Easy! Just left-click in the box and drag your cursor around to create your stroke (just like in MS Paint).</p>"
                      '<p>BUT...try to add something to the picture.  If the square is blank, start off the image with something cool.  If there is already an image going, add something that makes it better.</p>'
                      '<p>Help us make some great drawings!</p>'
                      '<ul>'
                      '<li><b>Get started: </b>  <a href=" ' + drawing_id + '" target="_blank">Click here</a> </li>'
                      '</ul>')


  overview = Overview()
  overview.append_field('Title', 'Draw a line in the box to complete the task.')
  overview.append(FormattedContent( overview_content))

  #------------------- Question test ---------------------

  #urlContent = '<a target="_blank" href="http://www.toforge.com"> Canvas </a>'

  qc1 = QuestionContent()
  qc1.append_field('Title','Click on the submit button once you have finished the task.')
  qc1.append(FormattedContent('The payment will not be authorized if you have not completed the task.'))

  answers = SelectionAnswer(min=1, max=1,style='dropdown',
                        selections=choices,
                        type='text',
                        other=False)

  #question1 = ExternalQuestion(external_url='http://distributeddrawing.appspot.com/',frame_height=400)

  q1 = Question(identifier='task',
                content=qc1,
                answer_spec=AnswerSpecification(answers),
                is_required=True)

  #------------------- Question form creation ---------------------

  questionForm = QuestionForm()
  questionForm.append(overview)
  questionForm.append(q1)

  #------------------- HIT creation ---------------------

  return mtc.create_hit(question=questionForm,
                 max_assignments=1,
                 lifetime=datetime.timedelta(days=1),
                 title=title,
                 description=description,
                 keywords=keywords,
                 duration = 60*5,
                 reward=0.01,
                 response_groups=['Minimal'])


  #hits = mtc.get_reviewable_hits()
  #assignment = mtc.get_assignments(hits.HITId)

def getInfo(mtc):
    hits = mtc.get_reviewable_hits(page_size=100)
    for hit in hits:
        assignments = mtc.get_assignments(hit.HITId)
        #for assignment in assignments:
            #print assignment.WorkerId
            #print assignment.HITId
            #mtc.reject_assignment(assignment.HITId)
        return assignments

def rejectTurker(mtc):
    hits = mtc.get_reviewable_hits(page_size=100)
    turkersInfo = getInfo(mtc)
    for turkerInfo in turkersInfo:
        mtc.reject_assignment(turkerInfo.AssignmentId)
    for hit in hits:
        mtc.dispose_hit(hit.HITId)

def approveTurker(mtc):
    hits = mtc.get_reviewable_hits(page_size=100)
    turkersInfo = getInfo(mtc)
    for turkerInfo in turkersInfo:
        mtc.approve_assignment(turkerInfo.AssignmentId)
    for hit in hits:
            mtc.dispose_hit(hit.HITId)

# if __name__ == "__main__":
    #launchHIT(mechTurkConn)
    #getInfo(mechTurkConn)
    #rejectTurker(mechTurkConn)
    #approveTurker(mechTurkConn)
