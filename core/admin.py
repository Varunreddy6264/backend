from django.contrib import admin
from .models import User,MiningSession,Transaction,Task,TaskCompletion,DailyClaim
admin.site.register(User);admin.site.register(MiningSession);admin.site.register(Transaction);admin.site.register(Task);admin.site.register(TaskCompletion);admin.site.register(DailyClaim)
