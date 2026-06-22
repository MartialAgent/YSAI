# Python 기초 및 데이터 타입 실습 스크립트
# 코랩과 같은 환경에서 실행할 수 있도록 변환

print("=" * 50)
print("Python 기초 및 데이터 타입 실습")
print("=" * 50)

# 1. 출력
print("\n1. 출력")
print('안녕하세요')
print(1)

# 셀의 맨 마지막을 항상 출력합니다
print("'안녕하세요'")
print("'반갑습니다'")

# print 구문을 붙혀 주면 중간에서도 출력합니다.
print('안녕하세요')
print("'반갑습니다'")
print("'다음에 또 봐요'")

# 2. 변수와 대입
print("\n2. 변수와 대입")
print("변수는 **데이터를 담는 그릇**이라고 생각하시면 됩니다.")

# 2-1. 변수의 이름
print("\n2-1. 변수의 이름")

# case 1. 알파벳 (가능) / 대소문자 모두 가능 /심지어 **한글도 가능하나 사용하는 것은 비추**!
a = 1
A = 1
변수 = 1
print(f"변수: {변수}")

# case 2. 알파벳 + 숫자 (가능)
a1 = 1

# case 3. 알파벳 + 언더바(_) (가능)
a_ = 1

# case 4. 언더바(_) + 알파벳 (가능)
_a = 1

# case 5. 숫자 + 알파벳 (불가능) - 주석 처리
# 1a = 1  # SyntaxError 발생

# case 6. 특수문자 (불가능) - 주석 처리
# * = 7  # SyntaxError 발생

# case 7. 언더바를 제외한 특수문자 (불가능) - 주석 처리
# a$ = 6  # SyntaxError 발생

# case 8. 변수의 이름 사이의 공백 (불가능) - 주석 처리
# a b = 6  # SyntaxError 발생

print("주로 변수는 **소문자 알파벳으로 생성**하고, 필요시 **언더바**나 **숫자를 붙히는 방식**이 일반적입니다.")

test = 10
test01 = 20
test_01 = 30

# 2-2. 변수의 출력
print("\n2-2. 변수의 출력")
print("1. print() 구문 사이에 **값을 직접 집어 넣으면**, 바로 **값이 출력**됩니다.")
print("2. print() 구문 사이에 **변수 이름**을 집어 넣으면, 그 **값이 출력**이 됩니다.")

# 값을 바로 집어 넣은 경우
print('test')

a = 123
print(a)

a = '안녕하세요, 반갑습니다'
print(a)

# 3. 데이터 타입
print("\n3. 데이터 타입")
print("**데이터 type**")
print("1. int(정수)")
print("2. float(실수)")
print("3. str(문자열)")
print("4. bool(참/거짓)")

# 3-1. int(정수)
print("\n3-1. int(정수)")
a = 1
print(f"type(a): {type(a)}")

if 1:
    print('1은 참으로 취급')
else:
    print('1은 거짓부렁이')

if 0:
    print('0은 참으로 취급')
else:
    print('0은 거짓부렁이')

if 123:
    print('123은 참으로 취급')
else:
    print('123은 거짓부렁이')

# 3-2. float(실수)
print("\n3-2. float(실수)")
a = 3.14
print(f"type(a): {type(a)}")
print(a)

# 3-3. str 혹은 object (문자)
print("\n3-3. str 혹은 object (문자)")
word = '안녕하세요'
word = "안녕하세요"
print(f"type(word): {type(word)}")

# 3-4. bool (참/거짓)
print("\n3-4. bool (참/거짓)")
a = False
print(a)
print(f"0 == False: {0 == False}")

# 3-5 아무것도 아닌 None 타입도 있습니다.
print("\n3-5 아무것도 아닌 None 타입도 있습니다.")
print("말 그래도 아무 것도 아닌 흔히 Null 값을 넣는다고도 합니다.")
print("사전상 의미는")
print("* **Null: Nullify (무효화하다)**")
print("라는 뜻을 가지고 있다네요~")
print("python에서는 **None** 입니다!")

a = None
print(f"type(a): {type(a)}")
print(a)

