# 파이썬 문법 (Python Syntax)

## 1. 자료구조

### 1.1 리스트 (List)
```python
lst = [1, 2, 3, 4, 5]

# 슬라이싱
print(lst[1:3])    # [2, 3]
print(lst[::-1])   # [5, 4, 3, 2, 1] 역순

# 컴프리헨션
squares = [x**2 for x in range(10) if x % 2 == 0]
# [0, 4, 16, 36, 64]

# 자주 쓰는 메서드
lst.append(6)       # 끝에 추가
lst.extend([7, 8])  # 여러 원소 추가
lst.insert(0, 0)    # 인덱스 위치에 삽입
lst.pop()           # 끝 원소 제거 및 반환
lst.sort()          # 원본 정렬 (in-place)
sorted(lst)         # 새 정렬 리스트 반환
```

### 1.2 딕셔너리 (Dict)
```python
d = {'a': 1, 'b': 2, 'c': 3}

# 접근
d['a']           # 1
d.get('z', 0)    # 키 없으면 기본값 반환

# 컴프리헨션
squared = {k: v**2 for k, v in d.items()}

# 자주 쓰는 패턴
for k, v in d.items():
    print(f"{k}: {v}")

keys = list(d.keys())
vals = list(d.values())

# 병합 (Python 3.9+)
d1 = {'a': 1}
d2 = {'b': 2}
merged = d1 | d2   # {'a': 1, 'b': 2}
```

### 1.3 집합 (Set)
```python
s1 = {1, 2, 3, 4}
s2 = {3, 4, 5, 6}

s1 | s2    # 합집합: {1,2,3,4,5,6}
s1 & s2    # 교집합: {3,4}
s1 - s2    # 차집합: {1,2}
s1 ^ s2    # 대칭차: {1,2,5,6}

# 중복 제거
lst = [1, 2, 2, 3, 3, 3]
unique = list(set(lst))
```

### 1.4 튜플 (Tuple)과 언패킹
```python
t = (1, 2, 3)
a, b, c = t           # 언패킹

# *로 나머지 받기
first, *rest = [1, 2, 3, 4, 5]
# first=1, rest=[2,3,4,5]

# 네임드튜플
from collections import namedtuple
Point = namedtuple('Point', ['x', 'y'])
p = Point(3, 4)
print(p.x, p.y)  # 3 4
```

---

## 2. 함수형 프로그래밍

### 2.1 람다와 고차함수
```python
# lambda
square = lambda x: x ** 2
print(square(5))   # 25

# map: 각 원소에 함수 적용
numbers = [1, 2, 3, 4, 5]
doubled = list(map(lambda x: x * 2, numbers))

# filter: 조건 만족 원소만
evens = list(filter(lambda x: x % 2 == 0, numbers))

# reduce: 누적 연산
from functools import reduce
total = reduce(lambda acc, x: acc + x, numbers, 0)  # 15
product = reduce(lambda acc, x: acc * x, numbers, 1) # 120
```

### 2.2 제너레이터 (Generator)
메모리 효율적 — 값을 필요할 때 생성

```python
# 제너레이터 표현식
gen = (x**2 for x in range(10))  # 즉시 계산 안 함

# yield 함수
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
print([next(fib) for _ in range(8)])  # [0,1,1,2,3,5,8,13]

# islice로 무한 제너레이터 제한
from itertools import islice
first_10 = list(islice(fibonacci(), 10))
```

### 2.3 데코레이터 (Decorator)
```python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time()-start:.4f}s")
        return result
    return wrapper

@timer
def slow_function(n):
    return sum(range(n))

slow_function(1_000_000)
```

