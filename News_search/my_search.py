import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import pymorphy2
import gensim.downloader as download_api
from sklearn.feature_extraction.text import TfidfVectorizer
import itertools
import pickle


class Document:
    def __init__(self, title, text, id):
        self.title = title
        self.text = text
        self.id = id
    
    def format(self, query):
        return [self.title, self.text + ' ...']



def get_word_info(word):
    p = morph.parse(word)[0]
    normal = p.normal_form
    pos = p.tag.POS
    if pos:
        if 'ADJ' in pos:
            pos1 = 'ADJ'
            return (normal, pos1)
    return (normal, pos)


def upd_str(text, stem=True):
    text = text.lower()
    words = re.findall(r'\w+', text)
    filter_words = list(filter(lambda x: x not in stop_words, words))
    if filter_words:
        if stem:
            new = list(map(lambda x: snowball.stem(x), filter_words))
            return ' '.join(new)
        new = list(map(lambda x: get_word_info(x), filter_words))
        print(new)
        return new
    return ''


def build_index():
    global index, Y, TF_IDF_vocab, russian_model, documents, stop_words, snowball, valid_types, morph, k1, k2

    with open('inv_index.pkl', 'rb') as file:
        index = pickle.load(file)

    with open('TF_IDF.pkl', 'rb') as file:
        Y = pickle.load(file)

    with open('TF_IDF_vocab.pkl', 'rb') as file:
        TF_IDF_vocab = pickle.load(file)  

    with open('documents.pkl', 'rb') as file:
        documents = pickle.load(file) 

    russian_model = download_api.load('word2vec-ruscorpora-300')
    stop_words = stopwords.words('russian')
    snowball = SnowballStemmer(language='russian')
    valid_types = ['NOUN', 'VERB', 'ADJ']
    morph = pymorphy2.MorphAnalyzer() 
    k1 = 1
    k2 = 1


def score(query, document, k=(0.5, 0.7)):
    # взвешенная сумма семантического сходства заголовка с запросом и среднего значения tf_idf встречающихся в тексте слов из запроса

    k1 = k[0]
    k2 = k[1]
    if not stem_query:
        return 0

    sims = {}
    tfidfs = []
    for word1 in list(filter(lambda x: str(x[1]) in valid_types, upd_query)):
        sims[word1[0]] = 0
        for word2 in list(filter(lambda x: str(x[1]) in valid_types, upd_str(document.title, stem=False))):
            if '_'.join(list(word1)) in russian_model and '_'.join(list(word2)) in russian_model:
                sims[word1[0]] = max(sims[word1[0]], russian_model.similarity('_'.join(list(word1)), '_'.join(list(word2))))
        
    for word in stem_query:
        if word in TF_IDF_vocab:
            idx = TF_IDF_vocab[word]
            tf_idf = Y[document.id].toarray()[0][idx]
            if tf_idf > 0:
                tfidfs.append(tf_idf)

    return sum(sims.values()) / (len(sims) + 1) * k1 + sum(tfidfs) * k2 / (len(tfidfs) + 1)



def retrieve(query):
    global upd_query, stem_query

    upd_query = upd_str(query, stem=False)
    stem_query = upd_str(query).split()
    stem_query = list(filter(lambda x: x in index, stem_query))
    
    if not stem_query:
        return documents[:500]

    most_rel_idxs = []
    f = False

    # перебираем всевозможные комбинации слов в запросе, начиная с самой длинной, пересекая индексы документов, содержащих слова в комбинации
    # прекращаем поиск, если нашлось хотя бы 500 документов
    for i in range(len(stem_query), 0, -1):
        for comb in itertools.combinations(stem_query, i):
            valid_idxs = set()
            for word in comb:
                if not valid_idxs:
                    valid_idxs = set(index[word]) 
                valid_idxs = valid_idxs & set(index[word])
            most_rel_idxs.extend(list(valid_idxs - set(most_rel_idxs)))
            
            if len(most_rel_idxs) > 500:
                f = True
                break
        if f:
            break
    

    candidates = [] 
    for idx in most_rel_idxs:
        candidates.append(documents[idx])

    return candidates[:500]
    

    

