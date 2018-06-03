from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Professor)
admin.site.register(SemesterCourse)
admin.site.register(SemesterCourseEvalTime)
admin.site.register(EvalSession)
admin.site.register(Evaluation)
