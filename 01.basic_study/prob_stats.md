# 확률통계 (Probability & Statistics)

## 1. 확률 기초

### 1.1 표본공간과 사건
- **표본공간(Ω)**: 가능한 모든 결과의 집합
- **사건(A)**: 표본공간의 부분집합
- **확률 공리**: P(Ω)=1, P(A)≥0, 상호배반 사건의 합산 가능성

### 1.2 조건부 확률
```
P(A|B) = P(A ∩ B) / P(B)
```
- B가 주어졌을 때 A가 일어날 확률
- 독립: P(A|B) = P(A) ↔ P(A∩B) = P(A)·P(B)

### 1.3 베이즈 정리 (Bayes' Theorem)
```
P(H|E) = P(E|H) · P(H) / P(E)
```
- **사전확률(Prior)** P(H): 증거 전 믿음
- **가능도(Likelihood)** P(E|H): 가설 하에서 증거 관측 확률
- **사후확률(Posterior)** P(H|E): 증거 후 업데이트된 믿음
- **주변확률(Marginal)** P(E) = Σ P(E|Hᵢ)·P(Hᵢ)

```python
# 베이즈 정리 예시: 병 진단
# P(병) = 0.01, P(양성|병) = 0.99, P(양성|건강) = 0.05
p_disease = 0.01
p_pos_given_disease = 0.99
p_pos_given_healthy = 0.05
p_healthy = 1 - p_disease

p_pos = p_pos_given_disease * p_disease + p_pos_given_healthy * p_healthy
p_disease_given_pos = (p_pos_given_disease * p_disease) / p_pos
print(f"양성일 때 실제 병일 확률: {p_disease_given_pos:.4f}")  # ~0.166
```

---

## 2. 확률분포

### 2.1 이산 확률분포

#### 베르누이 분포 (Bernoulli)
- 결과: 성공(1) or 실패(0)
- P(X=1) = p, P(X=0) = 1-p
- E[X] = p, Var(X) = p(1-p)

#### 이항 분포 (Binomial) B(n, p)
- n번 시행에서 성공 횟수
- P(X=k) = C(n,k) · p^k · (1-p)^(n-k)
- E[X] = np, Var(X) = np(1-p)

```python
from scipy import stats
import numpy as np

# 이항분포: 동전 10번, 앞면 확률 0.5
n, p = 10, 0.5
binom = stats.binom(n, p)
print(f"P(X=5) = {binom.pmf(5):.4f}")
print(f"P(X<=6) = {binom.cdf(6):.4f}")
print(f"평균={binom.mean()}, 분산={binom.var()}")
```

#### 포아송 분포 (Poisson) Poisson(λ)
- 단위 시간/공간에서 사건 발생 횟수
- P(X=k) = e^(-λ) · λ^k / k!
- E[X] = Var(X) = λ

```python
lam = 3  # 시간당 평균 3건
poisson = stats.poisson(lam)
print(f"P(X=0) = {poisson.pmf(0):.4f}")  # 사건 없을 확률
```

### 2.2 연속 확률분포

#### 균등 분포 (Uniform) U(a, b)
- f(x) = 1/(b-a), a≤x≤b
- E[X] = (a+b)/2, Var(X) = (b-a)²/12

#### 정규 분포 (Normal) N(μ, σ²)
- f(x) = (1/σ√2π) · exp(-(x-μ)²/2σ²)
- E[X] = μ, Var(X) = σ²
- **68-95-99.7 규칙**: μ±σ 안에 68%, μ±2σ 안에 95%

```python
import matplotlib.pyplot as plt

mu, sigma = 0, 1
normal = stats.norm(mu, sigma)

# P(-1 < X < 1) = 68%
prob = normal.cdf(1) - normal.cdf(-1)
print(f"P(|X|<1) = {prob:.4f}")

# 역함수: 상위 5% 분위수
q95 = normal.ppf(0.95)
print(f"95th percentile = {q95:.4f}")  # 1.645

# scipy로 P(X < 1) 계산
print(f"P(X<1) = {normal.cdf(1):.4f}")  # 0.8413
```

#### 지수 분포 (Exponential) Exp(λ)
- 포아송 프로세스에서 다음 사건까지의 대기 시간
- f(x) = λe^(-λx), x≥0
- E[X] = 1/λ, Var(X) = 1/λ²
- **무기억성**: P(X>s+t|X>s) = P(X>t)

---

## 3. 기댓값과 분산

### 3.1 기댓값 (Expected Value)
```
E[X] = Σ xᵢ·P(X=xᵢ)  (이산)
E[X] = ∫ x·f(x)dx     (연속)
```
- **선형성**: E[aX+b] = aE[X]+b
- E[X+Y] = E[X]+E[Y] (항상 성립)
- E[XY] = E[X]·E[Y] (X,Y 독립일 때만)

### 3.2 분산과 표준편차
```
Var(X) = E[(X-μ)²] = E[X²] - (E[X])²
SD(X) = √Var(X)
```
- Var(aX+b) = a²·Var(X)
- Var(X+Y) = Var(X)+Var(Y)+2Cov(X,Y)

### 3.3 공분산과 상관계수
```
Cov(X,Y) = E[(X-μₓ)(Y-μᵧ)]
ρ(X,Y) = Cov(X,Y) / (σₓ·σᵧ)   ∈ [-1, 1]
```

