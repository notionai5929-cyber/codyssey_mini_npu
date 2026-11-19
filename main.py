import time

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

if __name__ == "__main__":
    run_user_input_mode()