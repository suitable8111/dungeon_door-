# Steam 연동 라이브러리 (도전과제 동기화)

**App ID: 4718470**

이 폴더의 DLL 2개가 빌드 시 `game.exe` 옆에 복사되면 스팀 도전과제 동기화가 활성화됩니다.
없어도 게임은 정상 동작합니다 (도전과제는 로컬 저장만).

| 파일 | 출처 |
|---|---|
| `steam_api64.dll` | Steamworks SDK → `sdk/redistributable_bin/win64/steam_api64.dll` — [파트너 사이트](https://partner.steamgames.com/downloads/steamworks_sdk.zip)에서 SDK 다운로드 후 여기에 복사 |
| `SteamworksPy64.dll` | CI가 [SteamworksPy 릴리스](https://github.com/philippj/SteamworksPy/releases)에서 자동 다운로드 (수동 배치도 가능) |

## 활성화 절차

1. Steamworks SDK를 받아 `steam_api64.dll`을 이 폴더에 넣고 커밋
2. 태그 푸시 → CI가 SteamworksPy(파이썬 패키지 + DLL)를 설치/다운로드하고 빌드에 번들
3. 파트너 사이트 Stats & Achievements에 도전과제 등록 후 Publish
   (API 이름은 `core/achievements.py`의 `ACHIEVEMENTS` 키와 동일해야 함)

## 로컬 개발 테스트 (Windows)

스팀 클라이언트 실행 상태에서, `game.exe` 옆에 `steam_appid.txt` 파일을 만들고
내용에 `4718470` 한 줄만 넣으면 스팀 밖에서 실행해도 연동됩니다.
(`steam_appid.txt`는 배포 빌드에 포함하지 말 것 — .gitignore 처리됨)
