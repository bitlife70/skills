---
name: orchestra-bgm
description: 실제 오케스트라 녹음에서 측정한 악기·섹션 음향 프로파일로 오케스트라 BGM(wav)을 작곡·렌더링한다. 영상/모션그래픽 배경음악, 시네마틱 큐, 팡파레, 오프닝 음악 요청 시 사용.
---

# 오케스트라 BGM (분석 기반 재합성 엔진)

이 엔진은 실제 오케스트라 녹음 1,170개(VSCO-2 CE·Sonatina Symphonic Orchestra)를 분석해 얻은 측정값만으로
모든 악기를 다시 합성한다. 렌더링할 때 오디오 샘플은 쓰지 않는다. 측정값은 `profiles.json`에 들어 있다.

- **톤 악기**: 음높이·셈여림별 배음 스펙트럼, 어택 중 배음 변화, 활·숨 노이즈, 비브라토, 셈여림에 따른 음색 기울기, 릴리즈.
- **섹션(합주)**: 섹션 녹음에서 잰 '배음선 퍼짐(cent)'을 기준으로, 가상 연주자 N명에게 각자 음정 편차·비브라토·타이밍·음색 차이·좌석 위치를 준다. 편차 크기는 합성→재분석 폐루프로 원본과 같아지도록 보정되어 있다(`calib_detune`, `calib_vib_scale`).
- **타악기**: 녹음 스펙트럼에서 공명 모드를 찾아(팀파니 70개, 심벌·탐탐 최대 1,500개; 강한 피크의 감쇠 치마폭에 생기는 가짜 피크는 제외) 각 모드를 시간 추적한다. 가장 강한 12개 모드는 **측정한 음량 곡선 자체**(머묾·맥놀이·다단 감쇠)를, 나머지는 시작 크기·감쇠율·차오름 시간을 쓴다. 남은 성분은 시간-대역별 잔여 노이즈로 둔다. 금속 악기(심벌·탐탐)의 잔여분은 2.5 Hz 간격(원본의 공명선 밀도·피크 대 바닥 비에 맞춤)의 고정 무작위 공명선으로 채워 '쉬익'이 아닌 금속성 반짝임이 나게 한다. 이 모두를 합성→재분석 루프로 보정한다(잔여 노이즈 보정 폭은 ±6 dB로 제한하고, 음정 타악기—팀파니·글로켄슈필·실로폰·차임·트라이앵글—에서는 모드가 지배하는 대역의 잔여 노이즈를 줄이기만 허용).
- **노이즈 성분**(활 긁힘·숨·피치카토 몸통 울림·손가락 소리): 어택부터 지속부까지 시간 격자별로 측정해 재생한다. 측정 노이즈에는 배음 누설이 섞이므로, 악기·주법별로 음높이 5지점에서 합성→재분석 폐루프 보정을 한다.
- **뜯는 소리·짧은 음**: 2 ms 즉시 어택과 정렬된 위상으로 원본의 '탁' 하는 순간을 재현한다. 섹션에서는 연주자 간 배치된 타이밍 차로 생기는 배음별 보강·상쇄를 계산해 되돌린다(짧은 음은 음정이 흔들릴 시간이 없어 우연한 음색 왜곡이 고정되기 때문).
- **무대**: 좌석 배치(팬·폭·깊이), 깊이에 따른 고역 감쇠·잔향 비율, 콘서트홀 IR, 버스 리미터.

검증 수치(합성음을 원본과 같은 분석기로 재측정): 92개 음 기준 배음 스펙트럼 오차 중앙값 1.8 dB, 노이즈 성분 오차 대부분 1–2 dB, 타악기 시간-대역 엔벨로프 오차 3–4 dB.

## 1. 엔진 준비 (클라우드 작업공간에서 렌더)

렌더링은 작업공간(Bash)에서 한다. 사용자 PC 쪽 VM에는 scipy가 없다.

```bash
mkdir -p ~/orch && cd ~/orch
pip install --break-system-packages -q soundfile   # numpy, scipy 필요
```

엔진 파일 두 개(`orchestra.py`, `profiles.json`)를 아래 순서대로 찾아서 가져온다.

