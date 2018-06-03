from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import *
import datetime
import string
import random

# Create your views here.

#CHANGE ALL/NECESSARY TO REDIRECT

def index(request):
    request.session.flush()
    return render(request, 'eval/index.html', {})

def check_eval_pswd(request):
    eval_pswd = request.POST.get("eval-password", 'blank-pswd')
    now = timezone.now()
    session = EvalSession.objects.filter(session_start__lte = now, session_end__gte = now).first()
    if session is None:
        return render(request, 'eval/index.html', {
            'error_message' : "There is currently no class to evaluate",
        })

    if eval_pswd != session.session_eval_pswd:
        return render(request, 'eval/index.html', {
            'error_message' : "Incorrect password",
        })

    request.session['session_id'] = session.pk
    return redirect('/eval-page')


def eval_page(request):
    now = timezone.now()
    session = EvalSession.objects.filter(session_start__lte = now, session_end__gte = now).first()
    return render(request, 'eval/eval-page.html', {
        'session' : session,
    })


def eval_submit(request):
    # Save evaluation to database, make sure they ticked metric, return them if they didnt, etc.

    metric = request.POST.get('class-metric', '')
    comment = request.POST.get('class-comment', '')

    # If no metric ticked, return to eval page with error message
    if not metric:
        return render(request, 'eval/eval-page.html', {
            'error_message' : "You must tick a class metric for your response to be submitted.",
        })

    # If too late to submit (ex. page was open till after session expiration)
    session = EvalSession.objects.get(pk=request.session['session_id'])
    if not session.is_current_session():
        return render(request, 'eval/after-eval.html', {
            'able_to_submit' : False,
        })

    # If all good
    evaluation = Evaluation(eval_session_id=session, class_metric=metric, class_comment=comment)
    evaluation.save()
    return render(request, 'eval/after-eval.html', {
        'able_to_submit' : True,
    })


def prof_login(request):
    context = {}
    if 'error_message' in request.session.keys():
        context['error_message'] = request.session['error_message']

    if 'valid_username' in request.session.keys():
        context['valid_username'] = request.session['valid_username']

    return render(request, 'eval/prof-login.html', context=context)


def check_login(request):
    username = request.POST.get('username', '') # If no username, default='blank-username'
    password = request.POST.get('password', '') # If no password, default='blank-pswd'

    try:
        professor = Professor.objects.get(prof_id=username)
        if password == professor.prof_pswd:
            request.session.flush()
            request.session['prof_id'] = username
            return redirect('/prof-homepage')

    except (KeyError, Professor.DoesNotExist):
        request.session['error_message'] = "Invalid username"
        return redirect('/prof-login')


    request.session['error_message'] = "Password incorrect"
    request.session['valid_username'] = username
    return redirect('/prof-login')


def prof_homepage(request):
    if 'prof_id' not in request.session.keys():
        return redirect('/prof-login')

    if 'error_message' in request.session:
        error_message = request.session['error_message']
        del request.session['error_message']
    else:
        error_message = ""

    if 'confirm_message' in request.session:
        confirm_message = request.session['confirm_message']
        del request.session['confirm_message']
    else:
        confirm_message = ""

    professor = Professor.objects.get(prof_id=request.session['prof_id'])
    courses  = SemesterCourse.objects.filter(prof_id=professor).order_by('-semester_end_date').order_by('course_num')
    now = timezone.now()
    current_session = EvalSession.objects.filter(session_start__lte = now, session_end__gte = now).first()


    return render(request, 'eval/prof-homepage.html', {
        'professor' : professor,
        'courses' : courses,
        'error_message' : error_message,
        'confirm_message' : confirm_message,
        'current_session' : current_session,
        })

def edit_course_action(request):
    course_id = request.POST.get('course-id', '')
    if not course_id:
        return redirect('/prof-homepage')

    request.session['course-id'] = course_id
    if 'edit-course' in request.POST:
        return redirect('/edit-course')
    elif 'delete-course' in request.POST:
        return redirect('/delete-course')
    else:
        return redirect('/prof-homepage')


