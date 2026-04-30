[프로젝트 계획서] 심플 2D 비트 아트
로그라이크 게임
이 문서는 Claude Code 및 Qwen 2.5 Coder와 같은 AI 에이전트를 활용하여 스팀 배포용 2D
로그라이크 게임을 개발하기 위한 상세 지침서입니다.
1. 프로젝트 개요
● 게임 제목: (미정 - 프로젝트 코드네임: BitCrawler)
● 장르: 2D 그리드 기반 로그라이크
● 비주얼 스타일: 16x16 픽셀/비트 아트 (마인크래프트 2D 스타일)
● 핵심 목표: 최소한의 리소스로 '한 판'의 재미를 극대화하여 스팀 배포
2. 기술 스택 (Tech Stack)
구분 도구 역할
언어 Python 3.10+ 주요 로직 및 게임 엔진 구현
라이브러리 Pygame-CE (Community

Edition)

그래픽 렌더링, 사운드, 입력
처리

데이터 포맷 JSON / TOML 아이템, 몬스터 스탯 및 설정

관리

개발 조력자 Claude Code / Qwen 2.5 Coder 코드 생성 및 시스템 설계

자동화

3. 시스템 아키텍처
AI가 코드를 이해하고 확장하기 쉽도록 데이터 중심(Data-Driven) 및 모듈화 구조를
채택합니다.
● Core: 메인 루프, 이벤트 루프, 카메라 시스템
● Map System: 그리드 기반 절차적 맵 생성 (Room-based 또는 Random Walk)
● Entity System: 컴포넌트 기반 캐릭터 및 몬스터 관리
● Data Layer: data/ 폴더의 JSON 파일을 읽어 엔티티 속성 부여
4. 개발 로드맵
Phase 1: 기본 골격 구축 (Core Framework)
● Pygame-CE 기본 윈도우 및 해상도(320x180 업스케일링) 설정
● 그리드 기반 이동 시스템 (Input Handler)
● 간단한 2차원 배열 맵 렌더링
Phase 2: 로그라이크 핵심 로직 (Roguelike Mechanics)

● 절차적 맵 생성 알고리즘 구현 (방과 복도 생성)
● 기본 전투 시스템 (Turn-based 또는 Simple Real-time)
● 아이템 습득 및 인벤토리 기본 기능
Phase 3: 데이터 기반 확장 (Content Expansion)
● JSON 파일을 활용한 몬스터/아이템 데이터베이스 구축
● AI(Qwen)를 활용한 대량의 아이템 스탯 생성 및 밸런싱
● 레벨업 및 캐릭터 성장 시스템
Phase 4: 폴리싱 및 배포 (Polishing & Steam)
● 화면 흔들림(Screen Shake), 파티클 이펙트 추가
● Steamworks SDK 연동 (도전과제, 클라우드 저장)
● PyInstaller를 활용한 실행 파일(.exe) 패키징
5. AI 에이전트 지시 가이드 (Prompting Guide)
Claude Code나 Qwen에게 지시할 때 아래 형식을 사용하세요.
"Python Pygame-CE 환경에서 [특정 기능]을 구현해줘.
- 파일 위치: entities/enemy.py
- 규칙: 모든 데이터는 data/enemies.json에서 읽어와야 함
- 스타일: 16x16 그리드 좌표계를 엄격히 준수할 것"
이 계획서는 개발 진행 상황에 따라 지속적으로 업데이트될 예정입니다.