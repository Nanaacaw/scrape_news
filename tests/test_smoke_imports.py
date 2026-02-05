from pathlib import Path


def test_docker_artifacts_exist():
    assert Path("docker/api.Dockerfile").exists()
    assert Path("docker/worker.Dockerfile").exists()


def test_fastapi_app_imports():
    from src.api.main import app  # noqa: F401


def test_api_schemas_importable():
    from src.api.models.schemas import ArticleResponse  # noqa: F401