### 2.4 itertools / functools 패턴
```python
from itertools import chain, product, combinations, permutations, groupby
from functools import partial, lru_cache

# 중첩 리스트 펼치기
nested = [[1,2], [3,4], [5,6]]
flat = list(chain.from_iterable(nested))  # [1,2,3,4,5,6]

# 조합/순열
combs = list(combinations([1,2,3], 2))     # [(1,2),(1,3),(2,3)]
perms = list(permutations([1,2,3], 2))     # 6가지

# 메모이제이션
@lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

# partial: 인자 고정
from functools import partial
def power(base, exp): return base ** exp
square = partial(power, exp=2)
cube   = partial(power, exp=3)
```

---

## 3. OOP (객체지향 프로그래밍)

### 3.1 클래스 기본
```python
class Animal:
    species = "Unknown"   # 클래스 변수

    def __init__(self, name, sound):
        self.name = name   # 인스턴스 변수
        self.sound = sound

    def speak(self):
        return f"{self.name} says {self.sound}"

    def __repr__(self):
        return f"Animal(name={self.name!r})"

    def __eq__(self, other):
        return isinstance(other, Animal) and self.name == other.name

dog = Animal("Dog", "Woof")
print(dog.speak())
print(repr(dog))
```

### 3.2 상속과 다형성
```python
class Shape:
    def area(self):
        raise NotImplementedError

class Circle(Shape):
    def __init__(self, r):
        self.r = r
    def area(self):
        return 3.14159 * self.r ** 2

class Rectangle(Shape):
    def __init__(self, w, h):
        self.w, self.h = w, h
    def area(self):
        return self.w * self.h

shapes = [Circle(5), Rectangle(3, 4)]
total = sum(s.area() for s in shapes)  # 다형성
```

### 3.3 특수 메서드 (Dunder)
```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    def __len__(self):
        return 2

    def __getitem__(self, idx):
        return (self.x, self.y)[idx]

    def __iter__(self):
        yield self.x
        yield self.y

    def __str__(self):
        return f"Vector({self.x}, {self.y})"

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)    # Vector(4, 6)
print(list(v1))   # [1, 2]
```

### 3.4 dataclass
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Student:
    name: str
    score: float
    courses: List[str] = field(default_factory=list)

    def grade(self):
        if self.score >= 90: return 'A'
        if self.score >= 80: return 'B'
        return 'C'

s = Student("Alice", 92.5, ["Math", "CS"])
print(s.grade())  # A
```

---

## 4. NumPy 패턴

### 4.1 배열 생성과 조작
```python
import numpy as np

# 생성
a = np.zeros((3, 4))
b = np.ones((2, 3))
c = np.arange(0, 10, 2)       # [0, 2, 4, 6, 8]
d = np.linspace(0, 1, 5)      # [0, 0.25, 0.5, 0.75, 1]
r = np.random.randn(3, 3)     # 정규분포

# 형태 변환
a = np.arange(12)
b = a.reshape(3, 4)
c = b.flatten()               # 1D로
d = b.T                       # 전치
e = b[np.newaxis, :, :]       # 차원 추가
f = np.squeeze(e)             # 크기 1인 차원 제거
```

### 4.2 인덱싱과 슬라이싱
```python
A = np.array([[1,2,3],[4,5,6],[7,8,9]])

A[1, 2]         # 6 (행1, 열2)
A[0:2, 1:3]     # [[2,3],[5,6]]
A[:, 1]         # [2, 5, 8] (모든 행의 열1)

# 불리언 인덱싱
mask = A > 5
A[mask]         # [6, 7, 8, 9]
A[A % 2 == 0]   # 짝수만

# 팬시 인덱싱
A[[0, 2], :]    # 0행, 2행
A[:, [0, 2]]    # 0열, 2열
```

### 4.3 브로드캐스팅
```python
A = np.array([[1,2,3],[4,5,6]])  # (2,3)
b = np.array([10, 20, 30])       # (3,)

# 자동으로 브로드캐스트
C = A + b   # [[11,22,33],[14,25,36]]

# 열 정규화
mean = A.mean(axis=0)    # (3,) - 각 열의 평균
std  = A.std(axis=0)
A_norm = (A - mean) / std

