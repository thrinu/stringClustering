from __future__ import print_function
import pickle
import json
import codecs
import sys
import operator
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from WordsToNumbers import *
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.externals import joblib

from scipy.cluster.hierarchy import ward, dendrogram

def split_words_in_text(text):
    split = list()
    split = sentence_to_word_array(text, True, False, True)

    if len(split) > 0:
        return split

    split.append(text.lower())

    return split

# graph = open('myGraph.txt', 'r')
# graph = json.load(graph)
# names = [n['Name'] for n in graph]

parser = argparse.ArgumentParser(description='Cluster a text file with a list of strings')
parser.add_argument('filename', metavar='FILENAME',
                    help='File name with extention that contains the list of strings')

parser.add_argument('--maxC', dest='maxC', type=float, default=0.3,
                    help='add a max commonality parameter for the vectorizer. (default: 0.3). Larger commonality groups things into bigger/more generic clusters')

parser.add_argument('--minC', dest='minC', type=float, default=0.001,
                    help='add a min commonality parameter for the vectorizer. (default: 0.001). Larger commonality eliminates more noise, but may miss some specific clusters.')

parser.add_argument('--clusters', dest='clusterCount', type=int, default=50,
                    help='Number of clusters to create (default: 50)')

parser.add_argument('--out', dest='outputfile', default="a.out", help='output file name')

args = parser.parse_args()

filename = args.filename
max_commonality = args.maxC
min_commonality = args.minC
num_clusters = args.clusterCount
output_file_name = args.outputfile
output_file = {}

results = {}

if output_file_name:
    output_file = open(output_file_name, 'w')

names = []
infile = codecs.open(filename, encoding='utf-8')
for line in infile:
    names.append(line.strip())
infile.close()

# names_split = [(split_words_in_text(n)) for n in names]
# print(names_split)

print("vectorizing...")
tfidf_vectorizer = TfidfVectorizer(max_df=max_commonality, max_features=200000,
                                 min_df=min_commonality, tokenizer=split_words_in_text,
                                 use_idf=True, ngram_range=(1, 3))
                                 

tfidf_matrix = tfidf_vectorizer.fit_transform(names)  # fit the vectorizer to synopses

print(tfidf_matrix.shape)

terms = tfidf_vectorizer.get_feature_names()
if output_file:
    results["terms_used_to_cluster"] = terms
print(terms)
print()
print()

tfidf_vectorizer2 = TfidfVectorizer(max_df=0.9999, max_features=200000,
                                 min_df=max_commonality, tokenizer=split_words_in_text,
                                 use_idf=True, ngram_range=(1, 3))

tfidf_matrix2 = tfidf_vectorizer2.fit_transform(names)  # fit the vectorizer to synopses
excluded_terms = tfidf_vectorizer2.get_feature_names()
if output_file:
    results["excluded_terms"] = excluded_terms
print(excluded_terms)
print()
print()

dist = 1 - cosine_similarity(tfidf_matrix)

km = KMeans(n_clusters=num_clusters)
km.fit(tfidf_matrix)
clusters = km.labels_.tolist()

# uncomment the below to save your model
# since I've already run my model I am loading from the pickle
# joblib.dump(km,  'doc_cluster.pkl')
# km = joblib.load('doc_cluster.pkl')

names = {'names': names, 'cluster': clusters}
frame = pd.DataFrame(names, index=[clusters])

frame['cluster'].value_counts()
order_centroids = km.cluster_centers_.argsort()[:, ::-1]

groups = frame.groupby('cluster')

clusters = []
all_tags = dict()
for name, group in groups:

    result_group = {}
    values = group.values[:,1]
    tags = dict()
    for v in values:
        split_value = split_words_in_text(v)
        for sv in split_value:
            if sv in tags:
                tags[sv] = tags[sv] + 1
            else:
                if sv not in excluded_terms and len(sv) > 1:
                    tags[sv] = 1

    sorted_tags = reversed(sorted(tags.items(), key=operator.itemgetter(1)))
    important_tags = list()
    threshold = 2

    i = 0
    for t in sorted_tags:
        i += 1
        important_tags.append(t[0])
        if i > threshold:
            break

    for tag in important_tags:
        if tag in all_tags:
            all_tags[tag].extend(values)
        else:
            all_tags[tag] = list()
            all_tags[tag].extend(values)

    print(len(values))
    print(values)
    if output_file:
        result_group["values"] = list(values)

    clusters.append(result_group)
print("----------------------------------------------------------")

results["clusters"] = clusters

print(all_tags.keys())
if output_file:
    results["tags"] = all_tags
    output_file.write(json.dumps(results))