import requests
import spacy
from datetime import datetime
import logging

nlp = spacy.load("en_core_web_sm")
logger = logging.getLogger(__name__)

API_KEY = 'Ah9iDqJ19JOBkGi8NDLo4A4jODtJl9mN'  
API_ENDPOINT = 'https://api.nytimes.com/svc/topstories/v2/home.json'

def fetch_articles():
    params = {
        'api-key': API_KEY
    }

    try:
        response = requests.get(API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()  
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching articles: {str(e)}")
        raise  

def preprocess_text(text):
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)
