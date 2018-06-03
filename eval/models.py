from django.db import models
from django.utils import timezone

# Create your models here.

class Professor(models.Model):
    prof_id = models.CharField(max_length=15, primary_key=True)
    prof_pswd = models.CharField(max_length=30)
    first_name = models.CharField(max_length=20, default="")
    last_name = models.CharField(max_length=30, default="")

    def __str__(self):
        return self.first_name + " " + self.last_name + "(" + self.prof_id + ")"


class SemesterCourse(models.Model):
    course_num = models.CharField(max_length=20)
    prof_id = models.ForeignKey(Professor, null=True, on_delete=models.SET_NULL)
    year = models.IntegerField()
    semester = models.CharField(max_length=20)
    semester_start_date = models.DateField()
    semester_end_date = models.DateField()

    def __str__(self):
        return self.course_num + " (" + self.semester + " " + str(self.year) + ")"

class SemesterCourseEvalTime(models.Model):
    semester_course_id = models.ForeignKey(SemesterCourse, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()


class EvalSession(models.Model):
    semester_course_id = models.ForeignKey(SemesterCourse, on_delete=models.CASCADE)
    session_start = models.DateTimeField()
    session_end = models.DateTimeField()
    session_eval_pswd = models.CharField(max_length=15, default='')

    def __str__(self):
        return str(self.semester_course_id) + ' - ' + str(self.session_start.date())

    def is_current_session(self):
        return self.session_start < timezone.now() < self.session_end


class Evaluation(models.Model):
    eval_session_id = models.ForeignKey(EvalSession, on_delete=models.CASCADE)
    class_metric = models.CharField(max_length=15, blank=False)
    class_comment = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.class_metric + " - " + str(self.eval_session_id)
