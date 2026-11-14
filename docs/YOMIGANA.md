# Yomigana: 다른 컴퓨터에서 적용하거나 이어 작업하기

이 저장소는 Steam판 괭이갈매기 울 적에 EP1–4와 EP5–8의 일본어 루비 엔진 및
독음 변환 도구를 관리합니다. EP1–4 브랜치 `feat/japanese-ruby`는 원본
07th-Mod `mod`의 `ba457e4261f9876a707d12ee03fd22dc6b0a2478`에서 시작합니다.
현재 Windows 답편 브랜치 `feat/japanese-ruby-ep5-8`은 `e06c6a2`에서 시작해
EP1–4 루비 커밋들을 재적용하고 답편용 보정을 추가합니다.

답편 브랜치는 설치된 `0.u`에서 실제 호출되는 `simul_lipall`, `simul_multfont`,
`simul_nextld`, `simul_nextvoice` 등의 명령이 `e06c6a2`에는 구현되어 있고
`ba457e4`에는 없어서 그 기준을 보존합니다. 이것은 스크립트 호환성 근거이며,
설치 실행 파일의 저장소 출처를 입증하지는 않습니다. 두 브랜치는 같은 루비
파서와 그리기 코드를 공유하고, 답편 브랜치에는 추가 보정만 둡니다.

