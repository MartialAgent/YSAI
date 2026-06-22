# LLM 개념과 코드 (Large Language Models)

## 1. Transformer 아키텍처

### 1.1 전체 구조
```
입력 토큰 → 임베딩 → Positional Encoding
         → N × (Multi-Head Attention → Add&Norm → FFN → Add&Norm)
         → Linear → Softmax → 다음 토큰 확률
```

### 1.2 Positional Encoding
순서 정보를 sin/cos로 인코딩

```python
import numpy as np
import torch

def positional_encoding(max_len, d_model):
    PE = np.zeros((max_len, d_model))
    pos = np.arange(max_len)[:, np.newaxis]       # (max_len, 1)
    dim = np.arange(0, d_model, 2)                 # [0, 2, 4, ...]
    div_term = np.exp(dim * (-np.log(10000.0) / d_model))

    PE[:, 0::2] = np.sin(pos * div_term)  # 짝수 차원
    PE[:, 1::2] = np.cos(pos * div_term)  # 홀수 차원
    return torch.FloatTensor(PE)

PE = positional_encoding(100, 512)
print(PE.shape)  # (100, 512)
```

### 1.3 Feed-Forward Network (FFN)
각 위치에 독립적으로 적용되는 2층 MLP

```python
import torch.nn as nn

class FFN(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),           # ReLU보다 부드러운 활성화
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )

    def forward(self, x):
        return self.net(x)

# 보통 d_ff = 4 * d_model
ffn = FFN(d_model=512, d_ff=2048)
x = torch.randn(2, 10, 512)
print(ffn(x).shape)  # (2, 10, 512)
```

### 1.4 GPT 스타일 디코더 (Causal Attention)
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, num_heads, max_len=512):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        # 인과적 마스크 (미래 토큰 차단)
        mask = torch.tril(torch.ones(max_len, max_len)).view(1, 1, max_len, max_len)
        self.register_buffer('mask', mask)

    def forward(self, x):
        B, L, D = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)

        def split(t):
            return t.view(B, L, self.num_heads, self.d_k).transpose(1, 2)

        q, k, v = split(q), split(k), split(v)
        scores = (q @ k.transpose(-2, -1)) / (self.d_k ** 0.5)
        scores = scores.masked_fill(self.mask[:, :, :L, :L] == 0, float('-inf'))
        weights = F.softmax(scores, dim=-1)
        out = (weights @ v).transpose(1, 2).contiguous().view(B, L, D)
        return self.proj(out)
```

---

## 2. 언어모델 기초

### 2.1 언어모델의 정의
```
P(w₁, w₂, ..., wₙ) = ∏ P(wₜ | w₁, ..., wₜ₋₁)
```
다음 토큰의 조건부 확률 분포를 모델링

### 2.2 Perplexity (혼란도)
언어모델 평가 지표. 낮을수록 좋음.
```
PPL = exp(-1/N · Σ log P(wₜ|w<t))
```

```python
import torch
import torch.nn.functional as F
import math

def perplexity(logits, targets):
    """
    logits: (N, vocab_size) — 모델 출력 (log 확률 아님)
    targets: (N,) — 정답 토큰 ID
    """
    log_probs = F.log_softmax(logits, dim=-1)
    nll = F.nll_loss(log_probs, targets)  # 평균 NLL
    return math.exp(nll.item())

# 예시
vocab_size = 1000
N = 20
logits = torch.randn(N, vocab_size)
targets = torch.randint(0, vocab_size, (N,))
print(f"PPL: {perplexity(logits, targets):.2f}")
```

---

## 3. 파인튜닝 (Fine-tuning)

### 3.1 전체 파인튜닝 (Full Fine-tuning)
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers import TrainingArguments, Trainer
import torch

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# 데이터 준비
texts = ["I love this!", "This is terrible."]
labels = [1, 0]
encodings = tokenizer(texts, truncation=True, padding=True, return_tensors='pt')

class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.enc = encodings
        self.labels = labels
    def __len__(self): return len(self.labels)
    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.enc.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

dataset = SimpleDataset(encodings, labels)

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=2,
    learning_rate=2e-5,
)
trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
trainer.train()
```

### 3.2 LoRA (Low-Rank Adaptation)
대규모 모델을 효율적으로 파인튜닝 — 파라미터 99%를 고정

```
W' = W + ΔW = W + BA   (B: m×r, A: r×n, r << min(m,n))
```

```python
# peft 라이브러리 사용
from peft import get_peft_model, LoraConfig, TaskType
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("gpt2")

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,               # 랭크 (낮을수록 파라미터 절약)
    lora_alpha=32,     # 스케일링 계수
    lora_dropout=0.1,
    target_modules=["c_attn"]  # 적용할 레이어
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 294,912 || all params: 124,734,720 || trainable%: 0.24
```

---

## 4. RAG (Retrieval-Augmented Generation)

### 4.1 RAG 파이프라인
```
쿼리 → 쿼리 임베딩 → 벡터 검색 → 관련 문서 검색
     → [쿼리 + 문서] → LLM → 답변 생성
```

