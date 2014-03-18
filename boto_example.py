from boto.mturk.connection import MTurkConnection


mtc = MTurkConnection(aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY, host=HOST)

title = 'Draw a single line on a canvas'
description = ('asdfasdfasdfasdfasdfasdf')
keywords = 'drawing, web'



#------------------- Overview ---------------------
overview = Overview()
overview.append_field('Title', 'Draw a single line on the canvas provided by this website')
overview.append(FormattedContent('URL'))



#------------------- Question form creation ---------------------

questionForm = QuestionForm()
questionFrom.append(overview)

#------------------- HIT creation ---------------------

mtc.create_hit(questions=questionForm,max_assignments=1,title=title,description=description,keywords=keywords,duration=60*5,reward=0.01)