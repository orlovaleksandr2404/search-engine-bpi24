def test_healthcheck():
    # Базовый тест чтобы pytest в ci/cd не падал из-за отсутствия тестов
    assert True

def test_math_basic():
    assert 2 + 2 == 4
