from django.db import models
from django.contrib.auth.models import User

class PPTUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='ppt_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)
    
    # Store processed data to avoid re-running AI expensive calls
    extracted_text = models.TextField(blank=True, null=True)
    summary_text = models.TextField(blank=True, null=True)
    
    # Store generated quiz as JSON
    quiz_data = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload = models.ForeignKey(PPTUpload, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    time_taken = models.CharField(max_length=10)  # "MM:SS"
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.upload.title} - {self.score}/{self.total}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    total_xp = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except:
        pass
