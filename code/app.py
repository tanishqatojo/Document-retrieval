import os
import json
import time
import threading
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import redis
import logging
from datetime import datetime
from requests.exceptions import RequestException
from data import fetch_articles, preprocess_text

app = Flask(__name__)

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')

es = Elasticsearch([f'http://{ELASTICSEARCH_HOST}:9200'])
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_and_index_documents():
    articles = fetch_articles()
    processed_docs = []
    for article in articles:
        doc_id = article.get('url')
        if not es.exists(index="news_articles", id=doc_id):
            processed_doc = {
                'id': doc_id,
                'title': article.get('title'),
                'author': ', '.join(article.get('byline', '').split(',')[:2]),
                'published_date': article.get('published_date'),
                'source': 'The New York Times',
                'content': preprocess_text(article.get('abstract', '')),
                'url': article.get('url'),
                'section': article.get('section'),
                'subsection': article.get('subsection'),
                'keywords': article.get('des_facet', []),
            }
            processed_docs.append(processed_doc)
            es.index(index="news_articles", id=doc_id, body=processed_doc)
    return processed_docs

def check_index():
    try:
        index_stats = es.indices.stats(index="news_articles")
        doc_count = index_stats['indices']['news_articles']['total']['docs']['count']
        print(f"Number of documents in the index: {doc_count}")
    except Exception as e:
        print(f"Error checking index: {str(e)}")

def search_documents(query, top_k=10, threshold=0.5):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "content^2", "keywords^2", "section", "subsection"],
                "type": "best_fields",
                "tie_breaker": 0.3,
                "minimum_should_match": "30%"
            }
        },
        "size": top_k
    }
    
    print(f"Searching with query: {query}, top_k: {top_k}, threshold: {threshold}")
    results = es.search(index="news_articles", body=body)
    
    print(f"Total hits: {results['hits']['total']['value']}")
    
    filtered_results = []
    for hit in results['hits']['hits']:
        print(f"Score: {hit['_score']}, Title: {hit['_source'].get('title', 'No title')}")
        if hit['_score'] > threshold:
            document = hit['_source']
            document['score'] = hit['_score']
            filtered_results.append(document)
    
    print(f"Filtered results: {len(filtered_results)}")
    return filtered_results

def search_documents_with_cache(query, top_k=10, threshold=0.5):
    cache_key = f"search:{query}:{top_k}:{threshold}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        logger.info("Returning cached result")
        return json.loads(cached_result)
    
    results = search_documents(query, top_k, threshold)

    redis_client.setex(cache_key, 1200, json.dumps(results))
    
    return results

def background_scraper():
    while True:
        logger.info("Starting background scraping")
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    processed_articles = process_and_index_documents()
                    logger.info(f"Indexed {len(processed_articles)} new articles")
                    break  
                except RequestException as e:
                    if attempt < max_retries - 1:  
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in 60 seconds...")
                        time.sleep(30)
                    else:
                        raise  
        except Exception as e:
            logger.error(f"Error in background scraping: {str(e)}")
        
        logger.info("Sleeping for 1 hour before next scrape")
        time.sleep(1200)
def index_documents():
    processed_articles = process_and_index_documents()
    logger.info(f"Initially indexed {len(processed_articles)} documents")

@app.route('/health')
def health_check():
    try:
        es.info()
        redis_client.ping()
        return jsonify({"status": "healthy", "elasticsearch": "connected", "redis": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/search')
def search():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user_requests = redis_client.incr(f"user:{user_id}:requests")
    redis_client.expire(f"user:{user_id}:requests", 1200)
    if user_requests > 5:
        return jsonify({"error": "Rate limit exceeded"}), 429

    query = request.args.get('text', '')
    top_k = int(request.args.get('top_k', 10))
    threshold = float(request.args.get('threshold', 0.5))

    if not query:
        return jsonify({"error": "Search text is required"}), 400

    start_time = time.time()
    results = search_documents_with_cache(query, top_k, threshold)
    end_time = time.time()

    response = {
        "results": results,
        "query": query,
        "top_k": top_k,
        "threshold": threshold,
        "search_time": end_time - start_time
    }

    logger.info(f"Search completed in {end_time - start_time} seconds")

    return jsonify(response)

@app.route('/keywords')
def get_keywords():
    body = {
        "size": 0,
        "aggs": {
            "keywords": {
                "terms": {
                    "field": "keywords",
                    "size": 100
                }
            }
        }
    }
    results = es.search(index="news_articles", body=body)
    keywords = [bucket['key'] for bucket in results['aggregations']['keywords']['buckets']]
    return jsonify(keywords)

if __name__ == '__main__':
    scraper_thread = threading.Thread(target=background_scraper)
    scraper_thread.daemon = True
    scraper_thread.start()
    index_documents()
    check_index()

    app.run(debug=True)
