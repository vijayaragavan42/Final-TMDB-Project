import streamlit as st
import mysql.connector
import pandas as pd
from pathlib import Path 

st.set_page_config(
page_title="Movie Analysis Dashboard",
layout="wide"
)

st.title("🎬 Movie Analysis Dashboard")
st.write("Welcome to my Movie Analysis Project!")

@st.cache_data
def load_movies():
    connection = mysql.connector.connect(
host="localhost",
user="root",
password="Vijay@0204",
database="movie_analysis"
)

    try:
        query = "SELECT * FROM movies_cleaned"
        df = pd.read_sql_query(query,connection)
        return df

    finally:
        connection.close()
try:
    df = load_movies()

    # Prepare release year
    df["release_year"] = pd.to_datetime(
        df["release_date"],
        errors="coerce"
    ).dt.year


    st.header("Movie Filters")

    # Sidebar filters
    st.sidebar.header("Filter Movies")

    # Language filter
    languages = sorted(
        df["original_language"].dropna().unique().tolist()
    )

    selected_languages = st.sidebar.multiselect(
        "Select Language",
        languages
    )

    # Release year filter
    valid_years = df["release_year"].dropna()

    if not valid_years.empty:
        min_year = int(valid_years.min())
        max_year = int(valid_years.max())

        if min_year < max_year:
            selected_years = st.sidebar.slider(
                "Select Release Year Range",
                min_year,
                max_year,
                (min_year, max_year)
            )
        else:
            selected_years = (min_year, max_year)
            st.sidebar.write("Release year:", min_year)
    else:
        selected_years = None
        st.sidebar.warning("No valid release years found.")

    # Minimum rating filter
    min_rating = st.sidebar.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5
    )

    # Apply filters
    filtered_df = df.copy()

    if selected_languages:
        filtered_df = filtered_df[
            filtered_df["original_language"].isin(
                selected_languages
            )
        ]

    if selected_years is not None:
        filtered_df = filtered_df[
            filtered_df["release_year"].between(
                selected_years[0],
                selected_years[1]
            )
        ]

    filtered_df = filtered_df[
        filtered_df["vote_average"].fillna(0) >= min_rating
    ]

    # Display results
    st.subheader("Filtered Movie Results")

    st.metric("Movies Matching Filters", len(filtered_df))

    st.dataframe(
        filtered_df,
        use_container_width=True
    )
    st.divider()

    st.header("Movie Dashboard")

    # KPI Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Movies", len(filtered_df))

    with col2:
        st.metric(
            "Average Rating",
            round(filtered_df["vote_average"].mean(), 2)
        )

    with col3:
        st.metric(
            "Total Revenue",
            f"${filtered_df['revenue'].sum():,.0f}"
        )

    # Top 10 Movies by Revenue
    st.subheader("Top 10 Movies by Revenue")

    top_movies = filtered_df.nlargest(10, "revenue")

    st.bar_chart(
        top_movies.set_index("title")["revenue"]
    )

    # Budget vs Revenue
    st.subheader("Budget vs Revenue")

    chart_df = filtered_df[
        (filtered_df["budget"] > 0) &
        (filtered_df["revenue"] > 0)
    ]

    st.scatter_chart(
        chart_df,
        x="budget",
        y="revenue",
        x_label="Budget",
        y_label="Revenue"
    )
    # =================================
    # PAGE 3: QUERY EXPLORER
    # =================================

    st.divider()

    st.header("Query Explorer")

    st.write(
        "Explore your movie database using saved SQL queries."
    )

    # Save 10 SQL questions
    saved_queries = {
        "1. List all movies in the Action genre released after 2015, showing title and release date.": """
            SELECT
    m.title,
    m.release_date
FROM movies_cleaned AS m
JOIN movie_genres_cleaned AS mg
    ON m.movie_id = mg.movie_id
JOIN genres_cleaned AS g
    ON mg.genre_id = g.genre_id
WHERE g.genre_name = 'Action'
  AND m.release_date >= '2016-01-01'
ORDER BY m.release_date;
        """,

        "2.Find the top 10 highest-grossing movies along with the genre(s) each belongs to.": """
            SELECT
    m.title,
    m.revenue,
    g.genre_name
FROM movies_cleaned AS m
JOIN movie_genres_cleaned AS mg
    ON m.movie_id = mg.movie_id
JOIN genres_cleaned AS g
    ON mg.genre_id = g.genre_id
WHERE m.revenue > 0
ORDER BY m.revenue DESC
LIMIT 10;
""",

        "3. Calculate the average budget and average revenue for each genre, sorted by average revenue descending.": """
           SELECT
g.genre_name,
ROUND(AVG(m.budget), 2) AS average_budget,
ROUND(AVG(m.revenue), 2) AS average_revenue
FROM movies_cleaned AS m
JOIN movie_genres_cleaned AS mg
ON m.movie_id = mg.movie_id
JOIN genres_cleaned AS g
ON mg.genre_id = g.genre_id
WHERE m.budget > 0
AND m.revenue > 0
GROUP BY g.genre_name
ORDER BY average_revenue DESC; SELECT title, vote_average, vote_count
            FROM movies_cleaned
            WHERE vote_count >= 100
            ORDER BY vote_average DESC
            LIMIT 10
        """,

        "4.List the top 10 actors who have appeared in the most movies in the dataset.(cast)": """
         SELECT
c.actor_name,
COUNT(DISTINCT c.movie_id) AS movie_count
FROM caste_cleaned AS c
GROUP BY c.person_id, c.actor_name
ORDER BY movie_count DESC
LIMIT 10;
        """,

        "5. Find all directors who have directed more than 3 movies, along with their movie count.": """
            SELECT
    person_name AS director_name,
    COUNT(DISTINCT movie_id) AS movie_count
FROM crew_cleaned
WHERE job = 'Director'
GROUP BY person_name
HAVING COUNT(DISTINCT movie_id) > 3
ORDER BY movie_count DESC;

        """,

        "6. List the top 10 most frequently used keywords across all movies.": """
            SELECT
k.keyword_name,
COUNT(DISTINCT mk.movie_id) AS movie_count
FROM movie_keywords_cleaned AS mk
JOIN movie_keywords_cleaned AS k
ON mk.keyword_id = k.keyword_id
GROUP BY k.keyword_id, k.keyword_name
ORDER BY movie_count DESC
LIMIT 10;
        """,

        "7. Find movies where the budget was above the overall average budget but the revenue was below the overall average revenue.": """
           SELECT
title,
budget,
revenue
FROM movies_cleaned
WHERE budget > (
SELECT AVG(budget)
FROM movies_cleaned
WHERE budget > 0
)
AND revenue < (
SELECT AVG(revenue)
FROM movies_cleaned
WHERE revenue > 0
)
AND budget > 0
AND revenue > 0
ORDER BY budget DESC;
        """,

        "8. List all actors who have appeared in a movie directed by a specific director (e.g., Christopher Nolan).Highest Budget Movies": """
            SELECT DISTINCT
c.actor_name,
m.title AS movie_title
FROM caste_cleaned AS c
JOIN movies_cleaned AS m
ON c.movie_id = m.movie_id
JOIN crew_cleaned AS cr
ON m.movie_id = cr.movie_id
WHERE cr.job = 'Director'
AND cr.person_name = 'Christopher Nolan'
ORDER BY m.title, c.actor_name;
        """,

        "9. Find the genre with the highest average rating, considering only genres with at least 20 movies.": """
            SELECT
g.genre_name,
ROUND(AVG(m.vote_average), 2) AS average_rating,
COUNT(DISTINCT m.movie_id) AS movie_count
FROM movies_cleaned AS m
JOIN movie_genres_cleaned AS mg
ON m.movie_id = mg.movie_id
JOIN genres_cleaned AS g
ON mg.genre_id = g.genre_id
WHERE m.vote_average IS NOT NULL
GROUP BY g.genre_id, g.genre_name
HAVING COUNT(DISTINCT m.movie_id) >= 20
ORDER BY average_rating DESC
LIMIT 20;
        """,

        "10. List the top 10 movies with the highest number of keywords tagged to them.": """
            SELECT
m.title,
COUNT(DISTINCT mk.keyword_id) AS keyword_count
FROM movies_cleaned AS m
JOIN movie_keywords_cleaned AS mk
ON m.movie_id = mk.movie_id
GROUP BY m.movie_id, m.title
ORDER BY keyword_count DESC, m.title ASC
LIMIT 10;
        """
    }

    # Query selection
    selected_query = st.selectbox(
        "Select a SQL Question",
        list(saved_queries.keys())
    )

    # Display selected SQL
    with st.expander("View SQL Query"):
        st.code(
            saved_queries[selected_query],
            language="sql"
        )

    # Run query
    if selected_query:

        connection = None

        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Vijay@0204",
                database="movie_analysis"
            )

            result_df = pd.read_sql_query(
                saved_queries[selected_query],
                connection
            )

            st.subheader("Query Results")

            st.dataframe(
                result_df,
                use_container_width=True
            )

            st.success(
                f"Query completed! "
                f"{len(result_df)} rows returned."
            )

            # Automatic insight
            st.subheader("Insight")
            
            if result_df.empty:
                st.info("No results found for this query.")

        
            else:
                st.write(
                    f"This query returned {len(result_df)} rows. "
                    "Review the table and chart to understand "
                    "the results."
                )
        except Exception as e:
           st.error("Unable to load movie data.")
           st.error(str(e))

    
finally:
            if connection is not None and connection.is_connected():
                connection.close()


