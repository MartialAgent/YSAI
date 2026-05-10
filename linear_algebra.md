# 선형대수 (Linear Algebra)

## 1. 벡터

### 1.1 벡터 기초
- **벡터**: 크기와 방향을 가진 양, n차원 공간의 점
- **열벡터 / 행벡터**

```python
import numpy as np

v = np.array([1, 2, 3])          # 1D (벡터)
col = np.array([[1], [2], [3]])   # 열벡터 (3×1)
row = np.array([[1, 2, 3]])       # 행벡터 (1×3)
```

### 1.2 벡터 연산
```python
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# 덧셈, 스칼라 곱
print(a + b)          # [5, 7, 9]
print(2 * a)          # [2, 4, 6]

# 내적 (dot product)
dot = np.dot(a, b)    # 1*4 + 2*5 + 3*6 = 32
dot2 = a @ b          # 동일

# 노름 (L2)
norm = np.linalg.norm(a)   # √(1+4+9) = 3.742

# 코사인 유사도
cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### 1.3 벡터 공간 개념
- **선형 독립**: 어떤 벡터도 나머지의 선형결합으로 표현 불가
- **기저(Basis)**: 공간을 생성하는 선형독립 벡터 집합
- **차원(Dimension)**: 기저 벡터의 수

---

## 2. 행렬

### 2.1 행렬 연산

```python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 행렬 곱 (m×n @ n×p = m×p)
C = A @ B                  # [[19,22],[43,50]]

# 원소별 곱 (Hadamard)
H = A * B                  # [[5,12],[21,32]]

# 전치 (Transpose)
AT = A.T                   # [[1,3],[2,4]]

# 역행렬
A_inv = np.linalg.inv(A)
print(A @ A_inv)           # 단위행렬 (I)

# 행렬식 (Determinant)
det = np.linalg.det(A)    # 1*4 - 2*3 = -2
```

### 2.2 특수 행렬
- **단위행렬(I)**: 대각 원소가 1, 나머지 0
- **대각행렬(D)**: 대각 외 원소가 모두 0
- **대칭행렬**: A = Aᵀ
- **직교행렬**: AᵀA = I (행/열이 정규직교)
- **양의 정부호(PD)**: 모든 고유값 > 0

```python
# 단위행렬
I = np.eye(3)

# 대각행렬
D = np.diag([1, 2, 3])

# 직교행렬 예: 회전행렬
theta = np.pi / 4
R = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta),  np.cos(theta)]])
print(R.T @ R)  # ≈ I
```

---

## 3. 선형 시스템

### 3.1 Ax = b 풀기
```python
A = np.array([[2, 1], [1, 3]], dtype=float)
b = np.array([8, 13], dtype=float)

# numpy 풀이
x = np.linalg.solve(A, b)
print(x)  # [1, 6]

# 검증
print(A @ x)  # ≈ b
```

### 3.2 최소제곱 해 (Least Squares)
Ax = b가 over-determined (행 > 열)일 때 ||Ax - b||² 최소화.

```python
# y = ax + b 선형회귀
x_data = np.array([1, 2, 3, 4, 5])
y_data = np.array([2.1, 3.9, 6.2, 7.8, 10.1])

# 설계 행렬 구성
A = np.column_stack([x_data, np.ones(len(x_data))])

# 최소제곱 해: (AᵀA)⁻¹Aᵀb
coeffs, residuals, rank, sv = np.linalg.lstsq(A, y_data, rcond=None)
a, b_val = coeffs
print(f"기울기: {a:.4f}, 절편: {b_val:.4f}")
```

---

## 4. 고유값과 고유벡터

### 4.1 정의
```
Av = λv
```
- **고유벡터(v)**: 행렬 변환 후 방향이 변하지 않는 벡터
- **고유값(λ)**: 고유벡터의 스케일 변화량
- 특성방정식: det(A - λI) = 0

```python
A = np.array([[4, 1], [2, 3]])

eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"고유값: {eigenvalues}")           # [5, 2]
print(f"고유벡터:\n{eigenvectors}")

# 검증: Av = λv
v0 = eigenvectors[:, 0]
lam0 = eigenvalues[0]
print(np.allclose(A @ v0, lam0 * v0))   # True
```

### 4.2 대칭행렬의 고유분해
대칭행렬 A = QΛQᵀ (직교행렬 Q, 대각행렬 Λ)
- 고유값이 모두 실수
- 고유벡터가 서로 직교

```python
A = np.array([[4, 2], [2, 3]])  # 대칭
eigenvalues, Q = np.linalg.eigh(A)  # 대칭 전용 (더 안정적)

