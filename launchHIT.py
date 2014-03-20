import uuid
import datetime
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import QuestionContent,Question,QuestionForm,Overview,AnswerSpecification,SelectionAnswer,FormattedContent,FreeTextAnswer,ExternalQuestion

# ACCESS_ID = ''
# SECRET_KEY = ''
# HOST = 'mechanicalturk.sandbox.amazonaws.com'

# mechTurkConn = MTurkConnection(aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY, host=HOST)

def launchHIT(mtc):

  title = 'Draw a single line on a canvas'
  description = ('Draw on a canvas')
  keywords = 'drawing, web'
  choices = [('done','done')]

  #------------------- Overview ---------------------

  overview_content = """<p>Your task is to follow the link and draw a single line segment on a canvas.</p>

  <p>When creating your translation, please follow these guidelines:</p>
  <ul>
      <li><b>Follow the link provided. </b>  <a href="http://distributeddrawing.appspot.com/" target="_blank">Click here</a> </li>
  </ul>
  """

  overview = Overview()
  overview.append_field('Title', 'Draw a line on a canvas in order to complete the task.')
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

  mtc.create_hit(question=questionForm,
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
        #for assignment in assignments:
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
