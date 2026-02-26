from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import PPTUpload
import json
from unittest.mock import patch

class StudyCompanionTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password123')
        # Ensure profile exists (in case signal failed or race condition)
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=self.user)

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
            reverse('quiz_data_api', args=[self.ppt_upload.id]),
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
        """Test animation tool loads (protected view)"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('animation'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_view(self):
        """Test quiz interface loads"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('quiz', args=[self.ppt_upload.id]))
        self.assertEqual(response.status_code, 200)
        
    @patch('study_companion.views.generate_mcq')
    def test_quiz_api(self, mock_generate_mcq):
        """Test quiz data API returns JSON questions"""
        # Mock result — generate_mcq returns a parsed list, not a JSON string
        mock_generate_mcq.return_value = [
            {
                "question": "Test Q1",
                "options": ["A", "B", "C", "D"],
                "answer": "A"
            }
        ]
        
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('quiz_data_api', args=[self.ppt_upload.id]) + '?num_questions=1&difficulty=Easy')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('questions' in data)
        self.assertTrue(isinstance(data['questions'], list))
        self.assertEqual(len(data['questions']), 1)
        self.assertEqual(data['questions'][0]['question'], "Test Q1")

    def test_ppt_upload_model(self):
        """Test model data integrity"""
        upload = PPTUpload.objects.get(title="Test Presentation")
        self.assertEqual(upload.user.username, 'testuser')
        self.assertEqual(upload.extracted_text, "This is a test extracted text.")
        self.assertTrue(upload.file.name.endswith('.pptx'))

    def test_quiz_save_result(self):
        """Test saving quiz results via API"""
        self.client.login(username='testuser', password='password123')
        url = reverse('quiz_save_result', args=[self.ppt_upload.id])
        data = {
            'score': 4,
            'total': 5,
            'time_taken': '01:30'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['xp_earned'], 40)
        
        # Verify db content
        from .models import QuizResult, UserProfile
        result = QuizResult.objects.filter(user=self.user, upload=self.ppt_upload).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 4)
        
        # Verify profile update
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.total_xp, 40)
        self.assertEqual(profile.current_streak, 1)
