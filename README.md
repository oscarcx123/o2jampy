# o2jampy

A next generation o2jam to osu!mania converter

## Why o2jampy?

|  | [o2jampy](https://github.com/oscarcx123/o2jampy) | [wanwan159](https://osu.ppy.sh/community/forums/topics/121149) | [djask](https://github.com/djask/o2jam_utils) |
|---|---|---|---|
| Open Source | Yes | No | Yes |
| Accuracy | Perfect | Good | Meh |
| Codecs Support | All codecs | gb18030, euc-kr | utf-8 |
| Wav Extraction | Yes | Yes | Doesn't Work |
| Channel 0 Support | Yes | No | No |
| Batch Conversion | Yes | No | Yes |
| OGG to MP3 | Yes | No | No |
| Remove all SV | Yes (Optional) | No | No |
| Remove stacked notes | Yes | No | No |
| GUI | Maybe | Yes | No |

Rhythm games (OJN): [soundsphere](https://github.com/semyon422/soundsphere), [raindrop](https://github.com/zardoru/raindrop), o2mania

### Some charts for testing

* LN
    * o2ma3021 - [LN]Hishoku no Sora (lvl 55)
* Channel 0
    * o2ma1172 - [SHD]KAMUI (lvl 121)
    * o2ma2672 - Cirno's Perfect Math Class (lvl 140)
* Keysound
    * o2ma1082 - God Knows Piano Ver (lvl 15/16/28) (OGG)
    * o2ma392 - The Adventure Of Mikuru Asahina (lvl 3/6/22) (WAV)
    * o2ma2618 - KOTONOHA (lvl 70) (Both)

## How to use?

TODO

## Development Roadmap

* Auto convert ogg -> mp3
* Option to remove all bpm change
* Option to add green line multiplier (keep bpm change but remove sv effect)
* Option to remove stacked notes / hidden notes under LN (o2ma3021)
* Maybe GUI? (very low priority)
* Optimize wav extraction (it's way too slow, sometimes takes 30s for huge ojm file)

## Updates

### 2022.08.26 - 0.4.0

* [x] Refactor hitsound format detection (o2ma2618)
* [x] Bug fixes

### 2022.08.25 - 0.3.0

* [x] Channel 0 support (o2ma2673)
* [x] Fixed LN pairing issue (o2ma3021)
* [x] Fixed autoplay hitsound (<1000) not exported to osu's Event (o2ma1082, o2ma106, o2ma392)
* [x] Fixed normal-hitnormal2.ogg in event
* [x] Bug fixes

### 2022.08.24 - 0.2.0

* [x] OJM (M30 format) extraction
* [x] Bug fixes

### 2022.08.23 - 0.1.0

* [x] OJN data extraction
* [x] OJM (OMC and OJM format) extraction