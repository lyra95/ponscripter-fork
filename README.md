> [!NOTE]
> **이 포크에 대하여 — Yomigana**
>
> 이 저장소는 macOS에서 Steam판 **괭이갈매기 울 적에 EP1–4**의 일본어 대사 위에 요미가나(루비)를 표시하도록 Ponscripter 엔진을 수정한 포크입니다. 기존 한글 대사와 언어 전환 기능을 유지하면서 루비 출력, 대사 높이 검사, 기존 세이브 경로 호환성을 추가했습니다. 루비를 표시하려면 대사에도 `｜漢字《かんじ》` 형식의 독음 정보가 필요합니다.
>
> - **작업 브랜치:** [`feat/japanese-ruby`](https://github.com/lyra95/ponscripter-fork/tree/feat/japanese-ruby)
> - **기준 브랜치(baseline):** 이 포크의 [`mod`](https://github.com/lyra95/ponscripter-fork/tree/mod). 원본 [`07th-mod/ponscripter-fork`의 `mod`](https://github.com/07th-mod/ponscripter-fork/tree/mod)에서 가져온 수정 전 코드입니다.
> - **작업 시작 기준 커밋:** [`ba457e4`](https://github.com/07th-mod/ponscripter-fork/commit/ba457e4261f9876a707d12ee03fd22dc6b0a2478). 이후 변경 사항은 이 커밋을 기준으로 비교할 수 있습니다.
> - **다른 컴퓨터로 이관:** [Steam 설치 기준 가이드 및 Windows 작업 인계](docs/YOMIGANA.md)
> - **Mac 바이너리:** [v0.1.0 초기 배포본](https://github.com/lyra95/ponscripter-fork/releases/tag/v0.1.0-macos-arm64) — arm64, macOS 26.0 이상. Windows 빌드는 아직 제공하지 않습니다.

## 루비 적용 전후

동일한 세이브의 같은 장면을 1920×1080으로 촬영했습니다. 이미지를 클릭하면 크게 볼 수 있습니다.

| 적용 전 | 루비 적용 후 |
| --- | --- |
| [![적용 전 일본어 대사](docs/images/ruby-before.png)](docs/images/ruby-before.png) | [![한자 위에 독음을 표시한 대사](docs/images/ruby-after.png)](docs/images/ruby-after.png) |

# Ponscripter-fork (07th-mod)

[![Build status](https://github.com/07th-mod/ponscripter-fork/workflows/Build/badge.svg)](../../actions)

## Introduction

Ponscripter was created as an NScripter-style visual novel game interpreter with an emphasis
on supporting games in Western languages.

This fork is intended to provide additional features to Ponscripter that make it more suitable for releasing
games on Steam. It, however, does not have qualms with breaking compatibility in minor ways. See the CHANGES file.

Other engines focussed on Western-language games include:

* [Ponscripter](http://web.archive.org/web/20180812034417/http://unclemion.com/onscripter/) &mdash; The project this is based on
* [Ren'Py](http://www.renpy.org/) &mdash; A modern visual novel engine with python scripting support.

## Additional Features in this fork

### Scaling Options

#### Default Scaling

> [!Warning]
> On versions v3.0.2 and below, the "Umineko Steam release scaling mode" was the default, which could cause problems if you didn't specify a scaling mode (See [#17 where Umineko Saku 2019 had graphical issues on v3.0.2 and below](https://github.com/07th-mod/ponscripter-fork/issues/17)). This has been fixed on v4.0.0 and above.

The default scaling option for our fork (as of v4.0.0) expects an input game resolution of 640x480 (eg. older nscripter games), and applies 2x mode (doubles everything). This is equivalent to explicitly setting the scaling mode with `;value2500,mode640@2x`.

#### Normal Scaling Options

This fork includes 2x mode, which can be used to support older Nscripter games at 2x resolution.

This feature has been added as an extra argument to `;mode` (e.g. `;mode960@2x`).

Widescreen support is also included, and can be enabled with `;modew720` or `;modew1080`.

For example, our modded Umineko scripts have `;value2500,modew540@2x@umineko` as the first line of the script to give a 1920x1080 output resolution (as the input height of 540 is doubled). As for the `@umineko` option, see below.

Please note that you MUST specify `mode` before specifying any other options like `@2x`, otherwise those commands will be ignored or cause problems.

#### Umineko Steam Scaling Mode

We've added an additional option for scaling to suit the Umineko Steam release. This changes the behavior of font scaling, and also the `getspsize` command - See d2b5d19 and e9c7e03.

In most cases you will never need to use this scaling mode, but if you wish to enable it, add `@umineko` after the `mode` command, for example the very first commented line of your script could be something like `;value2500,modew540@2x@umineko`

## Documentation

The below links contain general information about POnscripter (not specific to this fork of POnscripter):

* [Ponscripter Tutorial](https://07th-mod.github.io/ponscripter-fork) - Most likely you should start here
* [Ponscripter API Reference](https://07th-mod.github.io/ponscripter-fork/api/) - Mirror of Uncle Mion's Ponscripter API reference

### Instructions to build from source

Please refer to [INSTALL.md](https://github.com/07th-mod/ponscripter-fork/blob/mod/INSTALL.md) for build instructions.

We also have automated builds on github which you can use as reference - see `.github/workflows`, `.travis_before_install.sh`, and `.travis_run.sh`.

## Compatibility

This incarnation of the engine has primarily been tested with the [Umineko](https://store.steampowered.com/app/406550/) script.

We strive to keep the engine able to compile and run correctly without the Steam runtime/api, but
the Steam platforms are our primary targets.

The following platforms are supported:

* Any modern Linux
* Windows 7/8/10
* OSX 10.9+

Any issues on these platforms should be reported.

## Bugs

Please report all bugs with this project on the [issues page](../../issues). Include your platform and, if possible, clear reproduction instructions.


## Acknowledgements

The original Ponscripter engine was maintained and, in great part, created by Mion.

Ponscripter is built primarily on Ogapee's work, without which there
would be nothing here.

The version of ONScripter taken as a base also includes notable
contributions from Chendo (original English support), insani
(further enhancements) and The Witch Hunt.

The following people (in alphabetical order) have contributed 
noteworthy patches and bug reports that have enhanced Ponscripter:

* Agilis
* chronotrig
* Daniel Oaks
* Euank
* Klashikari
* Mion of Sonozaki Futago-tachi
* Roine Gustafsson
* Roto
* Starchanchan

Apologies to anyone not mentioned &mdash; please let me know so I can set the
record straight!

## 07th-Mod fork

The 07th-Mod fork of this repo is brought to you with huge thanks to everyone mentioned above, but the latest changes are being maintained by the [07th-Mod](https://07th-mod.com) team. If you have any issues with this fork, please feel free to report them on the issues page or bother us on Discord about it.

## License

ONScripter is copyright © 2001-2007 Ogapee.  The Ponscripter fork is
copyright © 2006-2009 Haeleth.

Ponscripter is licensed under the GNU General Public License, version
2 or (at your option) any later version.  See COPYING for details.
