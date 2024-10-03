import pickle
import streamlit as st
import pandas as pd
import requests
from functools import lru_cache
import numpy as np

st.set_page_config(layout="wide")

# Custom CSS to style links
st.markdown("""
    <style>
    a {
        color: #FF6347 !important; /* Tomato color for links */
        text-decoration: none !important; /* Remove underline */
        font-weight: bold;
    }
    a:hover {
        color: #FFA07A !important; /* Light Salmon color on hover */
        text-decoration: underline !important; /* Add underline on hover */
    }
    </style>
    """, unsafe_allow_html=True)

# Load data
@st.cache_resource
def load_data():
    with open('movielist.pkl', 'rb') as file:
        movies = pd.read_pickle(file)
    with open('cosine_sim1.pkl', 'rb') as file:
        sim1 = pd.read_pickle(file)
    with open('cosine_sim2.pkl', 'rb') as file:
        sim2 = pd.read_pickle(file)
    with open('cosine_sim3.pkl', 'rb') as file:
        sim3 = pd.read_pickle(file)
    similarity = np.concatenate((sim1, sim2, sim3), axis=0)
    return movies, similarity

movies, similarity = load_data()

# Fetch movie poster and details
@lru_cache(maxsize=1000)
def fetch_movie_details(movie_id):
    try:
        api_key = st.secrets["tmdb_api_key"]
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}')
        response.raise_for_status()
        data = response.json()
        return {
            'poster_url': f'https://image.tmdb.org/t/p/w500{data["poster_path"]}',
            'imdb_id': data['imdb_id'],
            'release_year': data['release_date'][:4],
            'genres': ', '.join([genre['name'] for genre in data['genres']])
        }
    except requests.RequestException as e:
        st.error(f"Error fetching movie details: {e}")
        return None

# Recommend movies
def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        recommended_movies = []
        for i in distances[1:9]:
            movie_id = movies.iloc[i[0]]['movie_id']
            details = fetch_movie_details(movie_id)
            if details:
                recommended_movies.append({
                    'title': movies.iloc[i[0]]['title'],
                    'poster': details['poster_url'],
                    'imdb_id': details['imdb_id'],
                    'year': details['release_year'],
                    'genres': details['genres']
                })
        return recommended_movies
    except IndexError:
        st.error("Movie not found in database.")
        return []

# UI
st.title('Movie Recommender System')

movie_list = movies['title'].values
selected = st.selectbox('Select or type a movie to get recommendations', movie_list)

if selected:
    with st.spinner('Fetching recommendations...'):
        selected_movie_id = movies[movies['title'] == selected]['movie_id'].values[0]
        selected_movie_details = fetch_movie_details(selected_movie_id)
        recommendations = recommend(selected)
    
    if selected_movie_details:
        st.subheader(f'Selected Movie: [{selected}](https://www.imdb.com/title/{selected_movie_details["imdb_id"]})')
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(selected_movie_details['poster_url'], use_column_width=True)
        with col2:
            st.write(f"**Release Year:** {selected_movie_details['release_year']}")
            st.write(f"**Genres:** {selected_movie_details['genres']}")
    
    if recommendations:
        st.subheader('Recommended Movies')
        cols = st.columns(4)
        for i, movie in enumerate(recommendations):
            with cols[i % 4]:
                st.markdown(f"##### [{movie['title']} ({movie['year']})](https://www.imdb.com/title/{movie['imdb_id']})")
                st.markdown(f"[![Poster]({movie['poster']})](https://www.imdb.com/title/{movie['imdb_id']})")
                st.caption(f"Genres: {movie['genres']}")
    else:
        st.warning("No recommendations found.")

# Footer
st.markdown("---")
st.markdown("Data provided by [The Movie Database (TMDb)](https://www.themoviedb.org)")