1. **프로젝트 문서**: `project_read`로 `claude/orchestra_bgm/orchestra.py`와 `claude/orchestra_bgm/profiles.json`을 읽는다. 결과로 받은 `local_file`을 `cat <local_file> > ~/orch/orchestra.py`(또는 `profiles.json`)로 복사한다.
2. **사용자 폴더**(PC 연결 시): `C:\Users\User\workspace\motion_graphic_playground\orchestra_bgm\`에 `orchestra.py`, `profiles.json`, `examples/demo_theme.py`(전체 예제곡), `examples/demo_shorts.py`(30초 쇼츠 예제), `analysis/`(분석 파이프라인·`diag.py` 원본 대비 진단 그림)가 있다. `device_stage_files`로 가져와 `~/orch`에 복사한다.
3. 둘 다 없으면 9절의 파이프라인으로 프로파일을 다시 만든다.

확인: `python3 -c "import orchestra as O; print(len(O.profiles()['instruments']))"` → 37.

## 2. 곡 설계 (음표를 쓰기 전에)

- **길이 → 템포·마디 수**: 마디 수 = 길이(초) × bpm / 240 (4/4 기준). 영상용이면 장면 전환·클라이맥스 시점을 먼저 초 단위로 받아 마디 경계에 맞춘다(`s.sec(beat)`로 확인).
- **형식**: 도입(옅은 질감) → 주제 → 빌드업(오스티나토·크레셴도·롤) → 투티 클라이맥스 → 종지. 짧은 큐(15–30초)는 '도입–빌드–히트' 3단으로 쓴다.
- **조성·분위기**: 장엄·영웅적이면 단조 진행에서 마지막에 같은 으뜸음의 장조로 끝낸다(피카르디 3화음). 서정적이면 현 레가토, 목관 솔로, 하프를 쓴다. 긴박하면 스타카토 오스티나토, 낮은 금관, 팀파니, 스네어 롤을 쓴다.
- 작업 순서: 화성 진행표 → 베이스 → 멜로디 → 내성 → 타악기.

## 3. Score API

```python
import sys; sys.path.insert(0, '/root/orch')        # orchestra.py 위치
from orchestra import Score
s = Score(bpm=84, seed=7, rt=2.3)                  # rt = 홀 잔향(초), 1.6 실내악 ~ 2.8 대성당
B = 4; bar = lambda n: (n - 1) * B                 # 1마디 = 4박, 박(beat) 단위로 위치 지정

s.note('celli', bar(1), 'D3', 4, dyn='p', dyn_end='mf')            # 한 음 (dyn_end = 음 안의 크레셴도)
s.chord('violins2', bar(1), ['A4', 'D5'], 4, dyn='mp')               # 화음
end = s.line('violins1', bar(5), 'A4:1 D5:1.5 E5:.5 F5:1 | G5:2 (f) F5:1 E5:1',
             dyn='mp', legato=True)                                  # 선율: 음:박, r=쉼표, (f)=셈여림 변경
s.note('violas', bar(9), 'C4', 0.45, dyn='mf', art='staccato')       # 아티큘레이션
s.hit('timpani', bar(1), 'D2', dyn='f')                              # 타악기 1타(음높이 있는 악기는 음 지정)
s.roll('timpani', bar(4), 4, 'A2', dyn='p', dyn_end='ff')            # 롤(실제 연타로 합성)
s.roll('sus_cymbal', bar(8), 4, dyn='pp', dyn_end='f')               # 심벌 스웰
s.hit('cymbals', bar(9), dyn='ff'); s.hit('harp', bar(2), 'D4', dyn='mp')
s.set_tempo(bar(20), 72)                                             # 템포 변경(구간별 고정)
s.render('cue.wav', tail=4.0)                                        # 기본: master='concert' (자연스러운 다이내믹, 피크 -1 dBFS)
s.render('short.wav', master='shorts', narration=True)               # 쇼츠용(6절): -14 LUFS, -1 dBTP, 내레이션 자리 비움
# s.render(..., stems=True) -> (mix, {part: stereo})  /  workers=2 (파트 단위 병렬)  /  lufs=-16 처럼 목표 직접 지정
# 영상 길이에 맞추기: from orchestra import bpm_for; Score(bpm=bpm_for(seconds=28, bars=12))
```

- 음 이름은 과학적 표기(C4 = 가온 다, `F#4`, `Bb3`)나 MIDI 숫자. 타악기 음은 **실음**(글로켄슈필 포함)이다.
- 셈여림: `ppp pp p mp mf f ff fff` 또는 0–1. 음량과 음색(밝기)이 함께 바뀐다.
- 아티큘레이션 `art`: `sus`(기본), `staccato`/`spiccato`, `pizz`, `trem`, `marcato`. 프로파일에 없는 주법은 sus로 근사한다(짧은 엔벨로프, 강조, 트레몰로 진폭변조).
- `legato=True`(line): 다음 음이 어택 없이 이어지고 짧은 포르타멘토가 들어간다. 현·목관·호른 선율에 쓴다.
- 파트별 음량 미세조정은 `gain=±dB`, 가상 연주자 수 변경은 `voices=N`(note/chord/line 인자)로 한다.

