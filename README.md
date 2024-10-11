# 🍊 감귤하우스 
<img src="static/images/readme_img/gamgyulhouse.png" width="100%"/>

<br>

- 프로젝트 명 : Gamgyul House
- 프로젝트 진행 기간 : 24.09.20 ~ 24.10.13

<br>

감귤하우스는 상품(감귤)을 홍보하고 거래할 수 있는 SNS 플랫폼입니다. 
상품을 등록하지 않아도 일상을 공유하며 즐거운 SNS 활동을 할 수 있습니다. 
사진과 함께 게시물을 작성하여 자신의 일상을 공유할 수 있습니다. 다른 사용자를 팔로우하면 유저가 올린 게시물을 홈 피드에서 확인할 수 있습니다. 다른 사용자와 메시지를 주고 받을 수도 있습니다. 피드를 구경하다가 마음에 드는 게시물을 발견했다면 좋아요와 댓글을 남길 수 있습니다.

<br>

## 🏡 1. 팀 소개

| 이름   | 사진  | 깃허브 주소               | 담당 파트            |
|--------|-------|----------------------------|----------------------|
| 김동규  | ![김동규](이미지경로) | [@Donggyu-Kim](https://github.com/Donggyu-Kim1) | accounts, report           |
| 이원재  | ![이원재](이미지경로) | [@lwz7](https://github.com/lwj0712) | chat, alarm           |
| 문지영  | ![문지영](이미지경로) | [@JiyoungMoon](https://github.com/whaehofk521) | insta           |
| 박성재  | ![박성재](이미지경로) | [@HwangDal85](https://github.com/HwangDal85) | market           |

프로젝트 기간 동안 휴일, 주말 빠짐 없이 모두 참여해 작업한 열정있고 책임감 있는 BE 개발자들로 구성되어 있습니다.

<br>

## 2. 개발 목표

저희 감귤하우스 팀은 현대적이고 확장 가능한 SNS 및 사용자 간 직거래 플랫폼을 개발하는 것을 목표로 하고 있습니다. 주요 개발 목표는 다음과 같습니다.

1. **Django Rest Framework(DRF)** 를 활용한 RESTful API 구현
   - 효율적이고 확장 가능한 백엔드 설계
   - API 버전 관리 및 문서화

2. **WebSocket** 을 이용한 실시간 통신 구현
   - 채팅 기능 및 실시간 알림 시스템 개발
   - 효율적인 서버-클라이언트 통신 구조 설계

3. **JWT(JSON Web Token)** 를 이용한 사용자 인증 시스템 구축
   - 안전하고 확장 가능한 사용자 인증 메커니즘 개발
   - 토큰 기반 인증과 세션 기반 인증의 장단점 이해

4. **Class-Based Views(CBV)** 를 통한 CRUD 기능 구현
   - 재사용 가능하고 유지보수가 용이한 view 로직 설계
   - DRF의 generic views 활용 숙달

5. **팀 협업 경험 축적**
   - Git을 활용한 버전, 브랜치 관리 및 협업 워크플로우 확립
   - 팀원끼리 부담없이 물어보고 도와주는 협업 문화 형성

6. **AWS** 를 통한 클라우드 배포
   - 클라우드 인프라 구축 및 관리 경험 습득
   - CI/CD 파이프라인 구축을 통한 자동화된 배포 프로세스 확립

7. **Docker** 를 활용한 일관된 개발 및 운영 환경 구축
   - 컨테이너화된 애플리케이션 개발 및 배포 프로세스 학습

8. **Redis** 를 통한 효율적인 메모리 관리 및 실시간 기능 구현
   - 실시간 데이터 처리 최적화
   - 채팅 기능을 위한 메시지 브로커로 Redis 활용
   - 사용자 접속 상태 관리 및 실시간 알림 기능 구현
  
9. **Daphne**를 활용한 ASGI 서버 구현
   - Django Channels와 Daphne를 이용한 WebSocket 연결 관리
   - 비동기 처리를 통한 고성능 실시간 통신 구현

10. 확장 가능한 **데이터베이스** 설계
   - 복잡한 관계를 가진 데이터 모델 설계 및 구현

<br>

이 프로젝트를 통해 저희 팀은 현대적인 웹 개발 기술 스택을 종합적으로 활용하며, 실무에서 발생할 수 있는 다양한 기술적 도전과제를 해결하는 경험을 쌓을 것입니다. 이를 통해 팀원 각자의 기술적 역량을 향상시키는 동시에, 효과적인 의사소통, 작업 분배, 코드 리뷰 등 개발 과정에서 발생하는 팀원 간의 상호작용을 원활히 관리하고 조율하는 능력도 함께 키우고자 합니다.

<br>

## 3. 기능 명세

#### 1. 사용자 관리 (accounts 앱)

1.1. 인증 및 권한 관리
- 회원가입, 로그인, 로그아웃
- 세션 기반 인증: Django 세션 기반 인증을 사용하며, 로그인한 사용자는 세션을 통해 인증 상태가 유지됩니다.
- 소셜 로그인 : Google 계정으로 소셜 로그인을 지원합니다. JWT 인증을 사용합니다.
- 사용자 권한 : 로그인한 사용자만 특정 기능(채팅, 알림, 게시글 작성 등)을 사용할 수 있습니다.

1.2. 프로필 관리
- 프로필 정보 수정: 사용자는 자신의 프로필 사진, 자기소개 등의 정보를 수정할 수 있습니다.
- 프로필 설정 : 사용자는 자신의 정보 허용 범주를 나를 팔로우하는 사용자, 내가 팔로우하는 사용자, 기타 사용자에 대해 세분화하여 설정할 수 있습니다.
- 다른 사용자 프로필 보기: 사용자는 다른 사용자의 프로필을 볼 수 있습니다.
- 팔로우/언팔로우 기능: 사용자는 다른 사용자를 팔로우/언팔로우 할 수 있으며, 팔로우한 사용자의 활동이 피드에 나타납니다.
- 계정 비활성화 기능 : 계정을 비활성화 할 수 있습니다. 이메일 인증 절차를 거치면 다시 활성화할 수 있습니다.
- 계정 삭제 기능 : 사용자는 자신의 계정을 영구히 삭제할 수 있습니다.

1.3. 비밀번호 관리
- 비밀번호 변경: 사용자는 자신의 비밀번호를 변경할 수 있습니다.

1.4. 사용자 활동 기록
- 마켓 활동 기록: 사용자는 자신이 마켓에 등록한 상품을 확인 할 수 있습니다.

1.5 사용자 추천 기능
- 사용자가 팔로우 하는 사람들이 팔로우하는 사용자, 사용자가 작성한 게시글에 달린 태그와 동일한 태그를 사용한 다른 사용자, 팔로워가 가장 많은 사용자 1위부터 3위를 종합하여 총 15명의 사용자가 추천 목록에 나타납니다.

#### 2. 실시간 알림 기능 (alarm 앱)

2.1. 알림 생성
- 사용자는 새로운 메시지, 팔로우, 댓글 등의 중요한 이벤트가 발생할 때 실시간 알림을 받습니다. 이 알림은 Django Channels와 WebSocket을 통해 실시간으로 전달됩니다.

2.2 메시지 알림
- 새로운 메시지가 생성되면 알림을 생성합니다. 메시지 수신자가 WebSocket 연결 중인 상태(메시지가 생성된 채팅방에 접속해 있는 상태)라면 알림을 생성하지 않습니다.

2.3. 알림 클릭 시 리디렉션
- 알림을 클릭하면 관련된 페이지(예: 댓글이 달린 게시물)로 리디렉션 됩니다.

2.4. 알림 삭제 및 관리
- 사용자는 알림을 개별 또는 일괄 삭제할 수 있습니다.


#### 3. 실시간 채팅 기능 (chat 앱)

3.1. 1대1 실시간 채팅
- 사용자는 다른 사용자와 1대 1로 실시간 채팅을 할 수 있으며, 메시지는 WebSocket을 통해 실시간으로 전송됩니다.

3.2 이미지 첨부 기능
- 사용자는 이미지를 첨부하여 메시지로 전송할 수 있습니다. 5MB 이하로 제한됩니다.

3.2. 채팅 기록 저장 및 조회
- 이전에 주고받은 메시지들은 저장됩니다. 사용자는 채팅방에 다시 들어왔을 때 이전 채팅 기록을 조회할 수 있습니다.

3.3. 채팅방 생성 및 관리
- 사용자는 다른 사용자와의 대화를 시작할 때 새로운 채팅방을 생성하며, 채팅방 목록을 관리할 수 있습니다. 사용자가 채팅방에서 나가면 해당 채팅방이 목록에서 제거됩니다. 사용자가 모두 채팅방에서 나가면 채팅방이 제거됩니다.

3.4. 대화 읽음 처리 기능
- 채팅방에 입장하는 순간 채팅방의 모든 대화를 읽음 처리합니다. 이를 통해 쌓여있던 메시지들을 한 번에 읽음 처리합니다.
- 사용자의 WebSocket 연결 종료 시간을 기록합니다. 만약 메시지 수신자가 WebSocket 연결 중인 상태라면 실시간으로 메시지를 읽음 처리합니다.

#### 4. 게시글 관리 (insta 앱)

4.1. 사진 기반 게시물 작성
- 사용자는 사진과 텍스트가 포함된 게시물을 작성할 수 있습니다. 게시물은 제목 필드가 없으며, 이미지 중심의 SNS입니다.

4.2 피드 기능
- 내가 팔로우 중인 사용자의 게시글이 피드에 나타납니다. 팔로우하는 사용자가 없다면 팔로워가 많은 사용자 1위 부터 10위까지의 게시글이 피드에 나타납니다.

4.3. 게시물 조회 및 태그
- 사용자는 게시물에 달린 태그를 통해 검색하거나 조회할 수 있습니다.

4.4. 게시물에 대한 댓글 및 좋아요
- 사용자는 게시물에 댓글을 달거나 좋아요를 남길 수 있습니다.

#### 5. 사용자 간 직거래 기능 (market 앱)

5.1. 상품(감귤) 게시 및 거래
- 사용자는 상품 이름, 가격, 상품 설명, 재고, 품종, 재배지역, 재배일자, 이미지를 포함하여 상품을 게시할 수 있습니다. 결제 기능을 포함하지 않으며, 사용자가 서로 협의하여 직접 거래하는 방식입니다.

5.2 상품 리뷰 기능
- 상품 게시물에 대한 리뷰를 작성할 수 있습니다. 별점을 줄 수 있으며, 별점의 평균 값이 상품 페이지에 나타납니다.

5.2. 상품 검색 및 조회
- 사용자는 거래할 상품을 검색하고 게시된 상품의 세부 정보를 확인할 수 있습니다. 상품은 키워드로 검색할 수 있습니다.

#### 6. 신고 기능 (report 앱)

6.1. 게시물, 상품
- 사용자는 부적절하거나 불법적인 게시물이나 상품을 신고할 수 있습니다. 신고자는 신고 사유를 작성하여 전송합니다.

6.2. 신고 내용 관리
- 신고된 내용은 관리자 페이지에서 관리되며, 관리자가 신고 사유를 확인하고 적절한 조치를 취할 수 있습니다.

6.3 신고 처리 상태 관리
- 신고된 내용은 관리자 페이지에서 (처리 대기, 처리 중, 해결됨, 반려됨) 처리 상태를 관리할 수 있습니다.

<br>

## 4. 기술 스택 및 아키텍처

### 4.1 기술 스택
<div align=left>
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"> 
  <br>
  
  <img src="https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white"> 
  <img src="https://img.shields.io/badge/css-1572B6?style=for-the-badge&logo=css3&logoColor=white"> 
  <img src="https://img.shields.io/badge/javascript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black"> 
  <br>
  
  <img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white"> 
  <img src="https://img.shields.io/badge/bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white">
  <br>

  <img src="https://img.shields.io/badge/docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/postgreSQL-4169E1?style=for-the-badge&logo=PostgreSQL&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-FF4438?style=for-the-badge&logo=redis&logoColor=white">
  <br>

  <img src="https://img.shields.io/badge/linux-FCC624?style=for-the-badge&logo=linux&logoColor=black"> 
  <img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonwebservices&logoColor=white"> 
  <br>
  
  <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
</div>

<br>

### 4.2 아키텍처

<br>

## 5. 개발 환경 및 배포 URL

### 5.1 개발 환경

- Tools:

    <img src="https://img.shields.io/badge/VSCode-2496ED?style=for-the-badge&logo=VSCode&logoColor=white"/>
    <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">

- Web Framework:

    <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
    <img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white">
    <img src="https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray">

- 배포 환경:

    <img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonwebservices&logoColor=white">

- 협업 툴:

    <img src="https://img.shields.io/badge/discord-5865F2?style=for-the-badge&logo=Discord&logoColor=white">
    <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">
    <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white">
    <img src="https://img.shields.io/badge/figma-F24E1E?style=for-the-badge&logo=Figma&logoColor=white">

### 5.2 배포 URL

- URL:
- 테스트용 계정

```markdown
[일반 유저]
email: test@example.com
pw: xptmxmdbwj123

[관리자 유저]
id: admin
pw: 1234
```

<br>

## 6. API 문서 및 URL 구조

### 6.1 API 문서

- Swagger URL : http://localhost:8000/api/schema/swagger-ui/
- Redoc URl : http://localhost:8000/api/schema/redoc/

<br>

### 6.2 URL 구조

#### 🔑 accounts

| app: accounts | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| signup/ | POST | 회원가입 |  |  |  |
| login/ | POST | 로그인 |  |  |  |
| logout/ | POST | 로그아웃 | ✅ |  |  |
| change-password/ | PUT | 비밀번호 변경 | ✅ | ✅ |  |
| deactivate/ | POST | 계정 비활성화 | ✅ | ✅ |  |
| delete/ | POST | 계정 삭제 | ✅ | ✅ |  |
| request-reactivation/ | POST | 계정 재활성화 요청 |  |  |  |
| activate/\<uidb64\>/\<token\>/ | GET | 계정 활성화 |  |  | 유효한 토큰 |
| profile/\<str:username\>/ | GET | 유저 프로필 조회 | ✅ |  |  |
| profile/ | PUT, PATCH | 유저 프로필 수정 | ✅ | ✅ |  |
| privacy-settings/ | GET, PUT, PATCH | 개인정보 설정 조회 | ✅ | ✅ |  |
| follow/\<int:pk\>/ | POST | 사용자 팔로우 | ✅ |  |  |
| unfollow/\<int:pk\>/ | DELETE | 사용자 언팔로우 | ✅ |  |  |
| search/ | GET | 유저 프로필 검색 | ✅ |  |  |
| recommend/ | GET | 친구 추천 | ✅ |  |  |

#### 📢 alarm

| app: alarm | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| alarms/ | GET | 현재 로그인한 사용자의 알림 목록 조회 | ✅ |  |  |
| alarms/\<int:alarm_id\>/ | DELETE | 특정 알림 삭제 | ✅ |  | 해당 알림의 수신자여야 함 |
| alarms/bulk-delete/ | DELETE | 모든 알림 삭제 | ✅ |  | 해당 알림의 수신자여야 함 |

#### 🤝 chat

| app: chat | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| / | GET | 현재 사용자가 속한 채팅방 목록 조회 | ✅ |  |  |
| /create/ | POST | 1대1 채팅방 생성 | ✅ |  |  |
| /\<uuid:room_id\>/ | GET | 특정 채팅방 정보 조회 | ✅ |  | 해당 채팅방 참여자여야 함 |
| /\<uuid:room_id\>/leave/ | DELETE | 채팅방 나가기 | ✅ |  | 해당 채팅방 참여자여야 함 |
| /\<uuid:room_id\>/messages/ | GET | 채팅방 내 메시지 목록 조회 | ✅ |  | 해당 채팅방 참여자여야 함 |
| /\<uuid:room_id\>/messages/send/ | POST | 메시지 생성 | ✅ |  | 해당 채팅방 참여자여야 함 |
| /\<uuid:room_id\>/messages/search/ | GET | 메시지 검색 | ✅ |  | 해당 채팅방 참여자여야 함 |

#### 📷 insta

| app: insta | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| /posts/ | GET | 게시글 목록 조회 |  |  |  |
| /posts/\<int:pk\>/ | GET | 게시글 상세 조회 |  |  |  |
| /posts/create/ | POST | 게시글 작성 | ✅ |  |  |
| /posts/\<int:pk\>/delete/ | DELETE | 게시글 삭제 | ✅ | ✅ |  |
| /posts/\<int:post_id\>/comments/ | GET, POST | 게시글에 댓글 목록 조회 및 댓글 작성 | ✅ |  |  |
| /comments/\<int:pk\>/ | GET | 댓글 상세 조회 | ✅ |  |  |
| /posts/\<int:post_id\>/like/ | POST | 게시글 좋아요 | ✅ |  |  |
| /posts/search/ | GET | 태그로 게시글 검색 |  |  |  |

#### 🛒 products

| app: products | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| /products/ | GET | 상품 목록 조회 |  |  |  |
| /products/create/ | POST | 상품 생성 | ✅ |  |  |
| /products/\<int:id\>/ | GET | 상품 상세 조회 |  |  |  |
| /products/\<int:id\>/update/ | PATCH | 상품 정보 수정 | ✅ | ✅ |  |
| /products/\<int:id\>/delete/ | DELETE | 상품 삭제 | ✅ | ✅ |  |
| /products/\<int:product_id\>/reviews/\<int:id\>/delete/ | DELETE | 상품 리뷰 삭제 | ✅ | ✅ |  |

#### 🚨 report

| app: report | HTTP Method | 설명 | 로그인 권한 필요 | 작성자 권한 필요 | 추가 권한 |
| :-- | --- | --- | :-: | :-: | --- |
| /create/ | POST | 신고 생성 | ✅ |  |  |

<br>

## 7. 프로젝트 구조와 개발 일정

### 7.1 프로젝트 구조

```
📦BE
 ┣ 📂accounts
 ┃ ┣ 📂migrations
 ┃ ┣ 📂tests
 ┃ ┃ ┣ 📜test_views_account.py
 ┃ ┃ ┣ 📜test_views_profile.py
 ┃ ┃ ┗ 📜test_views_recommendation.py
 ┃ ┣ 📂views
 ┃ ┃ ┣ 📜account.py
 ┃ ┃ ┣ 📜profile.py
 ┃ ┃ ┗ 📜recommendation.py 
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜auth_backends.py     # 계정 비활성화 기능 구현을 위한 custom 인증 함수
 ┃ ┣ 📜filters.py           # 검색, 친구 추천기능 구현
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┗ 📜urls.py
 ┣ 📂alarm                  # 실시간 알람 생성을 위해 WebSocket 연결 사용
 ┃ ┣ 📂migrations
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜comsumers.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜routing.py           # 특정 URL에 대한 WebSocket 연결
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜signals.py           # 특정 이벤트가 발생할 때 특정 동작을 수행하게 설정  
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┣ 📜views.py
 ┣ 📂chat                   # 실시간 채팅 구현을 위해 WebSocket 연결 사용
 ┃ ┣ 📂migrations
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜comsumers.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜routing.py           # 특정 URL에 대한 WebSocket 연결          
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┣ 📜views.py
 ┣ 📂config
 ┃ ┣ 📜asgi.py              # 비동기 요청을 처리
 ┃ ┣ 📜pagination.py        # 공통으로 사용되는 pagination
 ┃ ┣ 📜settings.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜wsgi.py
 ┣ 📂insta
 ┃ ┣ 📂migrations
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜filters.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py
 ┣ 📂market
 ┃ ┣ 📂migrations
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py
 ┣ 📂report
 ┃ ┣ 📂migrations
 ┃ ┣ 📜admin.py
 ┃ ┣ 📜apps.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py
 ┣ 📜.gitignore
 ┣ 📜README.md
 ┣ 📜docker-compose.yml
 ┣ 📜manage.py
 ┗ 📜requirements.txt
```
</details>

<details>
    <summary><h4>📌 FE</h4></summary>

```

```
</details>

<br>

### 7.2 개발 일정

```mermaid
gantt
    title 감귤하우스 개발 일정표
    dateFormat  YYYY-MM-DD
    axisFormat  %m-%d

    section 기획
    요구사항 분석 / 기획         : des1, 2024-09-23, 2d
    ERD 및 WBS 작성             : des2, 2024-09-23, 2d
    프로젝트 초기 세팅           : des4, 2024-09-23, 2d

    section BE
    모델 설계                       : des5, 2024-09-25, 4d
    URL 설계                        : des8, 2024-9-25, 4d
    view 설계                       : des7, 2024-09-25, 4d
    시리얼라이저 설계                 : des6, 2024-09-27, 4d
    세부 기능 구현                    : des9, 2024-09-29, 7d
    버그 수정                        : des9, 2024-10-01, 7d
    테스트 코드 작성                  : des9, 2024-10-04, 4d

    section FE
    부트스트랩 적용                   : des10, 2024-10-08, 2d

    section 테스트 및 통합/배포
    테스트                          : des13, 2024-10-10, 2d
    통합/배포                            : des12, 2024-10-10, 2d

    section 발표 준비
    README 작성                      : des15, 2024-10-08, 5d
    시연 영상                        : des14, 2024-10-12, 1d

```

<br>

## 8. ERD
<img src="static/images/readme_img/ERD.png" width="100%"/>

<h4>관계도 해설</h4>

1. 사용자 관리:
    - User 테이블이 중심이 되어 사용자의 기본 정보를 저장합니다.
    - SocialAccount 테이블은 소셜 로그인 기능을 지원합니다.
    - PrivacySettings 테이블로 사용자의 개인정보 공개 설정을 관리합니다.
    - Follow 테이블로 사용자 간의 팔로우 관계를 표현합니다.

2. SNS 기능:
    - Post, Comment, Like 테이블들로 게시물, 댓글, 좋아요 기능을 구현합니다.
    - PostImage 테이블은 게시물에 여러 이미지를 첨부할 수 있게 합니다.

3. 메시지 시스템:
    - ChatRoom, Message 테이블은 사용자 간 채팅 기능을 제공합니다.
    - WebSocketConnection 테이블은 실시간 통신을 관리합니다.
        - 현재 사용자가 채팅방에 연결되어 있는지를 확인할 수 있습니다.
        - 채팅방에 연결되어 있는 상태라면 새로운 메시지를 읽음 처리합니다.
        - 채팅방에 연결되어 있는 상태라면 메시지 알림을 보내지 않습니다.

4. 알림 시스템:
    - 새로운 메시지에 대한 알림을 생성합니다.
    - 다른 사용자가 나를 팔로우 했을 때 알림
    - 내 게시물에 댓글이 달렸을 때 알림
    - 내 게시물에 좋아요가 달렸을 때 알림

5. Market 기능:
    - Product 테이블은 판매 상품 정보를 저장합니다.
    - ProductImage 테이블로 상품 이미지를 관리합니다.
    - Review 테이블은 상품에 대한 리뷰를 저장합니다.

6. 신고 시스템:
    - Report 테이블로 부적절한 컨텐츠 신고를 관리합니다.

7. 이미지 파일 관리:
    - PostImage와 ProductImage를 분리함으로써, SNS 기능과 Market 기능 각각의 요구사항에 최적화된 방식으로 이미지를 관리합니다.

주요 관계:
- 사용자(User)는 여러 게시물(Post), 댓글(Comment), 좋아요(Like), 상품(Product), 리뷰(Review)를 가질 수 있습니다.
- 게시물(Post)은 여러 이미지(PostImage), 댓글(Comment), 좋아요(Like)를 가질 수 있습니다.
- 상품(Product)은 여러 이미지(ProductImage)와 리뷰(Review)를 가질 수 있습니다.
- 사용자들은 서로 팔로우할 수 있고(Follow), 채팅방(ChatRoom)에 참여하여 메시지(Message)를 주고받을 수 있습니다.

<br>

## 9. 시연 영상

<br>

## 10. 트러블 슈팅

<br>

## 11. 🤙 컨벤션

프로젝트의 일관성 유지와 협업 효율성을 높이기 위해 아래 컨벤션을 따릅니다.

<br>

### 📌 Git 컨벤션
  

#### 커밋 메시지 구조
커밋 메시지는 크게 두 부분으로 구성됩니다.

```
<이모지> <타입>: <제목>

<본문>
```

#### 타입
| 이모지 | 커밋 메세지 | 타입 | 설명 |
|:---:|:---:|:---:|:---|
| ✨ | `:sparkles:` | feat: | 새로운 기능 추가 |
| 🐛 | `:bug:` | fix: | 버그 수정 |
| 📝 | `:memo:` | docs: | 문서 작업 |
| 🎨 | `:art:` | style: | 코드 포맷팅, 세미콜론 누락, 코드 변경이 없는 경우 |
| ♻️ | `:recycle:` | refactor: | 코드 리팩토링 |
| 🧪 | `:test_tube:` | test: | 테스트 |
| 🚀 | `:rocket:` | deploy: | 배포 |
| 🔧 | `:wrench:` | conf: | 빌드, 환경 설정 |
| ✏ | `:pencil2:` | chore: | 기타 작업 |
| 🔀 | `:twisted_rightwards_arrows:` | merge: | 브랜치 병합 |
| 🗃️ | `:card_file_box:` | db: | 데이터베이스 관련 변경 |


#### 제목 규칙
- 50자 이내로 작성
- 마침표 사용하지 않음
- 현재 시제 사용
- 명령문으로 작성

#### 본문 규칙(선택 사항)
- 72자 단위로 줄 바꿈
- 어떻게 보다는 무엇을, 왜에 대해 설명
- 제목과 본문 사이에 빈 줄 추가

### 브랜치 전략

#### 메인 브랜치
main: 프로젝트의 메인 브랜치

#### 보조 브랜치
feature/<기능명>: 새로운 기능 개발을 위한 브랜치

#### 병합 전략
- Pull Request(PR)를 사용하여 코드 리뷰를 진행
- 최소 1명 이상의 리뷰어의 승인을 받아야 병합할 수 있음
- 병합하기 전에 충돌을 해결

### 기타 규칙
- .gitignore 파일을 적극적으로 활용하여 불필요한 파일이 저장소에 포함되지 않도록 합니다.
</details>

<br>

### 📌 Code 컨벤션
  
#### 일반 규칙

- PEP 8 규칙을 준수합니다.
- Black formatter를 사용합니다.
- 각 파일의 import 문은 아래의 순서로 정렬합니다.
    1. 표준 라이브러리
    2. 서드파티 라이브러리
    3. 로컬 애플리케이션/라이브러리

#### Model 컨벤션

- 모델 클래스는 단수형 명사로 명명합니다.
- 필드 이름은 소문자 스네이크 케이스를 사용합니다.
- 관계 필드는 관련 모델의 이름을 사용합니다.
- Meta 클래스는 필드 정의 다음에 위치시킵니다.
- 커스텀 메서드는 Meta 클래스 다음에 위치시킵니다.
- 주석은 독스트링으로 작성합니다.

#### Serializer 컨벤션

- Serializer 클래스 이름은 관련 모델 이름 뒤에 'Serializer'를 붙입니다.
- Meta 클래스는 필드 정의 바로 다음에 위치시킵니다.
- fields 속성에서 필드를 명시적으로 나열합니다. __all__의 사용은 지양합니다.
- 중첩된 serializer는 명시적으로 정의합니다.
- 유효성 검사 메서드는 validate_<field_name> 형식으로 명명합니다.
- 주석은 독스트링으로 작성합니다.

#### View 컨벤션

- 클래스 기반 뷰를 사용합니다.
- 뷰 클래스 이름은 동작을 설명하는 동사로 시작하고 'View'로 끝납니다.
- 주석은 독스트링으로 작성합니다.

#### URL 컨벤션

- URL 패턴은 명확하고 RESTful한 구조를 따릅니다.
- URL 이름은 앱 이름을 접두사로 사용합니다.

#### 코드 리뷰

1. 기능 구현이 완료되면 push 하고 pr 요청
2. pr 메세지에는 어떤 기능을 구현했는지 작성
3. pr 요청을 보내고 다음 날 9시 전까지 comment 생성
4. pr 요청을 보낸 사람은 9시에 답변 생성
5. 답변 생성이 끝나면 팀원들에게 알리고 시간을 정해 답변 읽기
6. 피드백 후 merge
</details>

<br>

## 12. 프로젝트를 마치며

김동규
> Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

이원재
> Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

문지영
> Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

박성재
> Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.