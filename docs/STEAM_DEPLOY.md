# Steam 자동 배포 셋업 (App ID 4718470)

태그(`v*`)를 푸시하면 CI가 **Windows exe + macOS .app**을 빌드하고,
secrets가 설정돼 있으면 **SteamPipe로 자동 업로드 후 `beta` 브랜치에 라이브**합니다.

> ⚠ **default 브랜치 승격만은 수동**입니다 — Valve가 default 라이브에 웹 2FA 확인을
> 강제하기 때문에 어떤 CI로도 자동화할 수 없습니다. 파트너 사이트 Builds 페이지에서
> beta에 올라온 빌드를 확인하고 "Set live on default" 클릭 한 번이면 됩니다.

## 1회 셋업 (아래 순서대로)

### ① 파트너 사이트 — depot / 브랜치 / 실행 옵션

1. **macOS depot 생성**: App Admin → SteamPipe → Depots → *Add a new depot*
   - 이름: `DungeonDoor macOS Content`, Depot ID: **4718472** (자동 할당되는 다음 번호)
   - Depot 속성에서 OS = **macOS** 로 설정 (기존 4718471은 Windows)
   - 새 depot을 스토어 패키지에 추가 (Associated Packages)
2. **launch option 추가**: Installation → General Installation
   - New Launch Option: Executable = `DungeonDoor.app`, Operating System = **macOS**
   - (기존 `game.exe` 옵션은 OS = Windows 로 지정돼 있는지 확인)
3. **`beta` 브랜치 생성**: SteamPipe → Builds → *Create new branch* → 이름 `beta`
4. **Publish** (Steamworks 설정 게시)

### ② 빌더 계정 인증 → GitHub secrets

CI가 steamcmd로 로그인할 자격 증명입니다. 본 계정을 써도 되지만
권한을 좁힌 **빌더 전용 계정**(Upload to SteamPipe + Publish 권한만) 권장.

#### 방식 A — TOTP (권장, 만료 없음)

Steam Guard 모바일 인증기의 `shared_secret`으로 CI가 **매 실행마다 2FA 코드를 새로
생성**해 로그인합니다. config.vdf처럼 저장된 토큰이 없으니 만료·수동 갱신이 없습니다.

`shared_secret` 얻기 (인증기를 아래 도구로 등록해야 추출 가능):

- **Steam Desktop Authenticator** (Windows): 계정 등록 후 `maFiles/<steamid>.maFile`
  (JSON)의 `"shared_secret"` 값
- **steamguard-cli** (macOS/Linux): `steamguard setup`으로 등록 후
  `~/.config/steamguard-cli/maFiles/<계정>.maFile`의 `"shared_secret"` 값

> ⚠ 인증기를 SDA/steamguard-cli로 등록하면 휴대폰 Steam 앱 인증기는 해제됩니다.
> 빌더 전용 계정을 쓰면 본계정 인증기는 그대로 둘 수 있어 깔끔합니다.
> maFile은 계정 탈취에 쓰일 수 있는 민감 파일 — 리포에 커밋 금지.

GitHub 저장소 → Settings → Secrets and variables → Actions:

| Secret | 값 |
|---|---|
| `STEAM_USERNAME` | 빌더 계정명 |
| `STEAM_PASSWORD` | 빌더 계정 비밀번호 |
| `STEAM_SHARED_SECRET` | maFile의 `shared_secret` 값 (base64 문자열 그대로) |

`STEAM_SHARED_SECRET` + `STEAM_PASSWORD`가 설정돼 있으면 워크플로우가 자동으로
TOTP 방식을 사용하고 `STEAM_CONFIG_VDF`는 무시합니다 (지워도 됨).

#### 방식 B — config.vdf (폴백, 비권장)

> ⚠ config.vdf의 리프레시 토큰은 **로그인할 때마다 회전**하므로 CI에서 한 번 쓰면
> 다음 실행에서 `Access Denied`가 나기 쉽습니다. 매번 재추출해야 해서 비권장.

이 맥에서:

```bash
brew install steamcmd
steamcmd +login <계정명> +quit     # 비밀번호 + Steam Guard 코드 1회 입력
# 로그인 성공 후 자격 캐시를 base64로 인코딩해 클립보드에 복사:
base64 -i ~/Library/Application\ Support/Steam/config/config.vdf | pbcopy
```

| Secret | 값 |
|---|---|
| `STEAM_USERNAME` | 빌더 계정명 |
| `STEAM_CONFIG_VDF` | **base64 인코딩된** `config.vdf` (원문을 넣으면 `base64: invalid input` 오류 발생) |

### ③ 끝. 이후 릴리스 흐름

```bash
git tag -a v1.4.0 -m "..." && git push origin main v1.4.0
```

→ CI가 Windows/macOS 빌드 → GitHub Release 첨부 → Steam `beta` 브랜치 자동 라이브
→ 파트너 사이트에서 default 승격 클릭 (유일한 수동 단계)

## 구조

```
build/
├── windows/   → depot 4718471 (game.exe + _internal/)
└── macos/     → depot 4718472 (DungeonDoor.app)
```

- macOS 빌드는 **Apple Silicon(arm64)** 대상 (GitHub macos-latest 러너).
  Intel 맥 지원이 필요하면 macos-15-intel 러너 잡을 추가할 것.
- macOS .app은 미서명 — Steam 클라이언트로 설치되는 경우 quarantine이 붙지 않아
  실행에 문제 없음. (스토어 외 배포 시에는 공증 필요)
- secrets 미설정 시 deploy-steam 잡은 조용히 스킵 → 기존 수동 업로드 흐름 그대로 사용 가능.