def add_course(request):
    return render(request, 'eval/add-course.html', {})


def submit_add_course(request):
    course_num = request.POST.get('course-number')
    semester = request.POST.get('semester')
    year = request.POST.get('year')
    semester_start = request.POST.get('semester-start')
    semester_end = request.POST.get('semester-end')
    max_num_meeting_times = request.POST.get('max-meeting-time')

    if semester_start > semester_end:
        request.session['error_message'] = "Course information incomplete. New course not saved."
        return redirect('/prof-homepage')

    new_course = SemesterCourse()

    new_course.prof_id = Professor.objects.get(pk=request.session['prof_id'])
    new_course.course_num = course_num
    new_course.semester = semester
    new_course.year = year
    new_course.semester_start_date = semester_start
    new_course.semester_end_date = semester_end
    new_course.full_clean()
    new_course.save()

    # creating weekly meeting times, and storing them to DB
    for i in range(1, int(max_num_meeting_times)+1):
        day = request.POST.get("day-"+str(i))
        start_time = request.POST.get("start-time-"+str(i))
        end_time = request.POST.get("end-time-"+str(i))
        if day and start_time and end_time:
            eval_time = SemesterCourseEvalTime(semester_course_id=new_course, day_of_week=day, start_time=start_time, end_time=end_time)
            if (eval_time.start_time < eval_time.end_time):
                eval_time.full_clean()
                eval_time.save()

    # From the weekly times, creating evalation sessions automatically
    weekly_eval_times = SemesterCourseEvalTime.objects.filter(semester_course_id=new_course)
    for weekly_time in weekly_eval_times:
        diff_of_days  = weekly_time.day_of_week - new_course.semester_start_date.weekday()
        if diff_of_days < 0:
            diff_of_days += 7
        eval_day = new_course.semester_start_date + datetime.timedelta(days=diff_of_days)
        while eval_day <= new_course.semester_end_date:
            session_start = timezone.make_aware(datetime.datetime.combine(eval_day, weekly_time.start_time))
            session_end = timezone.make_aware(datetime.datetime.combine(eval_day, weekly_time.end_time))
            session_pswd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            eval_session = EvalSession(semester_course_id = new_course, session_start=session_start,
                                       session_end=session_end, session_eval_pswd=session_pswd)
            eval_session.full_clean()
            eval_session.save()
            eval_day += datetime.timedelta(days=7)


    request.session['confirm_message'] = "A new course has been added successfully"
    return redirect('/prof-homepage')


