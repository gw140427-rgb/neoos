# VPS Service for blitz.cloud

## blitz.cloud에 올리는 방법 (카드 없이 무료)

1. https://beta.blitz.cloud/auth/login?register=1 에서 가입 (카드 필요 없음)
2. 주소 만들기: 예) yangyang.blitz.cloud Claim
3. "Deploy" -> "Docker image" 또는 "GitHub project" 선택
   - 옵션 A: GitHub로 올리기
     - 이 폴더를 GitHub에 push (예: github.com/yangyang/vps-service)
     - blitz에서 GitHub 연결 -> 자동 빌드
   - 옵션 B: Docker Hub로 올리기
     - docker build -t yangyang/vps-service .
     - docker push yangyang/vps-service
     - blitz에서 이미지 이름 입력: yangyang/vps-service
4. Short name 입력: 예) vps  -> https://vps.yangyang.blitz.cloud 로 접속됨
5. blitz가 자동으로 포트 8000 감지, HTTPS 발급, 실행

## 로컬 테스트
pip install -r requirements.txt
uvicorn app_docker:app --host 0.0.0.0 --port 8000
# 대시보드: http://localhost:8000/dashboard/
# API: http://localhost:8000/docs
