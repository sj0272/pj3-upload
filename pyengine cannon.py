import pygame
import math

# 초기 설정
pygame.init()

# 화면 크기와 색상 정의
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

COLORS = [RED, ORANGE, GREEN, BLUE, PURPLE]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cannon Simulation")
clock = pygame.time.Clock()

# 물리 상수
g = 9.8  # 중력 가속도 (m/s^2)

# 대포 초기 위치
cannon_x, cannon_y = 100, HEIGHT - 50

# 목표물 위치
target_x, target_y = 700, HEIGHT - 100
target_radius = 30

# 대포 공격 세기 관련 상수
min_power = 30
max_power = 100
power_increment = 1
current_power = min_power
power_increasing = True

# 이전 궤적 저장
previous_trajectories = []
max_previous_trajectories = 5

# 점수 저장
total_attempts = []  # 개별 점수 저장

# 각도 변경 속도
angle_change_speed = 0.5

def calculate_trajectory(angle, speed):
    """발사 각도와 초기 속도를 기반으로 궤적 계산"""
    trajectory = []
    angle_rad = math.radians(angle)
    
    for t in range(0, 200, 2):  # 시간 단위를 늘리며 계산 (간격 조정)
        t /= 10  # 시간을 0.1초 단위로 계산
        x = speed * math.cos(angle_rad) * t
        y = speed * math.sin(angle_rad) * t - 0.5 * g * t**2

        if y < 0:  # 땅에 닿으면 계산 중지
            break

        trajectory.append((cannon_x + int(x), cannon_y - int(y)))

    return trajectory

def calculate_area(angle, speed):
    """발사 각도와 초기 속도를 기반으로 궤적 아래의 면적 계산"""
    angle_rad = math.radians(angle)
    max_time = (2 * speed * math.sin(angle_rad)) / g  # 비행 시간
    time_step = 0.01  # 시간 간격
    area = 0
    t = 0

    while t <= max_time:
        x = speed * math.cos(angle_rad) * t  # 가로 이동 거리
        y = max(speed * math.sin(angle_rad) * t - 0.5 * g * t**2, 0)  # 수직 이동 거리
        area += y * time_step  # 작은 직사각형 면적을 더함
        t += time_step

    return area

def calculate_distance(trajectory):
    """궤적에서 가장 먼 비거리 계산"""
    max_distance = 0
    for point in trajectory:
        distance = point[0] - cannon_x
        if distance > max_distance:
            max_distance = distance
    return max_distance

def calculate_position_weight(trajectory):
    """공의 마지막 위치를 기준으로 상수값을 계산 (1에서 점진적으로 감소)"""
    final_x = trajectory[-1][0] if trajectory else cannon_x
    final_distance = abs(target_x - final_x)
    max_distance = abs(target_x - cannon_x)
    return max(0.1, 1 - (final_distance / max_distance))

def draw_power_bar(current_power, min_power, max_power):
    """충전 중인 파워를 막대기로 표시"""
    bar_x, bar_y = 10, 70
    bar_width, bar_height = 200, 20
    filled_width = (current_power - min_power) / (max_power - min_power) * bar_width
    
    pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))  # 바 테두리
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, filled_width, bar_height))  # 채워진 부분

def draw_explosion(x, y):
    """목표물 명중 시 폭죽 효과 (팔방향으로)"""
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    for i in range(8):
        for dx, dy in directions:
            pygame.draw.circle(screen, YELLOW, (x + i * 5 * dx, y + i * 5 * dy), 5)
        pygame.display.flip()
        pygame.time.wait(50)

