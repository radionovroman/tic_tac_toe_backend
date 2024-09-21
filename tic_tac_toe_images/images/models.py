import uuid
from django.db import models
from django.contrib.auth.models import User

class SharedGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_link = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shared Game {self.shared_link} by {self.user.username}"

class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_game = models.ForeignKey(SharedGame, on_delete=models.SET_NULL, null=True, blank=True)
    filename = models.CharField(max_length=100)
    file = models.ImageField(upload_to='uploads/')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.filename
