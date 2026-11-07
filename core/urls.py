from django.urls import path
from .views import Dashboard,StartMining,ClaimMining,Referrals,Tasks,ClaimTask,DailyReward,Leaderboard
urlpatterns=[path('dashboard/',Dashboard.as_view()),path('mining/start/',StartMining.as_view()),path('mining/claim/',ClaimMining.as_view()),path('referrals/',Referrals.as_view()),path('tasks/',Tasks.as_view()),path('tasks/<int:task_id>/claim/',ClaimTask.as_view()),path('rewards/daily/claim/',DailyReward.as_view()),path('leaderboard/',Leaderboard.as_view())]
