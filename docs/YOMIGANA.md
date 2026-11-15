# Yomigana: 다른 컴퓨터에서 적용하거나 이어 작업하기

현재 `feat/japanese-ruby`는 Windows 문제편(EP1–4)과 해답편(EP5–8)에 함께
사용하는 엔진 브랜치입니다. `e06c6a2` 위에 초기 EP1–4 루비 변경과 렌더링
보정을 적용했습니다. 이전 이름은 `feat/japanese-ruby-ep5-8`이며, 2026-11-15에
문제편에도 적용한 뒤 사용자가 정상 동작을 보고해 브랜치 이름을 변경했습니다.
초기 07th-Mod `mod:ba457e4261f9876a707d12ee03fd22dc6b0a2478` 기반 문제편
브랜치는 `backup/feat/japanese-ruby`에 보존했습니다.

답편 스크립트의 `simul_lipall`, `simul_multfont`, `simul_nextld`, `simul_nextvoice`
명령을 지원하기 위해 `e06c6a2` 기반을 유지합니다. 이 명령이 `ba457e4`에는
없다는 사실은 답편 스크립트 호환성 근거이며, 설치 실행 파일의 출처를
입증하거나 현재 엔진의 문제편 실행을 배제하는 근거는 아닙니다.

초기 문제편 소스 기반의 Mac 배포본은 [v0.1.0-macos-arm64 (pre-release)](https://github.com/lyra95/ponscripter-fork/releases/tag/v0.1.0-macos-arm64)입니다.
이전 인계 기록에는 2026-11-14에 새 clone·가상환경에서 테스트 7개와 독립 파서를
확인하고, 배포 ZIP의 전체 스크립트 적용·Mac 실행·기본 저장 경로·재시작/로드·복원을
검증했다고 적혀 있습니다. 이는 현재 `e06c6a2` 기반 소스의 Mac 검증 결과가 아닙니다.

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
**07th-Mod 기반 한·일 대사가 함께 있는 패치의 `0.u`**입니다. 설치된 두 게임에서
확인한 패치는 창 제목에 `검수패치 26.08.10`이 표시되는 버전입니다.

게임 폴더에 `0.u`가 있고, 그 안에 `langjp`, `langen`, `rubyon 17,17`,
`*clear_text_and_save_backlog` 등이 있는 호환 스크립트인지 확인하세요.
답편 스크립트에는 `simul_*` 명령도 있습니다. 변환 도구의 검사는 전체 엔진
호환성 검사를 대신하지 않습니다. Steam 기본 파일만 있고 `0.utf`만
있다면, 먼저 해당 게임용 호환 07th-Mod/언어 패치를 준비해야 합니다.
**Steam 기본 설치만으로 이 변환 도구가 즉시 적용된다고 가정하지 마세요.**
`0.utf`를 임의로 `0.u`로 바꾸는 방법은 지원하지 않습니다.

게임 이미지·음성·모드 자산과 대사 전체는 이 저장소나 Release에 포함하지 않습니다.
엔진은 독음을 자동으로 추측하지 않으며, `｜漢字《かんじ》` 표기가 있는 대사가 필요합니다.

## 2. Windows 문제편·해답편 엔진 빌드 및 적용

PowerShell에서:

```powershell
git clone --branch feat/japanese-ruby https://github.com/lyra95/ponscripter-fork.git
cd ponscripter-fork
uv sync --locked
```

두 게임은 각각의 설치 폴더와 스크립트를 사용합니다. 문제편 기본 폴더명은
`Umineko`, 해답편은 `Umineko Chiru`입니다. 실제 Steam 라이브러리에서 확인하세요.
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

### 해답편 일본어 백로그 공백 보정

확인된 해답편 한·일 스크립트에는 일본어 백로그 화면의 `logsp` 두 곳이
한글 페이지 변수 `%backloglook`을 참조하는 오류가 있습니다. 루비 변환 전에도
있는 오류이며, 새 에피소드를 시작해도 일본어 과거 대사가 공백으로 표시됩니다.
엔진 업데이트만으로 스크립트의 잘못된 참조가 수정되지는 않습니다.

```powershell
uv run --locked python tools/yomigana/fix_answer_backlog.py `
  --script ".\local-output\0.u" --output ".\local-output\0-backlog-fixed.u"
```

도구는 일본어 NVL·ADV 표시 두 곳만 `%jpbackloglook`으로 바꾸고, 늘어난 두
바이트만큼 해당 줄의 들여쓰기를 줄입니다. 파일 크기·줄 길이·줄바꿈과 나머지
바이트 위치가 유지되므로 **이 보정만 적용할 때 세이브 주소 이전은 필요 없습니다.**
현재 스크립트와 현재 세이브를 백업하고 게임을 종료한 뒤 결과를 `0.u`로 복사합니다.
한글 표시 분기는 변경하지 않습니다. 이미 수정됐으면 변경 없이 출력합니다.

`save_offsets.py`와 이를 사용하는 Mac 복원 도구는 이 두 곳의 보정을 비교할 때만
동일하게 정규화합니다. 보정된 루비 대사에서 보정 전 원본으로도 직접 주소를 이전할
수 있으며, 백업 파일이나 체크섬 목록을 수동 수정할 필요가 없습니다. 실제 원본·대상
스크립트와 주소 계산은 그대로 유지합니다. 좌표·다른 명령·한글 분기 등의 변경은
계속 거부하며, 변경된 실제 행의 TEXTGOSUB 재개 상태도 기존처럼 거부합니다.

**대사 파일을 처음 루비 변환본으로 교체할 때는 세이브 복귀 주소도 이전합니다.**
PNS 세이브의 gosub/FOR 복귀 주소는 스크립트의 바이트 위치이므로, 줄 수가
같아도 루비를 삽입하면 위치가 달라집니다. 게임을 종료하고 현재 대사와 실제
세이브 폴더를 백업한 뒤 별도 복사본으로 준비합니다. Windows 예시:

```powershell
uv run --locked python tools/yomigana/save_offsets.py `
  --source-script "C:\Program Files (x86)\Steam\steamapps\common\Umineko\0.u" `
  --target-script ".\local-output\0.u" `
  --saves "C:\Program Files (x86)\Steam\steamapps\common\Umineko\mysav" `
  --output ".\local-output\relocated-saves"
```

실제 세이브 경로는 설치마다 확인합니다. 준비한 대사와 주소를 이전한 세이브
복사본을 함께 적용하고, 원본 폴더는 보관합니다. 엔진만 갱신하고 `0.u`는
그대로 유지하는 경우 이 작업은 필요 없습니다. 원본 대사로 복원할 때는
현재 루비 대사 → 원본 대사 방향으로 **현재 진행의 세이브**를 이전합니다.

현재 도구는 PNS 2.7의 1000개·1001개 스프라이트 형식을 지원하며 진행 내용과
나머지 바이트를 유지한 채 스택 주소만 조정합니다. 새 세이브는 갯수 태그를
읽습니다. 옛 태그 없는 파일은 작성한 엔진을 확인해 `--legacy-sprites 1000`
또는 `--legacy-sprites 1001`을 추가해야 합니다. 버전 번호만으로 추측하지
않으며, 다른 엔진에서 만든 옛 파일이 섞여 있으면 따로 처리합니다.
알 수 없는 형식, 중첩 저장
폴더, 루비를 삽입한 줄 내부의 TEXTGOSUB 재개 상태는 안전하게 이전할 수 없어
교체 전에 중단합니다. 구형 세이브에는 원본 스크립트 식별 정보가 없으므로,
**각 세이브를 실제로 만든 스크립트**를 source로 지정해야 합니다. 원본/변환본에서
만든 슬롯이 섞여 있으면 같은 source로 일괄 처리하지 마세요. 이미 변환본으로
저장한 슬롯을 원본 기준으로 다시 이전하면 안 됩니다.

자세한 MINGW32 빌드·Steam SDK DLL·설치 백업 절차는
[Windows 빌드 안내](WINDOWS_BUILD.md)를 따릅니다. 같은 소스의 x86 엔진 빌드를
두 게임에서 사용할 수 있지만, 실행 파일명은 문제편 `Umineko1to4.exe`,
해답편 `Umineko5to8.exe`로 맞추고 각 게임의 스크립트·자산·App ID·세이브 설정은
해당 설치판 것을 사용해야 합니다. `0.u`가 이미 루비 변환된 경우 엔진 업데이트만
할 때 다시 변환하지 마세요. 실행 파일과 호환 DLL을 한 쌍으로 백업하고 현재
실제 저장 폴더(`mysav` 등)도 보존합니다.

2026-11-15에 현재 기반을 다시 빌드해 문제편에 적용했습니다. 엔진 교체 후
문제편 창과 오프닝 재생을 확인했고 사용자가 정상 동작을 보고했습니다.
스크립트와 기존 세이브의 해시가 유지된 것을 확인했습니다. 이는 모든 에피소드,
저장/재시작, 언어 전환을 자동으로 검증했다는 의미는 아닙니다.

## 3. 초기 문제편 Mac Release 적용

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

현재 소스의 도구는 독음을 생성하고 세이브의 복귀 주소 이전을 검증한 뒤,
현재 앱·원본 `0.u`·현재 `saves/`를 백업하고 앱·대사·세이브를 함께 교체합니다.
복원할 때도 현재 진행을 유지하면서 원본 대사에 맞게 주소를 역으로 이전합니다.
앱의 원래 아이콘 등은 로컬에서 유지합니다. 초기 `v0.1.0` ZIP에는 이 주소
이전 수정이 없으므로, 기존 세이브가 있으면 최신 저장소의 도구를 사용하세요.
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

태그가 없는 세이브는 작성 엔진에 맞는 `--legacy-sprites`가 필요합니다.
복원 대상이 옛 1000개 엔진이면 `--restore-sprites 1000`도 지정합니다.
이때 1001번째 슬롯이 비어 있을 때만 제거하며, 사용 중이면 중단합니다.
별도 이전 CLI의 같은 옵션은 `--target-sprites 1000`입니다.

현재 엔진은 옛 1000개 파일과 기존 1001개 파일을 읽기 전에 전체 구조로 구분하고,
새 저장에는 갯수를 명시합니다. 따라서 **대사를 그대로 두고 엔진만 교체할 때는
기존 세이브를 변환할 필요가 없습니다.** 초기에 문제가 생긴 원인은 엔진 내부의
슬롯 수 증가와 세이브 구조를 혼동한 것이며, 새 게임을 시작할 필요는 없습니다.

Apple이 다운로드한 실행 파일을 차단하면 먼저 출처와 체크섬을 확인하고 macOS의
개인정보 보호 및 보안 설정에서 해당 실행을 허용하는 절차를 따르세요. 도구는 시스템
보안 설정을 자동으로 변경하지 않습니다.

## 4. 초기 문제편 Mac 소스 빌드와 Release 재생성

아래 절차는 초기 문제편 소스용입니다. 현재 공용 브랜치에도 Mac의 `saves/`
우선 선택 코드를 복구했습니다. Mac Steam 로그의 Auto-Cloud 대상도 `saves/`로
확인했으며, `mysav/`로 복사하는 것만으로는 이후 진행이 자동 동기화되지 않습니다.
현재 공용 소스의 전체 게임 동작은 아직 검증하지 않았습니다. 초기 Mac 빌드 흐름을
사용하려면 보존 브랜치의 별도 작업 트리에서 시작하세요. 해당 브랜치에는 현재
공용 엔진의 후속 렌더링 보정이 포함되지 않습니다.

```bash
git fetch origin
git worktree add --detach ../ponscripter-macos origin/backup/feat/japanese-ruby
cd ../ponscripter-macos
uv sync --locked
```

초기 빌드 기록의 Python 도구는 `fugashi 1.5.2`, `unidic-lite 1.0.8`입니다.
초기 기록에는 CMake 4.4.4 및 Apple Clang 사용이 적혀 있습니다. Homebrew에 SDL2 계열,
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

- 초기 Mac 배포본에 대한 이전 기록에서는 기존 세이브 로드, 한글 화면의 기준 이미지 일치, 저장 후 재시작/백로그,
  타이핑/즉시 출력의 최종 화면 일치, 페이지를 비운 뒤 본문/로그 보존을 확인했습니다.
- 사용자가 저장 경로 수정 후 로드 성공과 현재까지 정상 플레이를 확인했습니다.
- 초기 Mac 배포본과 보존 브랜치에는 `;localsave mysav` 때문에 기존 세이브를
  못 찾던 문제의 수정이 들어 있습니다. 현재 공용 소스에도 동일한 경로 우선 처리를 복구했습니다.
  기본 실행 검증에는 실제 헤더와 인자 없는 실행이 반드시 포함되어야 합니다.
- 높이 검사는 기존 페이지에 텍스트가 있을 때 다음 구간을 미리 측정하는 방식입니다.
  임의로 긴 한 구간을 중간에서 나누는 범용 페이지 분할은 아닙니다.
- Windows x86 빌드와 두 설치판 적용은 수행했습니다. 문제편 적용 후 사용자의
  정상 동작 보고가 있습니다. 전체 EP1–8 완주 및 현재 공용 소스의 Mac 동작은
  검증하지 않았습니다.
