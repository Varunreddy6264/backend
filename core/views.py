from datetime import timedelta
from decimal import Decimal,ROUND_DOWN
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import User,MiningSession,Transaction,Task,TaskCompletion,DailyClaim
from .telegram_auth import validate_init_data

def current_user(request):
 if settings.DEBUG and request.headers.get("X-Demo-Mode")=="true":
  u,_=User.objects.get_or_create(telegram_id=900000001,defaults={"username":"demo_user","first_name":"Demo"}); return u
 raw=request.headers.get("X-Telegram-Init-Data","")
 if not raw:raise ValidationError("Telegram initData header required")
 tg=validate_init_data(raw)
 u,_=User.objects.get_or_create(telegram_id=int(tg["id"]),defaults={"username":tg.get("username",""),"first_name":tg.get("first_name",""),"last_name":tg.get("last_name",""),"photo_url":tg.get("photo_url","")})
 for field in ["username","first_name","last_name","photo_url"]:setattr(u,field,tg.get(field,getattr(u,field)))
 u.save()
 if not u.is_active:raise ValidationError("Account suspended")
 return u

def user_json(u):
 return {"telegram_id":u.telegram_id,"username":u.username,"first_name":u.first_name,"last_name":u.last_name,"photo_url":u.photo_url,"referral_code":u.referral_code,"balance":str(u.balance),"total_earned":str(u.total_earned),"created_at":u.created_at}
def session_json(s):
 return {"id":s.id,"rate_per_hour":str(s.rate_per_hour),"started_at":s.started_at,"ends_at":s.ends_at,"status":s.status,"reward_amount":str(s.reward_amount)}
class Dashboard(APIView):
 def get(self,r):
  u=current_user(r); s=u.mining_sessions.filter(status="active",claimed_at__isnull=True).order_by("-started_at").first()
  tx=[{"id":x.id,"tx_type":x.tx_type,"amount":str(x.amount),"description":x.description,"created_at":x.created_at} for x in u.transactions.all()[:10]]
  daily_claimed=DailyClaim.objects.filter(user=u,claim_date=timezone.localdate()).exists()
  daily_reward=Decimal("50")+Decimal("10")*DailyClaim.objects.filter(user=u).count()
  return Response({"user":user_json(u),"active_mining":session_json(s) if s else None,"mining_rate_per_hour":settings.MINING_RATE_PER_HOUR,"mining_duration_hours":settings.MINING_DURATION_HOURS,"referral_count":u.referrals.count(),"transactions":tx,"daily_reward":str(daily_reward),"daily_claimed":daily_claimed})
class StartMining(APIView):
 def post(self,r):
  u=current_user(r); now=timezone.now()
  with transaction.atomic():
   active=MiningSession.objects.select_for_update().filter(user=u,status="active",claimed_at__isnull=True).order_by("-started_at").first()
   if active:
    if active.ends_at>now:return Response({"detail":"Mining already active"},status=409)
    return Response({"detail":"Claim the completed mining session before starting the next phase"},status=409)
   s=MiningSession.objects.create(user=u,rate_per_hour=Decimal(str(settings.MINING_RATE_PER_HOUR)),started_at=now,ends_at=now+timedelta(hours=settings.MINING_DURATION_HOURS))
  return Response(session_json(s),status=201)
class ClaimMining(APIView):
 def post(self,r):
  u=current_user(r); now=timezone.now()
  with transaction.atomic():
   s=MiningSession.objects.select_for_update().filter(user=u,status="active",claimed_at__isnull=True).order_by("-started_at").first()
   if not s:raise ValidationError("No unclaimed mining session")
   if now<s.ends_at:raise ValidationError("Mining session is locked until it completes")
   seconds=(s.ends_at-s.started_at).total_seconds()
   reward=(s.rate_per_hour*Decimal(str(seconds/3600))).quantize(Decimal("0.0001"),rounding=ROUND_DOWN)
   if reward<=0:raise ValidationError("No rewards available yet")
   s.reward_amount=reward;s.claimed_at=now;s.status="claimed";s.save()
   u.balance+=reward;u.total_earned+=reward;u.save()
   Transaction.objects.create(user=u,tx_type="mining_reward",amount=reward,description="Mining session reward")
  return Response({"claimed":str(reward),"balance":str(u.balance)})
class Referrals(APIView):
 def get(self,r):
  u=current_user(r);return Response({"referral_code":u.referral_code,"referral_count":u.referrals.count(),"referral_link":f"https://t.me/{__import__('os').getenv('TELEGRAM_BOT_USERNAME','YourNexmineBot')}?start={u.referral_code}"})
class Tasks(APIView):
 def get(self,r):
  u=current_user(r); done=set(TaskCompletion.objects.filter(user=u).values_list("task_id",flat=True)); return Response([{"id":t.id,"title":t.title,"description":t.description,"reward":str(t.reward),"target_url":t.target_url,"completed":t.id in done} for t in Task.objects.filter(is_active=True)])
class ClaimTask(APIView):
 def post(self,r,task_id):
  u=current_user(r)
  with transaction.atomic():
   t=Task.objects.select_for_update().filter(id=task_id,is_active=True).first()
   if not t:raise ValidationError("Task not found")
   if TaskCompletion.objects.filter(user=u,task=t).exists():raise ValidationError("Already claimed")
   # Add actual third-party task verification before enabling social tasks in production.
   TaskCompletion.objects.create(user=u,task=t);u.balance+=t.reward;u.total_earned+=t.reward;u.save()
   Transaction.objects.create(user=u,tx_type="task_reward",amount=t.reward,description=t.title)
  return Response({"claimed":str(t.reward),"balance":str(u.balance)})
class DailyReward(APIView):
 def post(self,r):
  u=current_user(r);today=timezone.localdate();reward=Decimal("50")+Decimal("10")*DailyClaim.objects.filter(user=u).count()
  with transaction.atomic():
   if DailyClaim.objects.filter(user=u,claim_date=today).exists():raise ValidationError("Daily reward already claimed")
   DailyClaim.objects.create(user=u,claim_date=today,reward=reward);u.balance+=reward;u.total_earned+=reward;u.save()
   Transaction.objects.create(user=u,tx_type="daily_reward",amount=reward,description="Daily check-in")
  return Response({"claimed":str(reward),"balance":str(u.balance)})
class Leaderboard(APIView):
 def get(self,r):
  return Response([{"rank":i+1,"username":u.username or u.first_name or "Miner","total_earned":str(u.total_earned)} for i,u in enumerate(User.objects.filter(is_active=True).order_by("-total_earned")[:50])])