### 4.2 기본 RAG 구현
```python
import numpy as np
from anthropic import Anthropic

client = Anthropic()

# 문서 저장소 (실제론 벡터 DB 사용)
documents = [
    "파이썬은 1991년 귀도 반 로섬이 만든 언어다.",
    "딥러닝은 다층 신경망을 사용한 머신러닝이다.",
    "트랜스포머는 2017년 Attention Is All You Need 논문에서 제안됐다.",
    "BERT는 양방향 트랜스포머 인코더 모델이다.",
    "GPT는 단방향(자기회귀) 트랜스포머 디코더 모델이다.",
]

def embed(text: str) -> np.ndarray:
    """실제론 embedding API 사용, 여기선 TF-IDF로 대체"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    vect = TfidfVectorizer()
    matrix = vect.fit_transform(documents + [text])
    return matrix[-1].toarray()[0], vect, matrix[:-1]

def retrieve(query: str, docs: list, top_k: int = 2) -> list:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vect = TfidfVectorizer()
    matrix = vect.fit_transform(docs + [query])
    query_vec = matrix[-1]
    doc_vecs = matrix[:-1]
    scores = cosine_similarity(query_vec, doc_vecs)[0]
    top_idx = scores.argsort()[-top_k:][::-1]
    return [docs[i] for i in top_idx]

def rag_answer(query: str) -> str:
    context_docs = retrieve(query, documents, top_k=2)
    context = "\n".join(f"- {d}" for d in context_docs)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""다음 문서를 참고해서 질문에 답하세요.

문서:
{context}

질문: {query}"""
        }]
    )
    return response.content[0].text

print(rag_answer("트랜스포머가 뭐야?"))
```

---

## 5. 프롬프트 엔지니어링

### 5.1 기본 기법

```python
from anthropic import Anthropic
client = Anthropic()

def call(prompt, system="", max_tokens=512):
    msgs = [{"role": "user", "content": prompt}]
    kwargs = {"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": msgs}
    if system:
        kwargs["system"] = system
    return client.messages.create(**kwargs).content[0].text

# Zero-shot
print(call("파이썬으로 피보나치 수열 10개를 출력하는 코드를 작성하라."))

# Few-shot: 예시 제공
few_shot_prompt = """감성 분류. 출력은 POSITIVE 또는 NEGATIVE만.

입력: 이 영화 정말 재밌었어!
출력: POSITIVE

입력: 최악의 경험이었다.
출력: NEGATIVE

입력: 그저 그랬어.
출력:"""
print(call(few_shot_prompt))

# Chain-of-Thought
cot_prompt = """문제를 단계별로 풀어라.

Q: 냉장고에 사과 3개, 바나나 5개가 있다. 사과 1개를 먹고 바나나 2개를 샀다.
   전체 과일은 몇 개인가?
A: 단계별 풀이:"""
print(call(cot_prompt))
```

### 5.2 Temperature와 Sampling

```python
# Temperature 비교
for temp in [0.0, 0.7, 1.5]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        temperature=temp,
        messages=[{"role": "user", "content": "한 단어로: 하늘의 색은?"}]
    )
    print(f"temp={temp}: {response.content[0].text.strip()}")

# Top-p (nucleus sampling)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    top_p=0.9,           # 누적 확률 90% 내 토큰만 샘플링
    messages=[{"role": "user", "content": "창의적인 문장을 만들어라."}]
)
```

### 5.3 시스템 프롬프트 설계
```python
system = """당신은 파이썬 코드 리뷰 전문가입니다.
- 코드의 문제점을 구체적으로 지적하라
- 개선 코드를 항상 제시하라
- 성능, 가독성, 안전성 순으로 평가하라
- 답변은 한국어로 작성하라"""

code = """
def get_user(id):
    query = "SELECT * FROM users WHERE id=" + str(id)
    return db.execute(query)
"""

review = call(f"다음 코드를 리뷰하라:\n```python{code}```", system=system)
print(review)
```

---

## 6. 양자화와 효율화

### 6.1 모델 크기와 추론 비용
| 모델 | 파라미터 | FP32 메모리 | INT8 메모리 |
|------|---------|------------|------------|
| GPT-2 | 117M | ~470MB | ~117MB |
| LLaMA-7B | 7B | ~28GB | ~7GB |
| LLaMA-70B | 70B | ~280GB | ~70GB |

### 6.2 INT8 양자화 (bitsandbytes)
```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,             # INT8 양자화
    # load_in_4bit=True,           # INT4 (더 공격적)
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    "gpt2",
    quantization_config=quantization_config,
    device_map="auto"
)
```

---

## 7. 평가 지표

### 7.1 BLEU, ROUGE
```python
# ROUGE: 요약 평가
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
reference = "The cat sat on the mat in the room."
hypothesis = "The cat was sitting on the mat."

scores = scorer.score(reference, hypothesis)
for key, val in scores.items():
    print(f"{key}: P={val.precision:.3f} R={val.recall:.3f} F={val.fmeasure:.3f}")
```

---

## 연습문제 풀이 가이드

**레벨 1 (개념 확인)**
- "GPT와 BERT의 학습 목표(pretraining objective) 차이는?"
- "LoRA가 전체 파인튜닝보다 메모리 효율적인 이유는?"

**레벨 2 (계산)**
- "temperature=0일 때 LLM의 동작은? 수식으로 설명하라"
- "Perplexity가 100인 모델과 10인 모델의 차이를 직관적으로 설명하라"

**레벨 3 (코딩)**
- "Anthropic API로 Few-shot 감성 분류기를 만들어 3개 문장을 분류하라"
- "간단한 RAG 시스템을 구현하라: 5개 문서 → TF-IDF 검색 → Claude API로 답변"
- "temperature 0.0, 0.7, 1.5의 출력 다양성을 같은 프롬프트로 10번 샘플링해 비교하라"