## 4. 파트 (이름 · 프로파일 · 좌석 · 실용 음역 · 주법)

| 파트 | 가상 연주자 | 좌석 | 실용 음역(실음) | 주법 |
|---|---|---|---|---|
| violins1 / violins2 | 8 / 7 | 무대 왼쪽 앞 / 왼쪽 안쪽 | G3–A6 | sus staccato pizz trem |
| violas | 6 | 중앙 오른쪽 | C3–D6 | sus staccato pizz trem |
| celli | 6 | 오른쪽 | C2–F5 | sus staccato pizz trem |
| basses | 5 | 오른쪽 뒤 | C1–C4 (기보보다 한 옥타브 낮게 실음 지정) | sus staccato pizz trem |
| flutes / piccolo | 2 / 1 | 목관 열 | C4–C7 / D5–C8 | sus staccato(flutes) |
| oboes / clarinets / bassoons | 2 / 2 / 2 | 목관 열 | Bb3–F6 / D3–C7 / Bb1–E5 | sus |
| contrabassoon | 1 | 목관 뒤 | Bb0–G3 | sus |
| horns | 4 | 왼쪽 뒤 | E2–F5 | sus staccato |
| trumpets / trombones | 3 / 3 | 중앙·오른쪽 뒤 | E3–C6 / E2–F5 | sus staccato |
| tuba | 1 | 오른쪽 뒤 | E1–C4 | sus staccato |
| harp | 1 | 왼쪽 | B0–G7 | hit(=뜯기, `s.hit`/`s.note`) |
| choir_female / choir_male | 6 / 6 | 맨 뒤 | G4–C6 / G2–F#4 | sus('아') |
| violin_solo, cello_solo, flute_solo, oboe_solo, clarinet_solo, bassoon_solo, horn_solo, trumpet_solo, trombone_solo | 1 | 해당 섹션 자리 | 섹션과 동일 | sus (+ violin_solo staccato, cello_solo pizz) |
| timpani | – | 뒤 중앙 | B1–Eb3 (± 몇 반음 가능) | hit, roll |
| bass_drum, cymbals, sus_cymbal, snare, tamtam, triangle | – | 뒤 | – | hit, roll |
| glockenspiel / xylophone / chimes | – | 뒤 | C5–C8 / G4–D8 / B2–C6 | hit |

음역을 벗어나도 외삽해서 소리는 나지만 음색 신뢰도가 떨어진다. 음역 안에서 쓴다.

## 5. '오케스트라답게' 들리게 하는 규칙

1. **섹션 단위로 쓴다**: 한 성부는 독주 파트보다 섹션 파트(violins1, horns…)로 쓴다. 독주(`*_solo`)는 서정적 선율에만 쓴다.
2. **겹치기(doubling)**
   - 베이스: basses + celli를 옥타브로, 클라이맥스에는 tuba·contrabassoon을 더한다.
   - 멜로디: 서정적이면 violins1 단독 → 반복 때 flutes를 한 옥타브 위에 얹는다. 영웅적이면 horns(한 옥타브 아래) + trumpets + violins1·2(옥타브).
   - 화성 패드: violas·violins2·clarinets·horns를 나눠 배치한다.