def main():
    global current_power, power_increasing

    running = True
    angle = 45  # 초기 발사 각도
    trajectory = []
    fired = False
    charging_power = False
    angle_velocity = 0  # 각도 변경 속도

    while running:
        screen.fill(WHITE)

        # 점수 표시 (오른쪽 위 정렬)
        font = pygame.font.Font(None, 36)
        for i, score in enumerate(total_attempts[-5:]):
            color = COLORS[i % len(COLORS)]  # 점수 색상
            score_text = font.render(f"{i + 1}: {score} pts", True, color)
            screen.blit(score_text, (WIDTH - 150, 10 + i * 30))

        # 각도 표시
        angle_text = font.render(f"Angle: {angle:.1f}°", True, BLACK)
        screen.blit(angle_text, (10, 10))

        # 이전 궤적 그리기
        for i, prev_traj in enumerate(previous_trajectories):
            color = COLORS[i % len(COLORS)]
            for point in prev_traj:
                pygame.draw.circle(screen, color, point, 8)  # 공의 크기를 조금 키움

            # 궤적 중앙에 번호 표시
            if prev_traj:
                midpoint = prev_traj[len(prev_traj) // 2]
                number_text = font.render(str(i + 1), True, color)
                screen.blit(number_text, (midpoint[0] - 10, midpoint[1] - 10))

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not fired:
                    charging_power = True
                if event.key == pygame.K_UP:
                    angle_velocity = -angle_change_speed
                elif event.key == pygame.K_DOWN:
                    angle_velocity = angle_change_speed

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and not fired:
                    speed = current_power
                    trajectory = calculate_trajectory(angle, speed)
                    previous_trajectories.insert(0, trajectory)  # 가장 최근 궤적을 맨 앞으로 추가
                    if len(previous_trajectories) > max_previous_trajectories:
                        previous_trajectories.pop()  # 최대 개수 초과 시 오래된 궤적 삭제
                    area = calculate_area(angle, speed)
                    distance = calculate_distance(trajectory)
                    position_weight = calculate_position_weight(trajectory)

                    # 점수 계산 및 저장
                    area_score = int(area // 10)  # 면적 점수
                    distance_score = int(distance // 10)  # 비거리 점수
                    attempt_score = int((area_score * 0.6 + distance_score * 0.4) * position_weight)  # 가중 평균 및 위치 가중치 적용

                    # 궤적 표시 모드 (컷씬)
                    for point in trajectory:
                        screen.fill(WHITE)

                        # 대포 및 목표물 그리기
                        pygame.draw.rect(screen, BLACK, (cannon_x - 20, cannon_y - 10, 40, 20))
                        pygame.draw.line(screen, RED, (cannon_x, cannon_y),
                                         (cannon_x + 50 * math.cos(math.radians(angle)),
                                          cannon_y - 50 * math.sin(math.radians(angle))), 5)
                        pygame.draw.circle(screen, BLUE, (target_x, target_y), target_radius)

                        # 궤적 점 그리기
                        pygame.draw.circle(screen, RED, point, 8)  # 공의 크기를 증가시킴
                        pygame.display.flip()
                        clock.tick(30)  # 발사 과정 집중 (컷씬 속도 조정)

                    pygame.time.wait(500)  # 컷씬 대기 시간 추가

                    # 목표물 명중 확인
                    for point in trajectory:
                        if math.hypot(point[0] - target_x, point[1] - target_y) <= target_radius:
                            draw_explosion(target_x, target_y)
                            attempt_score += 200  # 명중 시 추가 점수
                            font = pygame.font.Font(None, 50)
                            bonus_text = font.render("+200", True, YELLOW)
                            screen.blit(bonus_text, (target_x - 20, target_y - 40))
                            pygame.display.flip()
                            pygame.time.wait(1000)
                            break

                    total_attempts.append(attempt_score)  # 개별 점수 저장
                    if len(total_attempts) > 10:
                        total_attempts.pop(0)  # 이전 기록 유지

                    charging_power = False

                    fired = False  # 발사 완료 후 초기화
                    current_power = min_power  # 발사 후 세기 초기화

                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    angle_velocity = 0

        # 각도 변경
        angle += angle_velocity
        angle = max(0, min(angle, 90))  # 각도 제한

        # 대포 세기 충전
        if charging_power:
            if power_increasing:
                current_power += power_increment
                if current_power >= max_power:
                    power_increasing = False
            else:
                current_power -= power_increment
                if current_power <= min_power:
                    power_increasing = True

            # 파워 바 그리기
            draw_power_bar(current_power, min_power, max_power)

        # 대포 및 목표물, 인터페이스 그리기
        if not fired:
            pygame.draw.rect(screen, BLACK, (cannon_x - 20, cannon_y - 10, 40, 20))
            pygame.draw.line(screen, RED, (cannon_x, cannon_y),
                             (cannon_x + 50 * math.cos(math.radians(angle)),
                              cannon_y - 50 * math.sin(math.radians(angle))), 5)
            pygame.draw.circle(screen, BLUE, (target_x, target_y), target_radius)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