def edit_course(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    weekly_eval_times = SemesterCourseEvalTime.objects.filter(semester_course_id=course)
    days_of_week = [("Sunday", 6),
                    ("Monday", 0),
                    ("Tuesday", 1),
                    ("Wednesday", 2),
                    ("Thursday", 3),
                    ("Friday", 4),
                    ("Saturday", 5)
                    ]

    return render(request, 'eval/edit-course.html', {
        'course' : course,
        'semesters' : ['Fall', 'January', 'Spring', 'Summer'],
        'semester_start_date' : course.semester_start_date.strftime('%Y-%m-%d'),
        'semester_end_date' : course.semester_end_date.strftime('%Y-%m-%d'),
        'weekly_eval_times' : weekly_eval_times,
        'days_of_week' : days_of_week,

    })

def submit_edit_course(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    del request.session['course-id']

    course_num = request.POST.get('course-number')
    semester = request.POST.get('semester')
    year = request.POST.get('year')
    semester_start_date = request.POST.get('semester-start')
    semester_end_date = request.POST.get('semester-end')
    max_num_meeting_times = request.POST.get('max-meeting-time')

    if not (course_num and semester and year and semester_start_date and semester_end_date):
        request.session['error_message'] = "Course information incomplete. Changes not saved."
        return redirect('/prof-homepage')

    if semester_start_date > semester_end_date:
        request.session['error_message'] = "Course information incomplete. New course not saved."
        return redirect('/prof-homepage')

    course.course_num = course_num
    course.semester = semester
    course.year = year
    course.semester_start_date = semester_start_date
    course.semester_end_date = semester_end_date
    course.full_clean()
    course.save()

    # Getting rid of old weekly evaluation times
    old_eval_times = SemesterCourseEvalTime.objects.filter(semester_course_id=course)
    for old_time in old_eval_times:
        old_time.delete()

    # Replacing with new weekly evalation times
    for i in range(1, int(max_num_meeting_times)+1):
        day = request.POST.get("day-"+str(i), "")
        start_time = request.POST.get("start-time-"+str(i), "")
        end_time = request.POST.get("end-time-"+str(i), "")

        if day and start_time and end_time:
            eval_time = SemesterCourseEvalTime(semester_course_id=course, day_of_week=day, start_time=start_time, end_time=end_time)
            if (eval_time.start_time < eval_time.end_time):
                eval_time.full_clean()
                eval_time.save()

    # Deleting upcoming eval sessions that were based on old weekly meeting times
    now = timezone.now()
    old_upcoming_eval_sessions = EvalSession.objects.filter(semester_course_id=course, session_start__gte=now)
    for old_upcoming_session in old_upcoming_eval_sessions:
        old_upcoming_session.delete()

    weekly_eval_times = SemesterCourseEvalTime.objects.filter(semester_course_id=course)
    for weekly_time in weekly_eval_times:
        diff_of_days  = weekly_time.day_of_week - timezone.now().weekday()
        if diff_of_days < 0:
            diff_of_days += 7
        eval_day = timezone.now() + datetime.timedelta(days=diff_of_days)
        while eval_day.date() <= course.semester_end_date:
            session_start = timezone.make_aware(datetime.datetime.combine(eval_day, weekly_time.start_time))
            session_end = timezone.make_aware(datetime.datetime.combine(eval_day, weekly_time.end_time))
            session_pswd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            eval_session = EvalSession(semester_course_id=course, session_start=session_start,
                                       session_end=session_end, session_eval_pswd=session_pswd)
            eval_session.full_clean()
            eval_session.save()
            eval_day += datetime.timedelta(days=7)


    request.session['confirm_message'] = "Your changes have been saved."
    return redirect('/prof-homepage')


def delete_course(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    weekly_eval_times = SemesterCourseEvalTime.objects.filter(semester_course_id=course)
    days_of_week = [("Sunday", 6),
                    ("Monday", 0),
                    ("Tuesday", 1),
                    ("Wednesday", 2),
                    ("Thursday", 3),
                    ("Friday", 4),
                    ("Saturday", 5)
                    ]

    return render(request, 'eval/delete-course.html', {
        'course' : course,
        'semesters' : ['Fall', 'January', 'Spring', 'Summer'],
        'semester_start_date' : course.semester_start_date.strftime('%Y-%m-%d'),
        'semester_end_date' : course.semester_end_date.strftime('%Y-%m-%d'),
        'weekly_eval_times' : weekly_eval_times,
        'days_of_week' : days_of_week,
    })


def submit_delete_course(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    del request.session['course-id']

    course.delete()

    return redirect('/prof-homepage')




def course_sessions(request):
    course_id = request.POST.get('course-id')
    if not course_id:
        course_id = request.session.get('course-id')
        if not course_id:
            return redirect('/prof-homepage')

    request.session['course-id'] = course_id
    course = SemesterCourse.objects.get(pk=course_id)
    sessions = EvalSession.objects.filter(semester_course_id=course).order_by('session_end')
    days_of_week = [("Sunday", 6),
                    ("Monday", 0),
                    ("Tuesday", 1),
                    ("Wednesday", 2),
                    ("Thursday", 3),
                    ("Friday", 4),
                    ("Saturday", 5)
                    ]
    return render(request, 'eval/course-sessions.html', {
        'sessions' : sessions,
        'days_of_week' : days_of_week,

    })

def add_session(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    random_pswd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return render(request, 'eval/add-session.html', {
        'course' : course,
        'random_pswd' : random_pswd,

    })

def submit_add_session(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])

    session_start = request.POST.get('session-start')
    session_end = request.POST.get('session-end')
    session_pswd = request.POST.get('session-pswd')
    if not session_pswd:
        session_pswd = request.POST.get('input-pswd')

    if not session_pswd:
        return redirect('/course-sessions')

    session = EvalSession(semester_course_id=course, session_start=session_start,
                          session_end=session_end, session_eval_pswd=session_pswd)
    session.full_clean()
    session.session_start = timezone.make_aware(session.session_start)
    session.session_end = timezone.make_aware(session.session_end)
    session.save()
    return redirect('/course-sessions')


def edit_session_action(request):
    session_id = request.POST.get('session-id', '')
    if not session_id:
        return redirect('/course-sessions')

    request.session['session-id'] = session_id
    if 'edit-session' in request.POST:
        return redirect('/edit-session')
    elif 'delete-session' in request.POST:
        return redirect('/delete-session')
    else:
        return redirect('/course-sessions')


def edit_session(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    session = EvalSession.objects.get(pk=request.session['session-id'])
    new_rand_pswd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    return render(request, 'eval/edit-session.html', {
        'course' : course,
        'session' : session,
        'new_rand_pswd' : new_rand_pswd,

    })


def submit_edit_session(request):
    session = EvalSession.objects.get(pk=request.session['session-id'])
    session_start = request.POST.get('session-start')
    session_end = request.POST.get('session-end')
    session_pswd = request.POST.get('session-pswd')
    if not session_pswd:
        session_pswd = request.POST.get('input-pswd')
        if not session_pswd:
            session_pswd  = session.session_eval_pswd

    session.session_start = session_start
    session.session_end = session_end
    session.session_eval_pswd = session_pswd
    session.full_clean()
    session.session_start = timezone.make_aware(session.session_start)
    session.session_end = timezone.make_aware(session.session_end)
    session.save()
    return redirect('/course-sessions')


def delete_session(request):
    course = SemesterCourse.objects.get(pk=request.session['course-id'])
    session = EvalSession.objects.get(pk=request.session['session-id'])
    num_evals = len(Evaluation.objects.filter(eval_session_id=session))

    return render(request, 'eval/delete-session.html', {
        'course' : course,
        'session' : session,
        'num_evals' : num_evals,

    })


def submit_delete_session(request):
    session = EvalSession.objects.get(pk=request.session['session-id'])
    session.delete()
    return redirect('/course-sessions')

def choose_report(request):
    course_id = request.POST.get('course-id')
    request.session['course-id'] = course_id
    if not course_id:
        return redirect('/prof-homepage')

    if 'one-session-choose' in request.POST:
        return redirect('/one-session-choose')
    elif 'all-sessions-report' in request.POST:
        return redirect('/all-sessions-report')
    elif 'two-sessions-choose' in request.POST:
        return redirect('/two-sessions-choose')

    return redirect('/prof-homepage')


def one_session_choose(request):
    sessions = EvalSession.objects.filter(semester_course_id=request.session['course-id']).order_by('session_end')
    days_of_week = [("Sunday", 6),
                    ("Monday", 0),
                    ("Tuesday", 1),
                    ("Wednesday", 2),
                    ("Thursday", 3),
                    ("Friday", 4),
                    ("Saturday", 5)
                    ]
    return render(request, 'eval/one-session-choose.html', {
        'sessions' : sessions,
        'days_of_week' : days_of_week,
    })


def one_session_report(request):
    session = EvalSession.objects.get(pk=request.POST.get('session-id'))
    if not session:
        return redirect('/prof-homepage')

    evals = Evaluation.objects.filter(eval_session_id=session)

    eval_great = evals.filter(class_metric="Great")
    eval_good = evals.filter(class_metric="Good")
    eval_neutral = evals.filter(class_metric="Neutral")
    eval_bad = evals.filter(class_metric="Bad")
    eval_very_bad = evals.filter(class_metric="Very Bad")

    return render(request, 'eval/one-session-report.html', {
        'session' : session,
        'eval_great' : eval_great,
        'eval_good' : eval_good,
        'eval_neutral' : eval_neutral,
        'eval_bad' : eval_bad,
        'eval_very_bad' : eval_very_bad,

    })

def all_sessions_report(request):
    course_id = request.session['course-id']
    course = SemesterCourse.objects.get(pk=course_id)
    if not course:
        return redirect('/prof-homepage')

    sessions = EvalSession.objects.filter(semester_course_id=course)
    evals = Evaluation.objects.filter(eval_session_id__in=sessions)

    eval_great = evals.filter(class_metric="Great").order_by("eval_session_id__session_start")
    eval_good = evals.filter(class_metric="Good").order_by("eval_session_id__session_start")
    eval_neutral = evals.filter(class_metric="Neutral").order_by("eval_session_id__session_start")
    eval_bad = evals.filter(class_metric="Bad").order_by("eval_session_id__session_start")
    eval_very_bad = evals.filter(class_metric="Very Bad").order_by("eval_session_id__session_start")

    return render(request, 'eval/all-sessions-report.html', {
        'course' : course,
        'eval_great' : eval_great,
        'eval_good' : eval_good,
        'eval_neutral' : eval_neutral,
        'eval_bad' : eval_bad,
        'eval_very_bad' : eval_very_bad,
        'now' : timezone.now().date(),

    })


def two_sessions_choose(request):
    sessions = EvalSession.objects.filter(semester_course_id=request.session['course-id']).order_by('session_end')
    days_of_week = [("Sunday", 6),
                    ("Monday", 0),
                    ("Tuesday", 1),
                    ("Wednesday", 2),
                    ("Thursday", 3),
                    ("Friday", 4),
                    ("Saturday", 5)
                    ]
    return render(request, 'eval/two-sessions-choose.html', {
        'sessions' : sessions,
        'days_of_week' : days_of_week,
    })

def two_sessions_report(request):
    multiple_sessions = request.POST.getlist('session-id')
    if len(multiple_sessions) < 2:
        return redirect('/prof-homepage')

    session1 = EvalSession.objects.get(pk=multiple_sessions[0])
    session2 = EvalSession.objects.get(pk=multiple_sessions[1])
    if not (session1 and session2):
        return redirect('/prof-homepage')

    evals1 = Evaluation.objects.filter(eval_session_id=session1)
    evals2 = Evaluation.objects.filter(eval_session_id=session2)

    eval_great1 = evals1.filter(class_metric="Great")
    eval_good1 = evals1.filter(class_metric="Good")
    eval_neutral1 = evals1.filter(class_metric="Neutral")
    eval_bad1 = evals1.filter(class_metric="Bad")
    eval_very_bad1 = evals1.filter(class_metric="Very Bad")

    eval_great2 = evals2.filter(class_metric="Great")
    eval_good2 = evals2.filter(class_metric="Good")
    eval_neutral2 = evals2.filter(class_metric="Neutral")
    eval_bad2 = evals2.filter(class_metric="Bad")
    eval_very_bad2 = evals2.filter(class_metric="Very Bad")

    return render(request, 'eval/two-sessions-report.html', {
        'session1' : session1,
        'session2' : session2,

        'eval_great1' : eval_great1,
        'eval_good1' : eval_good1,
        'eval_neutral1' : eval_neutral1,
        'eval_bad1' : eval_bad1,
        'eval_very_bad1' : eval_very_bad1,

        'eval_great2' : eval_great2,
        'eval_good2' : eval_good2,
        'eval_neutral2' : eval_neutral2,
        'eval_bad2' : eval_bad2,
        'eval_very_bad2' : eval_very_bad2,

    })
