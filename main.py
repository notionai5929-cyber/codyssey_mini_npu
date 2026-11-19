import time
import json  # 파일 최상단 import time 아래에 추가


def normalize_label(raw_label):
    """
    expected 값('+', 'x')과 필터 키('cross', 'x')를
    내부 표준 라벨('Cross', 'X')로 정규화합니다.
    """
    if not isinstance(raw_label, str):
        raise ValueError(f"알 수 없는 라벨 형식: {raw_label}")

    key = raw_label.strip().lower()
    mapping = {
        "+": "Cross",
        "cross": "Cross",
        "x": "X",
    }
    if key not in mapping:
        raise ValueError(f"지원하지 않는 라벨 값: {raw_label}")
    return mapping[key]


def extract_size_from_key(pattern_key):
    """
    'size_{N}_{idx}' 형태의 패턴 키에서 N(정수)을 추출합니다.
    """
    parts = pattern_key.split("_")
    if len(parts) < 3 or parts[0] != "size":
        raise ValueError(f"잘못된 패턴 키 형식: {pattern_key}")
    return int(parts[1])


def run_json_analysis_mode(filepath="data.json"):
    """
    모드 2: data.json을 로드하여 필터/패턴 검증, MAC 판정, 성능 분석, 결과 요약을 수행합니다.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"\n오류: '{filepath}' 파일을 찾을 수 없습니다. main.py와 같은 폴더에 배치해 주세요.")
        return
    except json.JSONDecodeError as e:
        print(f"\n오류: '{filepath}' JSON 파싱 실패 ({e})")
        return

    raw_filters = data.get("filters", {})
    patterns = data.get("patterns", {})

    # [1] 필터 로드 및 키 정규화
    print("\n" + "-" * 40)
    print("### [1] 필터 로드")
    print("-" * 40)

    normalized_filters = {}
    for size_key, filter_dict in raw_filters.items():
        norm_dict = {}
        for raw_k, matrix in filter_dict.items():
            std_label = normalize_label(raw_k)
            norm_dict[std_label] = matrix
        normalized_filters[size_key] = norm_dict
        labels_str = ", ".join(norm_dict.keys())
        print(f"✓ {size_key:<7} 필터 로드 완료 ({labels_str})")

    # [2] 패턴 분석 (라벨 정규화 및 크기/스키마 검증)
    print("\n" + "-" * 40)
    print("### [2] 패턴 분석 (라벨 정규화 적용)")
    print("-" * 40)

    total_count = 0
    pass_count = 0
    fail_cases = []
    sample_by_size = {}  # 성능 분석용 크기별 대표 (패턴, 필터) 저장

    for pattern_key, item in patterns.items():
        total_count += 1
        print(f"\n--- {pattern_key} ---")

        try:
            n = extract_size_from_key(pattern_key)
            size_key = f"size_{n}"

            if size_key not in normalized_filters:
                raise ValueError(f"해당 크기의 필터({size_key})가 존재하지 않습니다.")

            filter_set = normalized_filters[size_key]
            if "Cross" not in filter_set or "X" not in filter_set:
                raise ValueError(f"{size_key} 필터에 Cross 또는 X 필터가 누락되었습니다.")

            pattern_matrix = item["input"]
            expected_label = normalize_label(item["expected"])

            # 크기 일치 검증 및 MAC 연산 (불일치 시 mac_operation 내부에서 ValueError 발생)
            cross_score = mac_operation(pattern_matrix, filter_set["Cross"])
            x_score = mac_operation(pattern_matrix, filter_set["X"])

            # 성능 측정을 위해 크기별 첫 번째 정상 케이스 저장
            if n not in sample_by_size:
                sample_by_size[n] = (pattern_matrix, filter_set["Cross"])

            pred = compare_scores(cross_score, x_score, "Cross", "X")

            print(f"Cross 점수: {cross_score:.16g}")
            print(f"X 점수:     {x_score:.16g}")

            if pred == "UNDECIDED":
                reason = f"동점(UNDECIDED) 처리 규칙(|Cross-X| < {EPSILON})에 따라 FAIL"
                print(f"판정: {pred} | expected: {expected_label} | FAIL (동점 규칙)")
                fail_cases.append((pattern_key, reason))
            elif pred == expected_label:
                pass_count += 1
                print(f"판정: {pred} | expected: {expected_label} | PASS")
            else:
                reason = f"예측({pred}) != 기대값({expected_label})"
                print(f"판정: {pred} | expected: {expected_label} | FAIL")
                fail_cases.append((pattern_key, reason))

        except (ValueError, KeyError, TypeError) as e:
            reason = f"데이터/크기 검증 오류: {e}"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_cases.append((pattern_key, reason))

    # [3] 성능 분석 (3x3 포함, 5x5 / 13x13 / 25x25)
    print("\n" + "-" * 40)
    print("### [3] 성능 분석 (평균/10회)")
    print("-" * 40)
    print(f"{'크기':<10}{'평균 시간(ms)':<16}{'연산 횟수'}")

    # 3x3 기본 샘플 측정 추가
    sample_3x3_pattern = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    sample_3x3_filter = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    avg_3x3 = measure_mac_time(sample_3x3_pattern, sample_3x3_filter, repeat=10)
    print(f"{'3x3':<10}{avg_3x3:<16.4f}{3 * 3}")

    for n in sorted(sample_by_size.keys()):
        pat, flt = sample_by_size[n]
        avg_ms = measure_mac_time(pat, flt, repeat=10)
        print(f"{f'{n}x{n}':<10}{avg_ms:<16.4f}{n * n}")

    # [4] 결과 요약
    fail_count = len(fail_cases)
    print("\n" + "-" * 40)
    print("### [4] 결과 요약")
    print("-" * 40)
    print(f"총 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {fail_count}개")

    if fail_cases:
        print("\n실패 케이스:")
        for case_id, reason in fail_cases:
            print(f"- {case_id}: {reason}")

EPSILON = 1e-9  # 부동소수점 오차 허용 기준


def mac_operation(pattern, filter_matrix):
    """
    N x N 크기의 입력 패턴과 필터에 대해 위치별 곱셈 후 누적합(MAC)을 계산합니다.
    크기가 일치하지 않으면 ValueError를 발생시킵니다.
    """
    rows = len(pattern)
    if rows == 0 or rows != len(filter_matrix):
        raise ValueError("패턴과 필터의 행 크기가 일치하지 않습니다.")

    total = 0.0
    for i in range(rows):
        if len(pattern[i]) != rows or len(filter_matrix[i]) != rows:
            raise ValueError(f"{i}번째 행의 열 크기가 일치하지 않거나 정사각 행렬이 아닙니다.")
        for j in range(rows):
            total += float(pattern[i][j]) * float(filter_matrix[i][j])

    return total


def compare_scores(score_a, score_b, label_a="A", label_b="B", epsilon=EPSILON):
    """
    두 필터의 MAC 점수를 비교해 승자 라벨을 반환합니다.
    두 점수의 차이가 epsilon 미만이면 동점(UNDECIDED)으로 판정합니다.
    """
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b


def measure_mac_time(pattern, filter_matrix, repeat=10):
    """
    I/O를 제외하고 MAC 연산 함수만 repeat회 반복 실행하여 평균 시간(ms)을 반환합니다.
    """
    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation(pattern, filter_matrix)
    end = time.perf_counter()

    avg_ms = ((end - start) / repeat) * 1000
    return avg_ms

def input_matrix(name, size=3):
    """
    사용자로부터 size x size 크기의 행렬을 한 줄씩(공백 구분) 입력받습니다.
    열 개수 불일치나 숫자 변환 실패 시 안내 문구를 출력하고 해당 줄을 재입력받습니다.
    """
    print(f"\n{name} ({size}줄 입력, 공백 구분)")
    matrix = []
    for row_idx in range(size):
        while True:
            raw = input(f"  {row_idx + 1}행: ").strip()
            parts = raw.split()
            if len(parts) != size:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                continue
            try:
                row = [float(x) for x in parts]
                matrix.append(row)
                break
            except ValueError:
                print("입력 형식 오류: 숫자만 입력할 수 있습니다. 다시 입력하세요.")
    return matrix


def run_user_input_mode():
    """
    모드 1: 사용자 입력 (3x3) 전체 흐름을 실행합니다.
    필터 A, B 입력 -> 저장 확인 -> 패턴 입력 -> MAC 연산 -> 판정 -> 성능 분석(3x3)
    """
    print("\n" + "-" * 40)
    print("### [1] 필터 입력")
    print("-" * 40)
    filter_a = input_matrix("필터 A", 3)
    filter_b = input_matrix("필터 B", 3)
    print("\n✓ 필터 A, B 저장 완료")

    print("\n" + "-" * 40)
    print("### [2] 패턴 입력")
    print("-" * 40)
    pattern = input_matrix("패턴", 3)

    # MAC 연산 및 판정
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    winner = compare_scores(score_a, score_b, "A", "B")

    # 3x3 성능 측정 (I/O 제외, 10회 반복 평균)
    avg_time_ms = measure_mac_time(pattern, filter_a, repeat=10)

    print("\n" + "-" * 40)
    print("### [3] MAC 결과")
    print("-" * 40)
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time_ms:.4f} ms")
    if winner == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {winner}")

    print("\n" + "-" * 40)
    print("### [4] 성능 분석 (3x3, 평균/10회)")
    print("-" * 40)
    print(f"{'크기':<10}{'평균 시간(ms)':<16}{'연산 횟수'}")
    print(f"{'3x3':<10}{avg_time_ms:<16.4f}{3 * 3}")

def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("0. 종료")

        choice = input("선택: ").strip()
        if choice == "1":
            run_user_input_mode()
        elif choice == "2":
            run_json_analysis_mode("data.json")
        elif choice == "0":
            print("시뮬레이터를 종료합니다.")
            break
        else:
            print("입력 오류: 1, 2, 0 중 하나를 선택하세요.")
            
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n시뮬레이터를 안전하게 종료합니다.")