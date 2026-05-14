# NLP 개념과 코드 (Natural Language Processing)

## 1. 텍스트 전처리

### 1.1 기본 전처리 파이프라인
```python
import re
import string

def preprocess(text: str) -> str:
    text = text.lower()                            # 소문자화
    text = re.sub(r'https?://\S+', '', text)       # URL 제거
    text = re.sub(r'[^a-zA-Z가-힣\s]', '', text)  # 특수문자 제거
    text = re.sub(r'\s+', ' ', text).strip()       # 공백 정규화
    return text

# 불용어(Stopword) 제거
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))
tokens = preprocess("Hello World! This is a test.").split()
filtered = [w for w in tokens if w not in stop_words]
```

### 1.2 정규화
```python
from nltk.stem import PorterStemmer, WordNetLemmatizer

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

words = ["running", "runs", "ran", "better", "studies"]

# 어간추출 (Stemming): 규칙 기반, 빠름
stems = [stemmer.stem(w) for w in words]
# ['run', 'run', 'ran', 'better', 'studi']

# 표제어추출 (Lemmatization): 사전 기반, 정확
lemmas = [lemmatizer.lemmatize(w, pos='v') for w in words]
# ['run', 'run', 'run', 'better', 'study']
```

---

## 2. 토크나이저

### 2.1 단어/문장 토크나이저
```python
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize

text = "Hello, I'm studying NLP. It's fascinating!"

words = word_tokenize(text)
# ['Hello', ',', 'I', "'m", 'studying', 'NLP', '.', 'It', "'s", 'fascinating', '!']

sentences = sent_tokenize(text)
# ['Hello, I\'m studying NLP.', "It's fascinating!"]
```

### 2.2 BPE (Byte Pair Encoding) 직접 구현
서브워드 기반 토크나이저 — GPT, BERT 계열에서 사용

```python
from collections import Counter, defaultdict

def get_vocab(corpus):
    """단어를 문자 시퀀스로 분리 (끝에 </w> 추가)"""
    vocab = Counter()
    for word in corpus:
        vocab[' '.join(list(word)) + ' </w>'] += 1
    return vocab

def get_stats(vocab):
    """인접 쌍의 빈도수 계산"""
    pairs = defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i+1]] += freq
    return pairs

def merge_vocab(pair, vocab):
    """가장 빈번한 쌍을 병합"""
    new_vocab = {}
    bigram = ' '.join(pair)
    replacement = ''.join(pair)
    for word, freq in vocab.items():
        new_word = word.replace(bigram, replacement)
        new_vocab[new_word] = freq
    return new_vocab

# BPE 학습
corpus = ["low", "lower", "newest", "widest", "low", "new"]
vocab = get_vocab(corpus)

num_merges = 10
for _ in range(num_merges):
    pairs = get_stats(vocab)
    if not pairs: break
    best = max(pairs, key=pairs.get)
    vocab = merge_vocab(best, vocab)
    print(f"병합: {best}")
```

### 2.3 HuggingFace Tokenizer
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

text = "Natural Language Processing is amazing!"
encoded = tokenizer(text, return_tensors='pt')

print(encoded['input_ids'])       # 토큰 ID
print(tokenizer.convert_ids_to_tokens(encoded['input_ids'][0]))
# ['[CLS]', 'natural', 'language', 'processing', 'is', 'amazing', '!', '[SEP]']

# 배치 인코딩
batch = ["Hello world", "NLP is great"]
encoded_batch = tokenizer(
    batch,
    padding=True,        # 짧은 시퀀스를 패딩
    truncation=True,
    max_length=128,
    return_tensors='pt'
)
```

---

## 3. 임베딩

### 3.1 TF-IDF
```python
from sklearn.feature_extraction.text import TfidfVectorizer

corpus = [
    "the cat sat on the mat",
    "the dog sat on the log",
    "the cat ate the rat"
]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

print(f"shape: {X.shape}")  # (3, 8) - 3문서, 8어휘
print(f"feature names: {vectorizer.get_feature_names_out()}")

# 코사인 유사도
from sklearn.metrics.pairwise import cosine_similarity
sim = cosine_similarity(X[0], X[1])
print(f"문서 0-1 유사도: {sim[0,0]:.4f}")
```

### 3.2 Word2Vec 개념과 구현
- **CBOW**: 주변 단어로 중심 단어 예측
- **Skip-gram**: 중심 단어로 주변 단어 예측

```python
from gensim.models import Word2Vec

sentences = [
    ["the", "cat", "sat", "on", "the", "mat"],
    ["the", "dog", "ran", "in", "the", "park"],
    ["cats", "and", "dogs", "are", "pets"]
]

model = Word2Vec(
    sentences,
    vector_size=50,   # 임베딩 차원
    window=3,         # 문맥 창 크기
    min_count=1,      # 최소 등장 횟수
    sg=1,             # 1=Skip-gram, 0=CBOW
    epochs=100
)

# 단어 벡터
cat_vec = model.wv['cat']        # (50,)

# 유사 단어
similar = model.wv.most_similar('cat', topn=3)