3. **배치(voicing)**: C3 아래에는 옥타브·5도만 둔다(3도는 탁해진다). 화음은 위로 갈수록 좁게 쌓는다. 한 파트 안 동시 음은 2–3개까지만.
4. **셈여림 밸런스**: 같은 표기라도 금관이 현보다 크다. 현 선율 위의 금관 패드는 2단계 낮게 쓴다(현 mf ↔ 금관 p). 투티 f에서 멜로디는 금관에 맡기거나 현 전체를 옥타브로 겹친다.
5. **움직임**: 긴 화음에는 `dyn_end`로 숨을 준다(p→mf→p). 빌드업은 첼로·베이스 8분음 스타카토 오스티나토, 위 성부 롱톤 크레셴도, 스네어·서스펜디드 심벌·팀파니 롤로 만든다.
6. **타악기는 구두점**: 팀파니는 화음 근음(으뜸음/딸림음)으로 마디 첫 박에 친다. 심벌 크래시와 탐탐은 섹션 시작에만 쓰고, 클라이맥스 직전 롤에서 다음 마디 첫 박 크래시로 잇는다. 글로켄슈필·하프는 질감·반짝임 용도로 소량만 쓴다.
7. **레가토 vs 분리**: 선율은 `legato=True`. 리듬 반주는 `staccato`, 길이는 박의 0.45–0.6 정도.
8. **종지**: 마지막 화음은 2마디 이상 잡고 `dyn_end`로 살짝 줄인다. 잔향 꼬리를 위해 `tail` 3–5초를 둔다.

## 6. 용도별 조정: 사용자가 '쇼츠용'이라고 하면

이 스킬은 다목적이라 기본값은 `master='concert'`다. 사용자가 **쇼츠·릴스·틱톡·세로 영상용**이라고 말했을 때만 아래처럼 바꾼다(묻지 말고 적용한 뒤, 무엇을 바꿨는지 한 줄로 알린다).

**작곡**
- 길이: 15–60초(영상 길이가 주어지면 거기에 맞춘다. `bpm_for`로 마디 수를 맞춘다).
- 첫 1–2초 안에 훅: 느린 도입 없이 리듬 모티프·화음 히트·짧은 크레셴도로 바로 시작한다. 도입은 1마디 이내로 둔다.
- 형식: 훅 → 전개 → 클라이맥스를 끝 20–25% 지점 전에 → 짧은 히트 엔딩. 반복 재생을 고려하면 마지막 마디를 첫 마디 화음으로 돌아오게 해서 루프가 자연스럽게 한다.
- 템포 90–130 bpm. 스타카토 오스티나토와 타악기로 리듬감을 키운다.
- 휴대폰 스피커는 150 Hz 아래가 거의 안 들린다. 베이스 라인은 celli로 한 옥타브 위를 겹치고, 멜로디는 G4–C6 대역에서 violins1·trumpets·horns로 또렷하게 쓴다.
- 동시에 움직이는 층은 3–4개 이내로 단순하게 쓴다.
- 내레이션이 있으면: 말하는 구간에서는 중음역(500 Hz–3 kHz) 악기 밀도를 줄인다(패드는 저역·고역으로, 선율은 쉬거나 flutes·glockenspiel 고역으로). 모티프는 문장 사이에 넣는다.

**렌더**: `s.render(path, master='shorts', narration=<내레이션 유무>)`
- 홀 잔향 0.72배, wet 축소(선명도), 45 Hz 하이패스, 저역 셸프 컷 + 180 Hz·3.2 kHz 보강(폰 스피커에서 들리게).
- 라우드니스 -14 LUFS 정규화 + 룩어헤드 리미터 -1 dBTP.
- `narration=True`면 2.3 kHz 중심 -4 dB, 900 Hz -1.5 dB로 목소리 자리를 비운다.

**검수 추가**: 폰 스피커 시뮬레이션(200 Hz–8 kHz 밴드패스)에서도 멜로디와 리듬이 들리는지, 모노 합(L+R)에서 소리가 빠지지 않는지 확인한다.

**내레이션과 합치기(덕킹)**:
```bash
ffmpeg -i video_with_vo.mp4 -i bgm.wav -filter_complex \
 "[0:a]asplit=2[vo][sc];[1:a]volume=-6dB[bg];[bg][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck];[vo][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 256k out.mp4
```

