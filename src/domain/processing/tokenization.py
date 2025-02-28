import pickle
import os
from abc import ABC, abstractmethod

from src.domain.processing.cleaning import clean_text, clean_token

class Tokenizer(ABC):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    @abstractmethod
    def tokenize(self, text):
        ...

class SpacyTokenizer(Tokenizer):
    def __init__(self):
        import spacy
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Done to avoid GPU warnings from Tensorflow
        tokenizer = None
        current_dir = os.path.dirname(os.path.realpath(__file__))
        nlp_path = os.path.join(current_dir, "spacy_nlp.p")

        if os.path.isfile(nlp_path):
            with open(nlp_path, "rb") as f:
                tokenizer = pickle.load(f)
        else:
            tokenizer = spacy.load("es_core_news_md")
        pickle.dump(tokenizer, open(nlp_path, "wb"))
        super().__init__(tokenizer)

    def tokenize(self, text):
        # type: (str) -> list
        text = clean_text(text)
        tokens = self.tokenizer(text)
        tokens = map(str, tokens)
        tokens = map(clean_token, tokens)
        tokens = [token for token in tokens if token != '']

        return tokens

class NLTKTokenizer(Tokenizer):
    def __init__(self):
        import nltk
        tokenizer = nltk.tokenize.word_tokenize
        super().__init__(tokenizer)

    def tokenize(self, text):
        # type: (str) -> list
        cleaned_text = clean_text(text) # The cleaning should be performed outside this module
        tokens = self.tokenizer(cleaned_text)
        tokens = [clean_token(token) for token in tokens]
        tokens = [token for token in tokens if token != '']
        return tokens

def get_tokenizer(tokenizer='nltk'):
    # type: (str) -> Tokenizer
    tokenizer = tokenizer.lower()
    if tokenizer == 'nltk':
        return NLTKTokenizer()
    elif tokenizer == 'spacy':
        return SpacyTokenizer()
    else:
        raise ValueError('Tokenizer {} not found'.format(tokenizer))
