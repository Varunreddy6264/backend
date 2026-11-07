import hashlib,hmac,json,time
from urllib.parse import parse_qsl
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
def validate_init_data(raw):
 if not settings.TELEGRAM_BOT_TOKEN: raise AuthenticationFailed("Bot token not configured")
 try:
  values=dict(parse_qsl(raw,keep_blank_values=True)); received=values.pop("hash")
 except Exception: raise AuthenticationFailed("Malformed Telegram initData")
 check="\n".join(f"{k}={v}" for k,v in sorted(values.items()))
 secret=hmac.new(b"WebAppData",settings.TELEGRAM_BOT_TOKEN.encode(),hashlib.sha256).digest()
 actual=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
 if not hmac.compare_digest(actual,received): raise AuthenticationFailed("Invalid Telegram signature")
 try:
  auth_date=int(values.get("auth_date", "0"))
  if not auth_date or abs(time.time()-auth_date)>86400: raise AuthenticationFailed("Telegram initData expired")
  return json.loads(values["user"])
 except Exception:raise AuthenticationFailed("Telegram user missing")