## 7. 렌더 · 검수 · 전달

1. 곡 스크립트를 `~/orch/<name>.py`로 저장하고 실행한다. 렌더 시간은 빽빽한 투티 기준 실시간의 약 2.5–3배(2코어)다. 1분이 넘는 곡은 `run_in_background`로 돌린다.
2. 검수 항목
   - 길이가 목표와 맞는지
   - 피크 ≤ -1 dBFS, NaN 없음
   - 0.1초 간격 RMS 곡선이 의도한 형식(빌드→클라이맥스)을 따르는지
   - 스펙트로그램에서 저역(<200 Hz)이 뭉개지지 않는지

   저역이 과하면 basses/celli `gain`을 줄이거나 화음 저음을 옥타브로 정리한다.
3. 전달: `SendUserFile`로 wav를 보낸다. PC가 연결되어 있으면 `device_commit_files`로 `...\motion_graphic_playground\<프로젝트>\`(예: `orchestra_bgm\output\`)에도 저장한다. 같은 파일명을 다시 커밋할 때는 예전 업로드가 쓰일 수 있으니 새 스테이징 이름(예: `cue__v2.wav`)으로 복사해 커밋하고, PC 쪽 `md5sum`으로 일치를 확인한다.
4. 영상과 합치기:
   ```bash
   ffmpeg -i video.mp4 -i cue.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out.mp4
   ```
   내레이션이 있으면 6절의 덕킹 명령을 쓴다.

## 8. 성능 팁

- 비용은 대략 (음 길이 × 가상 연주자 수 × 배음 수)에 비례한다. 저음일수록 배음이 많아 비싸다.
- 빠른 반복음(오스티나토)은 `voices=3–4`로 줄여도 차이가 작다.
- 긴 지속음은 문제없다. 같은 음을 짧게 여러 번 이어 붙이는 것보다 한 음으로 길게 쓰는 편이 자연스럽고 빠르다.

## 9. 프로파일 재생성 / 악기 추가 (필요할 때만)

사용자 폴더 `orchestra_bgm/analysis/`에서 다음 순서로 진행한다.

1. `fetch_samples.sh` + `sample_urls.txt`로 PC VM(GitHub 접근 가능)에서 샘플을 받고, 모노 44.1 kHz flac으로 변환한다. 이미 받은 샘플 묶음이 `_cache/samples.tar`에 있다.
2. 작업공간으로 가져와 `flac/` 폴더에 푼다.
3. `python3 analyze.py` → `analysis_raw.json`
4. `python3 build_profiles.py` → `../profiles.json` (보정값을 지우므로 이후 5–7단계를 반드시 다시 한다)
5. `python3 validate.py calib` → 섹션 퍼짐 보정
6. `python3 validate.py noisecal` → 노이즈 성분 보정(음높이별)
7. `python3 validate.py perccal` → 타악기 보정
8. `python3 validate.py report`로 오차를 확인하고, `python3 ab_compare.py`로 원본↔합성 A/B 음원과 스펙트로그램을 만든다.

새 악기는 `catalog.py`의 `FOLDER`/`PERC` 매핑에 추가하고 `orchestra.py`의 `PARTS`에 좌석을 정의한다.

## 10. 한계 (사용자에게 솔직히 말할 것)

- 레가토 전환, 피치 벤드, 금관 플러터·뮤트, 현 하모닉스·콜레뇨는 근사이거나 지원하지 않는다.
- 합창은 모음 '아' 하나만 있고 가사는 없다.
- 프로파일은 원 라이브러리의 녹음 공간색이 일부 반영된 값이다.
- `master='concert'`는 라우드니스 정규화 없이 피크만 맞춘다. 스트리밍 기준이 필요하면 `lufs=-16`처럼 목표를 지정한다(`'shorts'`는 -14 LUFS 기본).
- 출처: VSCO-2 Community Edition(CC0), Sonatina Symphonic Orchestra(CC Sampling+ 1.0). 프로파일에는 측정값만 들어 있고 오디오는 없다.
- 샘플을 직접 재생하는 하이브리드 방식은 쓰지 않는다(사용자 결정). 음색 개선은 분석·합성 쪽에서 한다.
