from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PPTUpload
from .ai_services import extract_ppt_text, summarize_text, generate_mcq
from .ai_services import extract_ppt_text, summarize_text, generate_mcq
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders


@login_required(login_url="login")
def dashboard_view(request):
    uploads = PPTUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'dashboard.html', {'uploads': uploads})

@login_required(login_url="login")
def upload_ppt_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        ppt_file = request.FILES['file']
        
        # Create DB entry
        upload = PPTUpload.objects.create(
            user=request.user,
            file=ppt_file,
            title=ppt_file.name
        )
        
        # Process PPT (Text Extraction)
        try:
            text = extract_ppt_text(upload.file.path)
            upload.extracted_text = text
            
            # Generate Summary immediately (or could be async)
            summary = summarize_text(text)
            upload.summary_text = summary
            
            upload.save()
            return redirect('summary', session_id=upload.id)
            
        except Exception as e:
            # Handle error (e.g., file format issue)
            print(f"Error processing PPT: {e}")
            # Optional: delete the upload if failed
            return render(request, 'upload_ppt.html', {'error': f'Error processing file: {e}'})
            
    return render(request, 'upload_ppt.html')

@login_required(login_url="login")
def summary_view(request, session_id):
    upload = get_object_or_404(PPTUpload, id=session_id, user=request.user)
    
    
    # Process summary for sign language
    from .ai_services import process_text_for_sign_language
    try:
        sign_words = process_text_for_sign_language(upload.summary_text)
    except Exception as e:
        print(f"Error generating sign language: {e}")
        sign_words = []
    
    return render(request, 'summary.html', {'upload': upload, 'words': sign_words})

@login_required(login_url="login")
def quiz_view(request, session_id):
    upload = get_object_or_404(PPTUpload, id=session_id, user=request.user)
    return render(request, 'quiz.html', {'upload': upload})

@login_required(login_url="login")
def quiz_data_api(request, session_id):
    """
    API endpoint to generate/get quiz data.
    Called via AJAX from quiz.html
    """
    upload = get_object_or_404(PPTUpload, id=session_id, user=request.user)
    
    difficulty = request.GET.get('difficulty', 'Medium')
    num_questions = int(request.GET.get('num_questions', 5))
    
    # We could cache this in the model, but for now let's generate fresh if params change
    # or just simple generation every time for the demo.
    
    questions = generate_mcq(upload.extracted_text, num_questions, difficulty)
    
    return JsonResponse({'questions': questions})

@login_required(login_url="login")
def quiz_submit_view(request, session_id):
    # This might be handled purely frontend with the JSON data, 
    # or we can submit to backend to save score.
    # For this plan, let's just render the results page.
    # For this plan, let's just render the results page.
    return render(request, 'quiz_results.html')

@login_required(login_url="login")
def animation_view(request):
	if request.method == 'POST':
		text = request.POST.get('sen')
		#tokenizing the sentence
		text.lower()
		#tokenizing the sentence
		words = word_tokenize(text)

		tagged = nltk.pos_tag(words)
		tense = {}
		tense["future"] = len([word for word in tagged if word[1] == "MD"])
		tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
		tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
		tense["present_continuous"] = len([word for word in tagged if word[1] in ["VBG"]])



		#stopwords that will be removed
		stop_words = set(["mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its', "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is', 'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's", "needn't", 'd', 'am', 'have',  'hasn', 'o', "aren't", "you'll", "couldn't", "you're", "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself', 'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren', 'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"])



		#removing stopwords and applying lemmatizing nlp process to words
		lr = WordNetLemmatizer()
		filtered_text = []
		for w,p in zip(words,tagged):
			if w not in stop_words:
				if p[1]=='VBG' or p[1]=='VBD' or p[1]=='VBZ' or p[1]=='VBN' or p[1]=='NN':
					filtered_text.append(lr.lemmatize(w,pos='v'))
				elif p[1]=='JJ' or p[1]=='JJR' or p[1]=='JJS'or p[1]=='RBR' or p[1]=='RBS':
					filtered_text.append(lr.lemmatize(w,pos='a'))

				else:
					filtered_text.append(lr.lemmatize(w))


		#adding the specific word to specify tense
		words = filtered_text
		temp=[]
		for w in words:
			if w=='I':
				temp.append('Me')
			else:
				temp.append(w)
		words = temp
		probable_tense = max(tense,key=tense.get)

		if probable_tense == "past" and tense["past"]>=1:
			temp = ["Before"]
			temp = temp + words
			words = temp
		elif probable_tense == "future" and tense["future"]>=1:
			if "Will" not in words:
					temp = ["Will"]
					temp = temp + words
					words = temp
			else:
				pass
		elif probable_tense == "present":
			if tense["present_continuous"]>=1:
				temp = ["Now"]
				temp = temp + words
				words = temp


		filtered_text = []
		for w in words:
			path = w + ".mp4"
			f = finders.find(path)
			#splitting the word if its animation is not present in database
			if not f:
				for c in w:
					filtered_text.append(c)
			#otherwise animation of word
			else:
				filtered_text.append(w)
		words = filtered_text;


		return render(request,'animation.html',{'words':words,'text':text})
	else:
		return render(request,'animation.html')

@login_required(login_url="login")
def history_view(request):
    uploads = PPTUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'history.html', {'uploads': uploads})
