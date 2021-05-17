from openTSNE import TSNE
import numpy as np
from sklearn.model_selection import train_test_split

import gzip
import pickle

# on importe le module Doc2Vec de la librairie gensim (a installer mais depend de numpu et spicy)
from gensim.models.doc2vec import Doc2Vec

def create_tsne_embedding(modelFile):
    model = Doc2Vec.load(modelFile)
    list = []
    for i in range(model.docvecs.count):
        list.append(model.docvecs[i])
    X = np.array(list)
    #X = model[model.wv.vocab]
    X_embedded = TSNE(n_components=2).fit(X)
    return X_embedded

def generate_embedding_vector(modelFile, aes):
    """
    Genere un vecteur qui sera new_embedding dans create_new_vector
    """
    # on charge un modele
    model = Doc2Vec.load(modelFile)
    # la methode infer_vector genere un embedding a partir d'un texte decoupe en une liste de 'tokens'
    vector = model.infer_vector(aes.split())
    vector = vector.reshape(1, -1)
    return vector

def create_new_vector(tsne_embedding, new_embedding):
    #embedding new points into an existing embedding
    return tsne_embedding.transform(new_embedding)