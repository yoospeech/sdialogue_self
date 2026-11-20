# SDialogue Self

SDialog를 기반으로 시나리오와 페르소나를 선택하고 대화 생성부터 자동 평가와 음성 합성까지 수행하는
end-to-end 데이터 생성기입니다. SDialog 본체는 `vendor/sdialog` Git submodule로 관리합니다.

## 제공 기능

- 서른여섯 가지 시나리오와 천 명의 결정적 가상 페르소나
- 영어 아랍어 중국어 프랑스어 독일어 이탈리아어 일본어 한국어 포르투갈어 스페인어 베트남어
  태국어 인도네시아어 힌디어 러시아어 폴란드어 선택
- 고정 턴 수 또는 범위 내 재현 가능한 무작위 턴 수
- 로컬 Hugging Face 모델을 이용한 대화 생성과 텍스트 기반 자동 평가
- 시나리오별 오디오 프리셋과 사용자 화자 전용 음향 증강
- 대화 JSON 평가 JSON WAV 또는 FLAC과 annotation 저장

언어 선택은 프롬프트의 출력 언어를 지정합니다. 실제 생성 품질과 TTS 지원 범위는 사용하는 모델에 따라
달라집니다.

## 설치

Python 3.10 이상 환경을 권장합니다.

```bash
git clone --recurse-submodules https://github.com/yoospeech/sdialogue_self.git
cd sdialogue_self
python -m pip install -r requirements.txt
```

이미 저장소를 clone했다면 submodule을 별도로 초기화합니다.

```bash
git submodule update --init --recursive
```

## 사용법

시나리오 목록을 확인합니다.

```bash
python sample.py --list-scenarios
```

한국어 대화 한 건을 여섯 턴으로 생성 평가하고 음성까지 합성합니다.

```bash
python sample.py --scenario weekend --language ko --turns 6
```

일본어 여행 대화 세 건을 각각 여섯 턴에서 열두 턴 사이로 만들고 사용자 화자에만 음향 효과를 적용합니다.

```bash
python sample.py \
  --scenario travel \
  --language ja \
  --count 3 \
  --min-turns 6 \
  --max-turns 12 \
  --user-only-augmentation
```

텍스트와 평가 JSON만 만들려면 다음 옵션을 사용합니다.

```bash
python sample.py --scenario random --language en --count 10 --skip-audio
```

기본 모델은 `LiquidAI/LFM3-1.7B`이며 `--model`로 다른 로컬 Hugging Face 모델을 지정할 수 있습니다.
결과는 기본적으로 `output/sample/run_*` 아래에 저장됩니다.

## 생성 순서

```text
시나리오와 페르소나 선택
  -> 두 Agent의 대화 생성
  -> 동일 HF 모델의 일반 텍스트 출력으로 자동 평가
  -> 대화와 평가 JSON 저장
  -> 통과한 대화의 오디오와 annotation 생성
```

SDialog의 구조화 출력 기반 LLM judge 대신 `PASS: 사유` 또는 `FAIL: 사유` 형식의 일반 텍스트 평가를
사용합니다. 따라서 tool calling이나 structured output을 지원하지 않는 로컬 HF 모델도 평가에 사용할 수
있습니다.

## TODO와 현재 미지원 항목

- [ ] 명시적인 backchanneling 생성
  - 현재는 맞장구 발화를 새로 생성하거나 기존 발화 중간에 삽입하지 않습니다.
  - 오디오 `overlap`은 이미 생성된 턴의 시간만 겹치며 새로운 backchannel을 만들지 않습니다.
- [ ] 발화 도중의 자연스러운 interruption 및 turn-taking 모델링
- [ ] 언어별 TTS 지원 여부를 실행 전에 검사하는 기능
- [ ] 생성과 평가에 서로 다른 모델을 지정하는 옵션
- [ ] 대규모 생성 작업의 재시작 및 실패 복구

## 라이선스

이 저장소의 코드는 MIT 라이선스를 따릅니다. SDialog의 라이선스와 저작권 고지는 submodule에서 확인할 수
있습니다.