```python
import numpy as np

x = np.array([1, 2, 3, 4, 5])
y = np.array([2, 4, 5, 4, 5])

print(f"Cov = {np.cov(x, y)[0,1]:.4f}")
print(f"Corr = {np.corrcoef(x, y)[0,1]:.4f}")
```

---

## 4. 중심극한정리 (CLT)

**정리**: 임의의 분포를 가진 iid 확률변수 X₁,...,Xₙ의 표본평균은 n→∞일 때 정규분포에 수렴한다.

```
X̄ ~ N(μ, σ²/n)   (n이 충분히 클 때)
```

```python
import numpy as np
import matplotlib.pyplot as plt

# 지수분포(비정규)에서 표본평균의 분포 확인
n_samples, n_obs = 10000, 30
lam = 1
means = [np.mean(np.random.exponential(1/lam, n_obs)) for _ in range(n_samples)]
print(f"표본평균의 평균: {np.mean(means):.4f}")   # ≈ 1/lam = 1
print(f"표본평균의 표준편차: {np.std(means):.4f}") # ≈ σ/√n = 1/√30
```

---

## 5. 추정과 검정

### 5.1 최대가능도추정 (MLE)
목적: 관측 데이터를 가장 잘 설명하는 파라미터 θ를 찾는다.

```
θ_MLE = argmax L(θ) = argmax Σ log P(xᵢ|θ)
```

```python
from scipy.optimize import minimize_scalar
import numpy as np

# 정규분포 MLE: 해석적으로 μ=X̄, σ²=Σ(xᵢ-X̄)²/n
data = np.array([2.1, 3.4, 2.8, 3.1, 2.9, 3.5, 2.6])
mu_mle = np.mean(data)
sigma_mle = np.std(data)  # ddof=0 (MLE)
print(f"μ_MLE = {mu_mle:.4f}, σ_MLE = {sigma_mle:.4f}")
```

### 5.2 가설검정
- **귀무가설(H₀)**: 기본 가정 (차이 없음)
- **대립가설(H₁)**: 증명하고 싶은 것
- **p-value**: H₀가 참일 때 관측값 이상 극단적인 결과가 나올 확률
- **유의수준 α**: 보통 0.05 (5%)

```python
from scipy import stats

# 단일 표본 t-검정: 모평균이 3인지 검정
data = np.array([2.8, 3.2, 2.9, 3.5, 3.1, 2.7, 3.3])
t_stat, p_value = stats.ttest_1samp(data, popmean=3.0)
print(f"t={t_stat:.4f}, p={p_value:.4f}")
print(f"귀무가설 기각: {p_value < 0.05}")
```

---

## 6. 정보이론 기초

### 6.1 엔트로피 (Entropy)
불확실성의 척도. 분포가 균등할수록 엔트로피 높음.

```
H(X) = -Σ P(x) · log₂P(x)   (비트 단위)
H(X) = -Σ P(x) · ln P(x)    (nat 단위)
```

### 6.2 교차 엔트로피 (Cross Entropy)
실제 분포 p와 예측 분포 q의 차이.

```
H(p, q) = -Σ p(x) · log q(x)
```
- 분류 모델의 손실 함수로 사용
- p=q일 때 최솟값 = H(p)

### 6.3 KL 발산 (KL Divergence)
두 분포의 차이 (비대칭).

```
KL(p||q) = Σ p(x) · log(p(x)/q(x))
         = H(p, q) - H(p) ≥ 0
```

```python
import numpy as np

def entropy(p):
    p = np.array(p)
    p = p[p > 0]
    return -np.sum(p * np.log(p))

def cross_entropy(p, q):
    p, q = np.array(p), np.array(q)
    return -np.sum(p * np.log(q + 1e-10))

def kl_divergence(p, q):
    return cross_entropy(p, q) - entropy(p)

p = [0.5, 0.3, 0.2]   # 실제 분포
q = [0.4, 0.4, 0.2]   # 예측 분포

print(f"H(p)     = {entropy(p):.4f}")
print(f"H(p,q)   = {cross_entropy(p, q):.4f}")
print(f"KL(p||q) = {kl_divergence(p, q):.4f}")
```

### 6.4 상호정보량 (Mutual Information)
```
I(X;Y) = H(X) - H(X|Y) = H(Y) - H(Y|X)
```
X와 Y가 공유하는 정보의 양. 독립이면 I(X;Y)=0.

---

## 연습문제 풀이 가이드

**레벨 1 (개념 확인)**
- "베이즈 정리에서 사전확률과 사후확률의 차이는?"
- "포아송 분포가 이항분포의 극한인 이유는?"

**레벨 2 (계산)**
- "동전 20번 던져 앞면 15번 이상 나올 확률을 scipy로 계산하라"
- "정규분포 N(5, 4)에서 P(3 < X < 7)을 계산하라"

**레벨 3 (코딩)**
- "균등분포 U(0,1) 샘플로 CLT를 시뮬레이션하라 (n=5, 30, 100 비교)"
- "이진분류 모델의 예측 확률 [0.9, 0.2, 0.8]과 실제 [1, 0, 1]의 cross entropy를 계산하라"
