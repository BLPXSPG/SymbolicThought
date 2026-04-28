import numpy as np
import faiss  
import re
import tiktoken
import pickle
from generate.auto_generate import gen_embedding, gen_embeddings_batch

class VectorDatabase:
    def __init__(self, max_length=50, dimension=1536):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension) 
        self.texts = []  
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.max_length = max_length 

    def reset(self):
        self.index = faiss.IndexFlatIP(self.dimension)

    def save_faiss(self, path):
        faiss.write_index(self.index, path)

    def load_faiss(self, path):
        self.index = faiss.read_index(path)

    def save_texts(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self.texts, f)
    def load_texts(self, path):
        with open(path, 'rb') as f:
            self.texts = pickle.load(f)

    def merge_strings_until_max_length(self, strings, max_length, index):
        merged_list = []  
        for i in range(len(strings)):
            if len(self.tokenization(''.join(merged_list))) + len(self.tokenization(strings[i])) > max_length:
                break  
            merged_list.append(strings[i])

        index = index[:len(merged_list)]
        index_2 = [sorted(index).index(x) for x in index]
        original_order = sorted(enumerate(merged_list), key=lambda x: index_2[x[0]])
        restored_sentences = [sentence for i, sentence in original_order]
        return ''.join(restored_sentences),restored_sentences

    def tokenization(self, text):
        return self.encoding.encode(text)  

    def add_text(self, text, config, split=True):
        if split:
            segments = self.split_text(text, self.max_length)
            embeddings = gen_embeddings_batch(segments, config)
            for sentence, embedding in zip(segments, embeddings):
                if embedding is not None and self.index.is_trained:
                    self.index.add(embedding)
                    self.texts.append(sentence)
        else:
            embedding = gen_embedding(text, config)
            if embedding is not None and self.index.is_trained:
                self.index.add(embedding)
                self.texts.append(text)

    def query_length(self, query_text, max_length, config, threshold=0.5, return_list=False):
        query_embedding = gen_embedding(query_text, config)
        D, I = self.index.search(query_embedding, 99999)  

        filtered_results = [(self.texts[i], D[0][j]) for j, i in enumerate(I[0]) if D[0][j] >= threshold and i >= 0]

        if not filtered_results:
            return '' if not return_list else []

        relative_sentences = [text for text, _ in filtered_results]
        index = [i for i, _ in filtered_results]

        text, text_list = self.merge_strings_until_max_length(strings=relative_sentences, max_length=max_length, index=index)

        if return_list:
            return text_list
        return text

    def query_num(self, query_text, num, config, threshold=0.5, return_list=True):
        query_embedding = gen_embedding(query_text, config)
        D, I = self.index.search(query_embedding, 99999) 

        filtered_results = [(self.texts[i], D[0][j]) for j, i in enumerate(I[0]) if D[0][j] >= threshold and i >= 0]

        if not filtered_results:
            return '' if not return_list else []

        relative_sentences = [text for text, _ in filtered_results]

        if len(relative_sentences) < num:
            return ''.join(relative_sentences) if not return_list else relative_sentences

        relative_sentences = relative_sentences[:num]

        index = relative_sentences[:num]
        index_2 = [sorted(index).index(x) for x in index]
        original_order = sorted(enumerate(relative_sentences), key=lambda x: index_2[x[0]])
        restored_sentences = [sentence for i, sentence in original_order]

        if return_list:
            return restored_sentences
        return ''.join(restored_sentences)

    def find_sentences(self, text):
        sentence_endings = r'([，。？！.?!\n]+)'
        sentences = re.split(sentence_endings, text)
        sentences = [sentences[i] + sentences[i+1] for i in range(0, len(sentences)-1, 2)]
        sentences = [i.strip() for i in sentences]
        sentences = [i for i in sentences if i != '']
        return sentences

    def split_text(self, text, max_length):
        sentences = self.find_sentences(text)
        segments = []  
        current_segment = [] 
        current_length = 0  

        for sentence in sentences:
            sentence_length = len(self.tokenization(sentence))
            if sentence_length > max_length:
                if current_segment:
                    segments.append(''.join(current_segment))  
                    current_segment = [] 
                    current_length = 0
                segments.append(sentence)
            elif current_length + sentence_length <= max_length:
                current_segment.append(sentence)
                current_length += sentence_length
            else:
                segments.append(''.join(current_segment)) 
                current_segment = [sentence]  
                current_length = sentence_length

        if current_segment:
            segments.append(''.join(current_segment))

        print(segments)
        return segments

