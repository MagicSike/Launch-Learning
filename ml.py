import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def similar_model(name, keyboard_df):
    # preprocessing
    #keyboard_df = pd.read_csv('static\data_site\keyboards.csv', encoding='utf-8-sig', encoding_errors='ignore')
    data_keep = keyboard_df[['product_name', 'product_id', 'product_price','product_type', 'product_color', 'product_top', 'product_brand']]
    
    # construct a reverse mapping of indices and products name and soup feature
    indices = pd.Series(data_keep.index, index=data_keep['product_id']).drop_duplicates()
    data_keep['soup'] = data_keep.apply(create_soup, axis=1)    
    
    # CountVectorizer object 
    count = CountVectorizer(stop_words='english')
    count_matrix = count.fit_transform(data_keep['soup'])

    #Compute the cosine similarity score
    cosine_sim2 = cosine_similarity(count_matrix, count_matrix)

    # get top 5 recommendations
    recommend(name, cosine_sim2, data_keep, indices)
    #joblib.dump(cosine_sim2, 'models_built\checking.joblib')

    return recommend(name, cosine_sim2, data_keep, indices)

def recommend(name, cosine_sim, df, indices):
    # Index of each product
    idx = indices[name]

    # Get the pairwsie similarity scores of products associated with the product
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort based on the cosine similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the 5 most similar products
    sim_scores = sim_scores[1:6]

    # Get the product from the indices
    keyboard_indices = [i[0] for i in sim_scores]
    #keyboard_score = [i[1] for i in sim_scores]
    
    # Return the top 5 most similar 
    recommendations = df['product_id'].iloc[keyboard_indices]

    #print(recommendations)
    #for rec, score in zip(keyboard_score, recommendations):
        #print(rec, score)
    
    return recommendations

def create_soup(x):
    return str(x['product_price']) + ' ' + x['product_type'] + ' ' + str(x['product_color']) + ' ' + str(x['product_top']) + ' ' + x['product_brand']
