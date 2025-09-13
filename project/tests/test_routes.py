import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from route.route import router

# App de test avec router
app = FastAPI()
app.include_router(router)

# Monter les fichiers statiques
static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.isdir(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# --------------------------
# Mocks et overrides
# --------------------------

@pytest.fixture
def mock_db_session():
    mock = MagicMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.all.return_value = []

    mock.execute = AsyncMock(return_value=mock_result)
    mock.scalar = AsyncMock(return_value=0)
    mock.scalar_one_or_none = AsyncMock(return_value=None)

    return mock

@pytest.fixture(autouse=True)
def override_dependencies(mock_db_session):
    from database import db_init
    app.dependency_overrides[db_init.get_db_cont] = lambda: mock_db_session
    app.dependency_overrides[db_init.get_db_isol] = lambda: mock_db_session

# --------------------------
# ROUTES HTML STATIQUES
# --------------------------
@pytest.mark.parametrize("url", [
    "/about.html", "/contact.html", "/lsfb.html", 
    "/statistics.html", "/suggestions.html",
    "/video_view_cont.html", "/video_view_isol.html"
])
def test_static_pages(url):
    client = TestClient(app)
    response = client.get(url)
    assert response.status_code == 200

# --------------------------
# ROUTES DYNAMIQUES : CONT
# --------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("params", [
    {"term": "bonjour", "submitType": "search"},
    {"term": "", "submitType": "filter"}
])
async def test_results_cont(params):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/results_cont", params=params)
        await response.aread()
        assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_get_segments():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/get_segments/1")  # Remplacer 1 par un ID valide
        assert response.status_code == 200
        data = response.json()
        assert "segments_list" in data
        assert isinstance(data["segments_list"], list)

@pytest.mark.asyncio
async def test_get_cont_poses(mock_db_session):
    # Préparer le mock pour simuler les données
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
        MagicMock(pose_part="left_hand", pose_path="path/to/cont_pose1.npy"),
        MagicMock(pose_part="right_hand", pose_path="path/to/cont_pose2.npy"),
    ]
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/cont_poses/valid_video_id")  # Remplacer valid_video_id par un ID valide
        data = response.json()
        
        assert response.status_code == 200
        assert "pose_paths" in data
        assert isinstance(data["pose_paths"], dict)
        assert "left_hand" in data["pose_paths"]
        assert "right_hand" in data["pose_paths"]
        assert len(data["pose_paths"]["left_hand"]) == 1  # Vérifie qu'il y a une pose pour la main gauche
        assert len(data["pose_paths"]["right_hand"]) == 1  # Vérifie qu'il y a une pose pour la main droite



# --------------------------
# ROUTES DYNAMIQUES : ISOL
# --------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("params", [
    {"term": "manger", "submitType": "search"},
    {"term": "manger", "submitType": "filter"}
])
async def test_results_isol(params):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/results_isol", params=params)
        await response.aread()
        assert response.status_code in [200, 422]

# --------------------------
# ROUTES VIDÉO
# --------------------------
@pytest.mark.asyncio
async def test_get_video_cont_missing_param():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/video/cont/999")
        assert response.status_code == 422  # previous_term est requis

@pytest.mark.asyncio
async def test_get_video_cont_bad_term():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/video/cont/999", params={"previous_term": "test"})
        await response.aread()
        assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_video_isol_ok_or_fail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/video/isol/999", params={"previous_term": "bonjour"})
        await response.aread()
        assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_get_isol_poses(mock_db_session):
    # Préparer le mock pour simuler les données
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
        MagicMock(pose_part="left_hand", pose_path="path/to/pose1.npy"),
        MagicMock(pose_part="right_hand", pose_path="path/to/pose2.npy"),
    ]
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/isol_poses/valid_video_id")  # Remplacer valid_video_id par un ID valide
        data = response.json()
        
        assert response.status_code == 200
        assert "pose_paths" in data
        assert isinstance(data["pose_paths"], dict)
        assert "left_hand" in data["pose_paths"]
        assert "right_hand" in data["pose_paths"]
        assert len(data["pose_paths"]["left_hand"]) == 1  # Vérifie qu'il y a une pose pour la main gauche
        assert len(data["pose_paths"]["right_hand"]) == 1  # Vérifie qu'il y a une pose pour la main droite


# --------------------------
# STATISTIQUES
# --------------------------
@pytest.mark.asyncio
async def test_stats_general():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/general")
        await response.aread()
        assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_stats_videos_info():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/videos/info")
        await response.aread()
        assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_stats_poses_distribution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/poses/distribution")
        await response.aread()
        assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_stats_signers_variability():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/signers/variability")
        await response.aread()
        assert response.status_code in [200, 422]

# --------------------------
# VISUALISATIONS
# --------------------------
@pytest.mark.asyncio
async def test_stats_gloss_histogram():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/visualizations/histogram", params={"top": 10})
        await response.aread()
        assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_stats_top_subtitles():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/visualizations/top_subtitles", params={"top": 10})
        await response.aread()
        assert response.status_code in [200, 422]

# --------------------------
# FRÉQUENCE GLOSSES
# --------------------------
@pytest.mark.asyncio
async def test_stats_gloss_frequency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/stats/glosses/frequency")
        await response.aread()
        assert response.status_code in [200, 422]
