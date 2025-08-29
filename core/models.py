from django.db import models
class OAuthToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class Lock(models.Model):
    name = models.CharField(max_length=100, unique=True)
    acquired_at = models.DateTimeField(auto_now_add=True)