print("조건문에 None이라면??")
if None:
    print('None은 참으로 취급')
else:
    print('None은 거짓부렁이')

# 4. 데이터 타입 (집합)
print("\n4. 데이터 타입 (집합)")
print("**집합 형태의 데이터 타입**")
print("1. list (순서 O, 집합)")
print("2. tuple (순서 O, 읽기 전용 집합)")
print("3. set (순서 X, 중복X 집합)")
print("4. dict (key, value로 이루어진 사전형 집합)")

# 4-1. list (순서가 있는 집합)
print("\n4-1. list (순서가 있는 집합)")
print("[] 형태로 표현합니다.")

mylist = []
print(mylist)
print(f"type(mylist): {type(mylist)}")

mylist = [1, 3, 2, 4, 5]
print(mylist)

# 값을 추가하기
print("\n값을 추가하기")
mylist = []
print(mylist)

mylist.append(1)
print(mylist)

mylist.append(2)
mylist.append(3)
print(mylist)

# 값을 제거하기
print("\n값을 제거하기")
print(mylist)
mylist.remove(1)
print(mylist)

# 여러 값들이 포함되어 있을 때 제거 순서
print("\n여러 값들이 포함되어 있을 때 제거 순서")
mylist = []
mylist.append(1)
mylist.append(2)
mylist.append(3)
mylist.append(1)
mylist.append(2)
mylist.append(3)
print(mylist)

mylist.remove(1)
print(mylist)

mylist.remove(1)
print(mylist)

# 인덱싱(indexing) -> 색인
print("\n인덱싱(indexing) -> 색인")
mylist = [1, 2, 3, 4]
print("인덱스는 **0번 부터 시작** 합니다.")

print(f"mylist[0]: {mylist[0]}")
print(f"mylist[3]: {mylist[3]}")

# 인덱스로 접근하여 값 바꾸기
print("\n인덱스로 접근하여 값 바꾸기")
print(mylist)
print(f"mylist[0]: {mylist[0]}")
mylist[0] = 100
print(mylist)

# 전체 길이 (사이즈) 알아내기
print("\n전체 길이 (사이즈) 알아내기")
print(f"len(mylist): {len(mylist)}")

# 4-2. tuple (순서가 있는 집합, 읽기 전용)
print("\n4-2. tuple (순서가 있는 집합, 읽기 전용)")
print("() 로 표현합니다")

mytuple = (1, 2, 3, 4, 5)

# tuple은 수정 불가능
print("tuple은 append, remove, 인덱스 수정이 불가능합니다.")

# 길이 파악하기
print(f"len(mytuple): {len(mytuple)}")
print(mytuple)

# 4-3. set (순서 X, 중복 X)
print("\n4-3. set (순서 X, 중복 X)")
myset = set()
print(myset)
print(f"type(myset): {type(myset)}")

myset.add(1)
myset.add(2)
myset.add(3)
print(myset)

# 중복 추가해도 중복 제거됨
myset.add(1)
myset.add(2)
myset.add(3)
myset.add(1)
myset.add(2)
myset.add(3)
print(myset)

myset.add(4)
print(myset)

# 4-4. dict (사전형 집합, key와 value 쌍)
print("\n4-4. dict (사전형 집합, key와 value 쌍)")
print("{}로 표현합니다")

mydict = dict()
print(mydict)
print(f"type(mydict): {type(mydict)}")

# 값을 추가하기
print("\n값을 추가하기")
mydict = dict()
mydict['apple'] = 123
print(f"mydict['apple']: {mydict['apple']}")

mydict[0] = 2
print(f"mydict[0]: {mydict[0]}")

print("mydict의 키는 **문자형** / **숫자형**이 혼용 가능합니다")
print(mydict)

# float(실수)도 키로써 입력이 가능합니다.
mydict[3.14] = 1
print(mydict)

# 값을 바꾸기
print("\n값을 바꾸기")
mydict['apple'] = 'byebye'
print(mydict)

# 길이 파악하기
print("\n길이 파악하기")
print(f"len(mydict): {len(mydict)}")

print("\n" + "=" * 50)
print("실습 완료!")
print("=" * 50)
