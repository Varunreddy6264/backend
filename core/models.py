import secrets
from django.db import models
from django.utils import timezone
class User(models.Model):
 telegram_id=models.BigIntegerField(unique=True,db_index=True)
 username=models.CharField(max_length=100,blank=True); first_name=models.CharField(max_length=100,blank=True); last_name=models.CharField(max_length=100,blank=True); photo_url=models.URLField(blank=True)
 referral_code=models.CharField(max_length=20,unique=True,default="")
 referred_by=models.ForeignKey("self",null=True,blank=True,on_delete=models.SET_NULL,related_name="referrals")
 is_active=models.BooleanField(default=True); total_earned=models.DecimalField(max_digits=18,decimal_places=4,default=0); balance=models.DecimalField(max_digits=18,decimal_places=4,default=0); created_at=models.DateTimeField(auto_now_add=True)
 def save(self,*a,**kw):
  if not self.referral_code:self.referral_code=secrets.token_urlsafe(7)[:10].upper()
  super().save(*a,**kw)
class MiningSession(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="mining_sessions"); rate_per_hour=models.DecimalField(max_digits=12,decimal_places=4); started_at=models.DateTimeField(default=timezone.now); ends_at=models.DateTimeField(); claimed_at=models.DateTimeField(null=True,blank=True); reward_amount=models.DecimalField(max_digits=18,decimal_places=4,default=0); status=models.CharField(max_length=20,default="active")
class Transaction(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="transactions"); tx_type=models.CharField(max_length=30); amount=models.DecimalField(max_digits=18,decimal_places=4); description=models.CharField(max_length=255,blank=True); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: ordering=["-created_at"]
class Task(models.Model):
 title=models.CharField(max_length=120); description=models.TextField(blank=True); reward=models.DecimalField(max_digits=12,decimal_places=4); target_url=models.URLField(blank=True); is_active=models.BooleanField(default=True)
class TaskCompletion(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE); task=models.ForeignKey(Task,on_delete=models.CASCADE); completed_at=models.DateTimeField(auto_now_add=True)
 class Meta: constraints=[models.UniqueConstraint(fields=["user","task"],name="unique_user_task")]
class DailyClaim(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE); claim_date=models.DateField(); reward=models.DecimalField(max_digits=12,decimal_places=4)
 class Meta: constraints=[models.UniqueConstraint(fields=["user","claim_date"],name="unique_daily_claim")]
