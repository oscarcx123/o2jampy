# o2jampy

A next generation o2jam to osu!mania converter

## Why o2jampy?

|                     | o2jampy               | wanwan159       | djask        |
|---------------------|-----------------------|-----------------|--------------|
| Open Source         | Yes                   | No              | Yes          |
| Beatmap Accuracy    | Excellent             | Good            | Meh          |
| Codecs Support      | All codecs            | gb18030, euc-kr | utf-8        |
| Wav Extraction      | Yes                   | Yes             | Doesn't Work |
| Channel 0 Support   | Yes                   | Yes             | No           |
| Batch Conversion    | Yes                   | No              | Yes          |
| OGG to MP3          | Yes                   | No              | No           |
| Remove all SV       | Yes (Optional)        | No              | No           |
| Remove stacked note | Yes                   | No              | No           |
| GUI                 | Maybe                 | Yes             | No           |

## How to use?

TODO

## Development Roadmap

* Auto convert ogg -> mp3
* Option to remove all bpm change
* Option to add green line multiplier (keep bpm change but remove sv effect)
* Option to remove stacked notes / hidden notes under LN (o2ma3021)
* Maybe GUI? (very low priority)
* Optimize wav extraction (it's way too slow, sometimes takes 2 minutes for large ojm file)

## Updates

Known issue:
* channel 0 (o2ma2673)


### 2022.08.25 - 0.3.0

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