# 재구성 확인
A_reconstructed = Q @ np.diag(eigenvalues) @ Q.T
print(np.allclose(A, A_reconstructed))  # True
```

### 4.3 머신러닝에서의 의미
- PCA: 공분산 행렬의 고유벡터 = 주성분 방향
- 고유값 = 해당 방향의 분산량
- 큰 고유값 방향 = 데이터 분산이 큰 방향

---

## 5. 특이값 분해 (SVD)

### 5.1 정의
임의의 m×n 행렬 A를 다음으로 분해:
```
A = UΣVᵀ
```
- **U** (m×m): 좌 특이벡터 (직교행렬)
- **Σ** (m×n): 특이값 대각행렬 (내림차순)
- **V** (n×n): 우 특이벡터 (직교행렬)

```python
A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])

U, S, Vt = np.linalg.svd(A, full_matrices=False)
print(f"U shape: {U.shape}")   # (4, 3)
print(f"S: {S}")               # 특이값 (내림차순)
print(f"Vt shape: {Vt.shape}") # (3, 3)

# 재구성
A_reconstructed = U @ np.diag(S) @ Vt
print(np.allclose(A, A_reconstructed))  # True
```

### 5.2 저랭크 근사 (Low-rank Approximation)
상위 k개 특이값만 사용 → 데이터 압축 / 노이즈 제거

```python
# 이미지 압축 시뮬레이션
A = np.random.randn(100, 100)
U, S, Vt = np.linalg.svd(A)

for k in [5, 20, 50]:
    A_k = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
    error = np.linalg.norm(A - A_k, 'fro') / np.linalg.norm(A, 'fro')
    variance_explained = np.sum(S[:k]**2) / np.sum(S**2)
    print(f"k={k}: 재구성 오차={error:.4f}, 설명분산={variance_explained:.4f}")
```

### 5.3 SVD와 PCA의 관계
- 중심화된 데이터 X의 SVD = PCA
- X = UΣVᵀ → 주성분 = V의 열벡터
- 설명분산 비율 = σᵢ² / Σσⱼ²

---

## 6. 차원 축소

### 6.1 PCA (Principal Component Analysis)

```python
from sklearn.decomposition import PCA
import numpy as np

# 2D 데이터 생성
np.random.seed(42)
X = np.random.randn(100, 5)  # 100 샘플, 5 특성

# PCA
pca = PCA(n_components=2)
X_reduced = pca.fit_transform(X)

print(f"원본 shape: {X.shape}")         # (100, 5)
print(f"축소 shape: {X_reduced.shape}") # (100, 2)
print(f"설명 분산 비율: {pca.explained_variance_ratio_}")

# 직접 구현 (SVD 사용)
X_centered = X - X.mean(axis=0)
U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
X_pca = X_centered @ Vt[:2].T   # 상위 2개 주성분
```

### 6.2 행렬의 계수 (Rank)
- 선형독립인 행(또는 열)의 최대 수
- rank(A) = rank(Aᵀ) = 0이 아닌 특이값의 수

```python
A = np.array([[1, 2, 3], [2, 4, 6], [1, 1, 1]])
rank = np.linalg.matrix_rank(A)
print(f"rank = {rank}")  # 2 (첫 두 행이 선형 종속)
```

---

## 7. 노름과 거리

### 7.1 벡터 노름
```
L1 노름: ||v||₁ = Σ|vᵢ|
L2 노름: ||v||₂ = √(Σvᵢ²)
L∞ 노름: ||v||∞ = max|vᵢ|
```

```python
v = np.array([3, -4, 0])
print(f"L1: {np.linalg.norm(v, 1)}")   # 7
print(f"L2: {np.linalg.norm(v, 2)}")   # 5
print(f"L∞: {np.linalg.norm(v, np.inf)}")  # 4
```

### 7.2 행렬 노름
```python
A = np.array([[1, 2], [3, 4]])
print(f"Frobenius: {np.linalg.norm(A, 'fro'):.4f}")  # √(1+4+9+16)
print(f"Spectral:  {np.linalg.norm(A, 2):.4f}")      # 최대 특이값
```

---

## 연습문제 풀이 가이드

**레벨 1 (개념 확인)**
- "고유벡터와 일반 벡터의 차이는? 직관적으로 설명하라"
- "SVD에서 U, Σ, V의 역할을 각각 설명하라"

**레벨 2 (계산)**
- "A = [[3,1],[0,2]]의 고유값과 고유벡터를 손으로 계산하고 numpy로 검증하라"
- "[[1,2,0],[0,1,3]]의 SVD를 구하고 k=1 저랭크 근사를 계산하라"

**레벨 3 (코딩)**
- "100×50 랜덤 행렬을 PCA로 2D 축소하고 설명 분산 비율을 시각화하라"
- "Word2Vec 임베딩 행렬(가정)에 SVD를 적용해 단어 유사도를 코사인 유사도로 계산하라"