# 행 정규화
mean_row = A.mean(axis=1, keepdims=True)  # (2,1) 유지
A_row_norm = A - mean_row
```

### 4.4 벡터화 연산 (빠른 패턴)
```python
# 느린 방식 (for loop)
result = []
for x in range(1000):
    result.append(np.sin(x))

# 빠른 방식 (벡터화)
x = np.arange(1000)
result = np.sin(x)   # C 레벨에서 실행

# einsum: 복잡한 텐서 연산
A = np.random.randn(3, 4)
B = np.random.randn(4, 5)
C = np.einsum('ij,jk->ik', A, B)  # 행렬 곱
trace = np.einsum('ii', A[:3, :3])  # 대각합
```

---

## 5. Pandas 패턴

### 5.1 DataFrame 기본
```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'score': [85, 92, 78, 95],
    'grade': ['B', 'A', 'C', 'A']
})

# 기본 탐색
df.head(2)
df.info()
df.describe()
df.shape         # (4, 3)
df.dtypes
```

### 5.2 선택과 필터링
```python
# 열 선택
df['score']           # Series
df[['name', 'score']] # DataFrame

# 행 선택
df.iloc[0]            # 인덱스로
df.loc[0]             # 레이블로

# 조건 필터링
df[df['score'] >= 90]
df[(df['score'] >= 80) & (df['grade'] == 'A')]
df.query("score >= 90 and grade == 'A'")
```

### 5.3 그룹과 집계
```python
# groupby
df.groupby('grade')['score'].mean()
df.groupby('grade').agg({'score': ['mean', 'std', 'count']})

# pivot_table
df_wide = df.pivot_table(values='score', index='grade', aggfunc='mean')
```

### 5.4 누락값 처리
```python
df_with_nan = pd.DataFrame({'a': [1, np.nan, 3], 'b': [np.nan, 2, 3]})

df_with_nan.isna().sum()         # 열별 누락값 개수
df_with_nan.dropna()             # 누락값 포함 행 삭제
df_with_nan.fillna(0)            # 0으로 채우기
df_with_nan.fillna(df_with_nan.mean())  # 평균으로 채우기
```

---

## 6. 파이썬 고급 패턴

### 6.1 컨텍스트 매니저
```python
# with 문
with open('file.txt', 'r') as f:
    content = f.read()

# 직접 구현
class Timer:
    def __enter__(self):
        import time
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        print(f"Elapsed: {self.elapsed:.4f}s")

with Timer() as t:
    sum(range(1_000_000))
```

### 6.2 타입 힌트
```python
from typing import Optional, Union, List, Dict, Tuple, Callable

def process(
    data: List[float],
    func: Callable[[float], float],
    default: Optional[float] = None
) -> Dict[str, float]:
    results = [func(x) for x in data]
    return {'mean': sum(results) / len(results)}
```

### 6.3 예외 처리 패턴
```python
class ValidationError(ValueError):
    pass

def validate_score(score: float) -> float:
    if not 0 <= score <= 100:
        raise ValidationError(f"Score {score} out of range [0, 100]")
    return score

try:
    validate_score(150)
except ValidationError as e:
    print(f"Invalid: {e}")
except Exception as e:
    print(f"Unexpected: {e}")
finally:
    print("Done")  # 항상 실행
```

---

## 연습문제 풀이 가이드

**레벨 1 (동작 예측)**
- `list(map(lambda x: x**2, filter(lambda x: x%2==0, range(10))))` 출력값은?
- `[*range(3), *range(3)]` 결과는?

**레벨 2 (작성)**
- `collections.Counter`를 사용해 문자열의 단어 빈도수를 계산하라
- 제너레이터로 무한 등차수열(시작, 공차 지정)을 구현하라

**레벨 3 (최적화)**
- 1백만 개의 숫자 합산을 for loop vs NumPy 벡터화로 비교하고 timeit으로 측정하라
- LRU 캐시 없이/있이 피보나치(n=35)를 계산하고 시간 차이를 측정하라
