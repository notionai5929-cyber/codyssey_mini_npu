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

if __name__ == "__main__":
    cross_filter = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    x_filter = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
    test_pattern = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]

    score_a = mac_operation(test_pattern, cross_filter)
    score_b = mac_operation(test_pattern, x_filter)
    result = compare_scores(score_a, score_b, "Cross", "X")
    avg_time = measure_mac_time(test_pattern, cross_filter, repeat=10)

    print(f"Cross 점수: {score_a}, X 점수: {score_b}")
    print(f"판정: {result} | 평균 시간(10회): {avg_time:.4f} ms")