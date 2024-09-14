# Document Retrieval System

## Overview
This project implements a robust document retrieval system using Python, Flask, Elasticsearch, and Redis. It's designed to efficiently fetch, process, index, and search articles from the New York Times API, demonstrating key concepts in information retrieval and system design.

## Key Features
- Real-time article fetching and indexing
- Efficient full-text search capabilities
- Caching mechanism for improved performance
- Background scraping for continuous data updates
- Dockerized application for easy deployment and scaling

## Technology Stack
- **Flask**: Lightweight web framework for the API
- **Elasticsearch**: Powerful search and analytics engine
- **Redis**: In-memory data structure store used for caching
- **Docker**: Containerization for consistent development and deployment environments

## System Architecture

### 1. Data Fetching and Processing (`data.py`)
- Fetches articles from the New York Times API
- Preprocesses text data for optimal indexing

### 2. Core Application (`app.py`)
- Implements the Flask web server
- Manages connections to Elasticsearch and Redis
- Handles article indexing and search operations

### 3. Caching Layer (Redis)
- Caches search results to reduce load on Elasticsearch
- Implements a simple rate limiting mechanism

### 4. Search Engine (Elasticsearch)
- Indexes processed articles
- Performs full-text search with relevance scoring

### 5. Background Scraper
- Continuously fetches and indexes new articles
- Runs in a separate thread to avoid blocking the main application

## Key Design Decisions and Rationale

### 1. Caching Strategy
We implemented caching using Redis for several reasons:
- **Improved Response Time**: Frequently requested search results are served from cache, significantly reducing response times.
- **Reduced Load**: Caching minimizes the number of queries to Elasticsearch, reducing the load on the search engine.
- **Scalability**: Redis can easily scale to handle increased load, making our system more robust.

### 2. Background Scraping
The decision to implement background scraping was based on:
- **Real-time Updates**: Ensures the index is continuously updated with the latest articles.
- **Improved User Experience**: Users always have access to the most recent content without manual updates.
- **Efficient Resource Usage**: By running in a separate thread, it doesn't interfere with the main application's performance.

### 3. Elasticsearch for Full-text Search
Elasticsearch was chosen for its:
- **Powerful Full-text Search**: Provides advanced search capabilities out of the box.
- **Scalability**: Can handle large volumes of data and concurrent searches efficiently.
- **Rich Querying**: Supports complex queries and relevance scoring.

### 4. Dockerization
The application is containerized using Docker for:
- **Consistency**: Ensures the application runs the same way in every environment.
- **Easy Deployment**: Simplifies the deployment process across different platforms.
- **Scalability**: Makes it easier to scale individual components of the system.

### 5. Logging
Comprehensive logging is implemented to:
- **Facilitate Debugging**: Helps in identifying and resolving issues quickly.
- **Monitor Performance**: Provides insights into system performance and bottlenecks.
- **Track Usage**: Helps in understanding how the system is being used.

## Future Enhancements
- Implement more advanced NLP techniques for improved search relevance
- Add user authentication and personalized search features
- Implement a more sophisticated caching strategy (e.g., cache invalidation based on content updates)
- Develop a user-friendly front-end interface

## API Documentation
1. Health Check
- **URL**: `/health`
2. Search
- **URL**: `/search`
3. Keywords
- **URL**: `/keywords`
### Rate Limiting
The API implements rate limiting to prevent abuse. Each user (identified by `user_id`) is limited to 5 requests per hour.

### Error Handling
The API returns appropriate HTTP status codes and error messages:
- 400 Bad Request: When required parameters are missing
- 429 Too Many Requests: When rate limit is exceeded
- 500 Internal Server Error: For server-side errors