# 벡터 연산 (king - man + woman ≈ queen)
result = model.wv.most_similar(positive=['dog', 'cat'], negative=[], topn=3)
```

### 3.3 BERT 임베딩 (문장 수준)
```python
from transformers import AutoTokenizer, AutoModel
import torch

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # [CLS] 토큰의 임베딩 = 문장 표현
    return outputs.last_hidden_state[:, 0, :].numpy()

emb1 = get_embedding("I love cats")
emb2 = get_embedding("I like felines")
emb3 = get_embedding("The stock market fell today")

# 코사인 유사도
import numpy as np
cos = lambda a, b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
print(f"cats vs felines: {cos(emb1[0], emb2[0]):.4f}")  # 높음
print(f"cats vs stock:   {cos(emb1[0], emb3[0]):.4f}")  # 낮음
```

---

## 4. Attention 메커니즘

### 4.1 Scaled Dot-Product Attention
```
Attention(Q, K, V) = softmax(QKᵀ / √dₖ) · V
```

```python
import torch
import torch.nn.functional as F
import numpy as np

def scaled_dot_product_attention(Q, K, V, mask=None):
    d_k = Q.size(-1)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(d_k)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    weights = F.softmax(scores, dim=-1)
    return torch.matmul(weights, V), weights

# 예시
seq_len, d_model = 5, 8
Q = torch.randn(1, seq_len, d_model)
K = torch.randn(1, seq_len, d_model)
V = torch.randn(1, seq_len, d_model)

output, attn_weights = scaled_dot_product_attention(Q, K, V)
print(f"Output shape: {output.shape}")      # (1, 5, 8)
print(f"Attn shape: {attn_weights.shape}")  # (1, 5, 5)
```

### 4.2 Multi-Head Attention
```python
import torch
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_k = d_model // num_heads
        self.num_heads = num_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def split_heads(self, x):
        B, L, D = x.shape
        x = x.view(B, L, self.num_heads, self.d_k)
        return x.transpose(1, 2)  # (B, H, L, d_k)

    def forward(self, Q, K, V, mask=None):
        Q, K, V = self.W_q(Q), self.W_k(K), self.W_v(V)
        Q, K, V = self.split_heads(Q), self.split_heads(K), self.split_heads(V)
        out, _ = scaled_dot_product_attention(Q, K, V, mask)
        out = out.transpose(1, 2).contiguous().view(Q.shape[0], -1, self.num_heads * self.d_k)
        return self.W_o(out)

mha = MultiHeadAttention(d_model=64, num_heads=8)
x = torch.randn(2, 10, 64)  # (batch, seq, d_model)
out = mha(x, x, x)
print(out.shape)  # (2, 10, 64)
```

---

## 5. 텍스트 분류 실습

### 5.1 감성 분석 (HuggingFace Pipeline)
```python
from transformers import pipeline

# 제로샷 분류
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = classifier(
    "This movie was absolutely fantastic!",
    candidate_labels=["positive", "negative", "neutral"]
)
print(result['labels'][0], result['scores'][0])

# 감성 분석
sentiment = pipeline("sentiment-analysis")
print(sentiment("I love this product!"))
# [{'label': 'POSITIVE', 'score': 0.9998}]
```

### 5.2 간단한 텍스트 분류기
```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

texts = [
    "I love this movie", "Great film!", "Best movie ever",
    "Terrible waste of time", "Awful film", "I hated it"
]
labels = [1, 1, 1, 0, 0, 0]

X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.33)

pipe = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression())
])
pipe.fit(X_train, y_train)
print(f"Accuracy: {pipe.score(X_test, y_test):.4f}")
```

---

## 6. 평가 지표

### 6.1 분류 지표
```python
from sklearn.metrics import classification_report, confusion_matrix

y_true = [1, 0, 1, 1, 0, 1, 0]
y_pred = [1, 0, 0, 1, 0, 1, 1]

print(classification_report(y_true, y_pred))
# precision, recall, F1-score 출력
```

### 6.2 언어생성 지표 (BLEU)
기계번역/텍스트생성 평가 지표: 예측 n-gram과 정답 n-gram의 겹침 비율

```python
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu

reference = [['the', 'cat', 'sat', 'on', 'the', 'mat']]
hypothesis = ['the', 'cat', 'is', 'on', 'the', 'mat']

score = sentence_bleu(reference, hypothesis)
print(f"BLEU: {score:.4f}")
```

---

## 연습문제 풀이 가이드

**레벨 1 (개념 확인)**
- "BPE와 WordPiece 토크나이저의 차이는?"
- "TF-IDF에서 DF가 높은 단어의 IDF 값은 크고 작고?"

**레벨 2 (계산)**
- "Attention 식에서 √dₖ로 나누는 이유는 무엇인가?"
- "BERT [CLS] 토큰이 문장 임베딩으로 쓰이는 이유는?"

**레벨 3 (코딩)**
- "간단한 BPE 토크나이저를 처음부터 구현하라 (get_stats, merge_vocab)"
- "두 문장의 TF-IDF 벡터를 구하고 코사인 유사도를 계산하라"
- "scaled_dot_product_attention을 numpy만으로 구현하라"
