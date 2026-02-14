from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import PPTUpload
import json

class StudyCompanionTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        
        # Create a sample PPT upload
        # Fix: Provide a file using SimpleUploadedFile
        self.ppt_upload = PPTUpload.objects.create(
            user=self.user,
            title="Test Presentation",
            file=SimpleUploadedFile("test.pptx", b"dummy content"),
            extracted_text="This is a test extracted text.",
            summary_text="This is a test summary."
        )

    def test_login_required_views(self):
        """Test that views require login"""
        protected_urls = [
            reverse('dashboard'),
            reverse('summary', args=[self.ppt_upload.id]),
            reverse('quiz', args=[self.ppt_upload.id]),
            reverse('quiz_api', args=[self.ppt_upload.id]),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 200)
            self.assertEqual(response.status_code, 302) # Redirects to login
            # Check if redirects to login page
            self.assertTrue('/login' in response.url or '/accounts/login' in response.url)

    def test_dashboard_view(self):
        """Test dashboard loads for logged in user"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Presentation")

    def test_upload_ppt_view_get(self):
        """Test upload page loads"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)

    def test_summary_view(self):
        """Test summary page loads with correct context"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('summary', args=[self.ppt_upload.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This is a test summary.")

    def test_animation_view(self):
        """Test animation tool loads (public view)"""
        response = self.client.get(reverse('animation'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_view(self):
        """Test quiz interface loads"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('quiz', args=[self.ppt_upload.id]))
        self.assertEqual(response.status_code, 200)
        
    def test_quiz_api(self):
        """Test quiz data API returns JSON questions"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('quiz_data_api', args=[self.ppt_upload.id]) + '?num_questions=3&difficulty=Easy')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('questions' in data)
        self.assertTrue(isinstance(data['questions'], list))

    def test_ppt_upload_model(self):
        """Test model data integrity"""
        upload = PPTUpload.objects.get(title="Test Presentation")
        self.assertEqual(upload.user.username, 'testuser')
        self.assertEqual(upload.extracted_text, "This is a test extracted text.")
        self.assertTrue(upload.file.name.endswith('.pptx'))
