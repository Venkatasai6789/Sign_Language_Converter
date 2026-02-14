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