현재 Mac 배포본은 [v0.1.0-macos-arm64 (pre-release)](https://github.com/lyra95/ponscripter-fork/releases/tag/v0.1.0-macos-arm64)입니다.
2026-11-14에 새 GitHub clone과 새 Python 가상환경에서 테스트 7개 및 독립 파서를
확인했고, 배포 ZIP의 전체 스크립트 적용·Mac 실행·기본 저장 경로·재시작/로드·복원을
검증했습니다. 기존 개인 작업 폴더가 필요한 설치 경로는 없습니다.

## 어디에 무엇을 보관하는가

| 보관 위치 | 내용 |
| --- | --- |
| 이 Git 저장소 | C++ 엔진 수정, 독음 생성 코드와 인명 사전, 테스트, 빌드/이관 문서, 적용 전후 사진 |
| GitHub Releases | 검증한 Mac 엔진 실행 파일, 필요한 dylib, 적용·복구 도구, 빌드 정보와 체크섬 |
| 사용자의 별도 개인 백업 | 최신 세이브, 본인 게임의 수정 전 앱/스크립트, 로컬 설치 기록 |
| Steam 설치 폴더 | 게임 원본, 이미지/음성/음악 및 본인이 적용한 호환 모드 |

현재 작업 폴더나 Python 가상환경을 옮길 필요는 없습니다. 새 컴퓨터에서 저장소를
clone하고 의존성을 다시 설치합니다. **세이브와 원본 백업은 Git/Release에 올리지
않으므로 별도로 복사해야 합니다.** 예전 작업 시작 시점 백업과 최신 진행을 구분하세요.

## 1. Steam에서 게임 설치 폴더 찾기

기본 설치 위치:

- Windows: `C:\Program Files (x86)\Steam\steamapps\common\Umineko`
- macOS: `~/Library/Application Support/Steam/steamapps/common/Umineko`

다른 드라이브/Steam 라이브러리를 선택했으면 그 위치가 다릅니다.
**Steam 라이브러리 → 게임 우클릭 → 관리 → 로컬 파일 탐색**으로 연 폴더를
설치 도구의 `--game-dir`에 지정하세요. 도구는 기본 경로를 강제로 가정하지 않습니다.

### Steam 기본 설치와 모드 전제

Steam에서 게임을 설치하는 것이 출발점입니다. 다만 현재 검증된 변환 대상은
**07th-Mod 기반 한·일 대사가 함께 있는 패치의 `0.u`**입니다. 설치 답편에서
확인한 패치는 창 제목에 `검수패치 26.08.10`이 표시되는 버전입니다.

게임 폴더에 `0.u`가 있고, 그 안에 `langjp`, `langen`, `rubyon 17,17`,
`*clear_text_and_save_backlog`, 답편의 `simul_*` 명령 호출이 있어야 합니다. Steam 기본 파일만 있고 `0.utf`만
있다면, 먼저 해당 게임용 호환 07th-Mod/언어 패치를 준비해야 합니다.
**Steam 기본 설치만으로 이 변환 도구가 즉시 적용된다고 가정하지 마세요.**
`0.utf`를 임의로 `0.u`로 바꾸는 방법은 지원하지 않습니다.

게임 이미지·음성·모드 자산과 대사 전체는 이 저장소나 Release에 포함하지 않습니다.
엔진은 독음을 자동으로 추측하지 않으며, `｜漢字《かんじ》` 표기가 있는 대사가 필요합니다.

## 2. Windows 답편(EP5–8) 엔진 빌드 및 적용

PowerShell에서:

```powershell
git clone --branch feat/japanese-ruby-ep5-8 https://github.com/lyra95/ponscripter-fork.git
cd ponscripter-fork
uv sync --locked
```

독음 생성은 **원본을 덮어쓰지 않고 다른 파일로** 합니다. 출력은 게임 밖의 작업
폴더에 두고, Windows용 엔진을 준비한 뒤 게임을 종료한 상태에서 적용하세요.

```powershell
uv run --locked python tools/yomigana/annotate.py `
  "C:\Program Files (x86)\Steam\steamapps\common\Umineko\0.u" `
  ".\local-output\0.u"
```

출력 옆에 `0.report.json`이 만들어집니다. 기존 루비 파일의 중복 변환이나
지원하지 않는 스크립트는 거부합니다. 자동 독음이므로 문맥/특수 독음 검수가 필요합니다.
원본과 한글 행/명령/줄바꿈이 보존되는지 검사합니다.

자세한 MINGW32 빌드·Steam SDK DLL·설치 백업 절차는
[Windows 빌드 안내](WINDOWS_BUILD.md)를 따릅니다. 2026-11-14에 이 답편
브랜치를 다시 빌드해 x86 실행 파일과 Win32 SDK DLL을 만들고 답편 게임 폴더에
적용했습니다. 적용 전 실행 파일·DLL·`0.u`를 백업했고, `0.u`와 세이브는 변경하지
않았습니다. 재빌드 후 게임 실행은 아직 확인하지 않았습니다. 현재 게임이 실제
사용하는 저장 폴더(`mysav` 등)를 보존하고, 실행 파일과 DLL을 한 쌍으로 백업하세요.

## 3. Mac Release 적용

[Releases](https://github.com/lyra95/ponscripter-fork/releases)에서 Mac ZIP과
`SHA256SUMS.txt`를 받습니다. 현재 최초 빌드는 **Apple Silicon(arm64), macOS 26.0 이상**입니다.
Intel Mac/이전 macOS용으로 검증한 빌드가 아닙니다. 실제 요구 버전과 파일 해시는
ZIP 안의 `BUILD_INFO.json`에도 기록됩니다. 로컬 ad-hoc 서명이며 Apple 공증본은 아닙니다.

먼저 ZIP과 `SHA256SUMS.txt`가 있는 다운로드 폴더에서 확인합니다.

```bash
shasum -a 256 -c SHA256SUMS.txt
```

ZIP을 풀고, 그 안의 폴더에서 실행합니다. 게임과 Steam Cloud 동기화를 마무리하고
게임을 종료한 상태여야 합니다. Python 3.9 이상과 pip가 필요합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/yomigana/requirements.txt
.venv/bin/python tools/yomigana/apply_macos.py \
  --game-dir "$HOME/Library/Application Support/Steam/steamapps/common/Umineko" \
  --release-dir .
```

사용자 지정 Steam 라이브러리라면 `--game-dir`을 바꿉니다.

도구는 독음을 생성하고, 현재 앱·원본 `0.u`·현재 `saves/`를 별도 백업한 뒤
실행 파일/라이브러리와 `0.u`를 교체합니다. 앱의 원래 아이콘 등은 로컬에서 유지합니다.
백업 위치는 출력되며, 기본값은 게임 폴더의 상위에 있는 `yomigana-backups/`입니다.
세이브를 지우거나 과거 진행으로 덮어쓰지 않습니다. 이미 루비가 들어간 스크립트의
중복 설치는 거부합니다.

설치 후 평소처럼 Steam에서 실행하고 **로드 메뉴로 기존 슬롯을 불러옵니다**.
언어 설정을 일본어로 바꾸면 루비가 나옵니다. 자동으로 마지막 장면에 이어지는
기능을 새로 추가한 것은 아닙니다.

복원(현재 진행 유지):

```bash
.venv/bin/python tools/yomigana/apply_macos.py \
  --game-dir "$HOME/Library/Application Support/Steam/steamapps/common/Umineko" \
  --restore "/본인/백업/Umineko-날짜"
```

Apple이 다운로드한 실행 파일을 차단하면 먼저 출처와 체크섬을 확인하고 macOS의
개인정보 보호 및 보안 설정에서 해당 실행을 허용하는 절차를 따르세요. 도구는 시스템
보안 설정을 자동으로 변경하지 않습니다.

## 4. Mac 소스 빌드와 Release 재생성

현재 검증한 Python 도구는 `fugashi 1.5.2`, `unidic-lite 1.0.8`입니다.
빌드에는 CMake 4.4.4 및 Apple Clang을 사용했습니다. Homebrew에 SDL2 계열,
SMPEG2, FreeType, PNG/JPEG, Ogg/Vorbis 등 개발 라이브러리가 필요합니다.

```bash
uv run --locked python tools/yomigana/fetch_steam_sdk.py --platform macos
cmake -S . -B build -DCMAKE_PREFIX_PATH=/opt/homebrew \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUSE_CPU_GFX=OFF -DUSE_STEAM=ON \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.8 -DCMAKE_CXX_STANDARD=11 \
  -DCMAKE_CXX_FLAGS=-Wno-narrowing
cmake --build build -j 8
```

원본/현재 앱을 **읽기 전용 템플릿**으로 써서 별도 출력 앱에 라이브러리를 묶습니다.
출력 경로는 아직 존재하지 않는 새 경로여야 합니다. 실제 설치 앱을 출력으로 지정하지 마세요.

```bash
uv run --locked python tools/yomigana/bundle_macos.py \
  --app-template "$HOME/Library/Application Support/Steam/steamapps/common/Umineko/Umineko1to4.app" \
  --binary build/src/ponscr --output release-output/staging/Umineko1to4.app \
  --manifest release-output/libraries.json
uv run --locked python tools/yomigana/package_macos.py \
  --app release-output/staging/Umineko1to4.app --version 0.1.0 \
  --output release-output/assets --library-sources release-output/libraries.json
```

패키저는 앱의 아이콘·게임 파일을 제외하고 엔진/라이브러리와 이 도구만 ZIP에 넣습니다.
최소 macOS 버전을 바이너리에서 측정하고, SDK 및 라이브러리 정보·체크섬을 남깁니다.
SDL2-compat가 동적으로 여는 SDL3의 별칭도 보존합니다.

기본 저장 경로 및 재실행 회귀 검증은 실제 게임을 변경하지 않는 복사본에서 합니다.
로컬 게임의 폰트만 읽고, 테스트용 대사/저장 파일은 임시 폴더에 만듭니다.

```bash
uv run --locked python tools/yomigana/tests/test_mac_runtime.py \
  --app release-output/staging/Umineko1to4.app \
  --fonts "$HOME/Library/Application Support/Steam/steamapps/common/Umineko/fonts"
```

## 검증 범위와 알려진 한계

- Mac에서 기존 세이브 로드, 한글 화면의 기준 이미지 일치, 저장 후 재시작/백로그,
  타이핑/즉시 출력의 최종 화면 일치, 페이지를 비운 뒤 본문/로그 보존을 확인했습니다.
- 사용자가 저장 경로 수정 후 로드 성공과 현재까지 정상 플레이를 확인했습니다.
- 과거 `;localsave mysav` 때문에 엉뚱한 폴더를 읽던 버그를 수정했습니다.
  기본 실행 검증에는 실제 헤더와 인자 없는 실행이 반드시 포함되어야 합니다.
- 높이 검사는 기존 페이지에 텍스트가 있을 때 다음 구간을 미리 측정하는 방식입니다.
  임의로 긴 한 구간을 중간에서 나누는 범용 페이지 분할은 아닙니다.
- 전체 EP1–4 완주 및 Windows 빌드는 아직 검증하지 않았습니다.
