"""
Tests para VOXMETRIK_V2 API

Ejecutar tests:
    pytest tests/test_api.py
    pytest tests/test_api.py -v  (verbose)
    pytest tests/test_api.py --cov (con cobertura)
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Cliente de prueba
client = TestClient(app)

class TestHealthEndpoints:
    """Tests para endpoints de salud"""
    
    def test_root_endpoint(self):
        """Prueba que el endpoint raíz funciona"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
    
    def test_health_endpoint(self):
        """Prueba que el health check funciona"""
        response = client.get("/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
    
    def test_api_info_endpoint(self):
        """Prueba que el endpoint de info funciona"""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        assert "endpoints_groups" in data

class TestArtistsEndpoints:
    """Tests para endpoints de artistas"""
    
    def test_get_top_artists(self):
        """Prueba obtener top artistas"""
        response = client.get("/artists/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "count" in data
    
    def test_get_top_artists_custom_limit(self):
        """Prueba obtener top artistas con límite personalizado"""
        response = client.get("/artists/top?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) <= 20
    
    def test_get_artists_count(self):
        """Prueba obtener total de artistas"""
        response = client.get("/artists/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_artists" in data["data"]
        assert isinstance(data["data"]["total_artists"], int)
    
    def test_search_artists(self):
        """Prueba buscar artistas"""
        response = client.get("/artists/search/?q=ed&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "search_term" in data
        assert "count" in data
    
    def test_search_artists_empty_term(self):
        """Prueba que búsqueda vacía falla"""
        response = client.get("/artists/search/?q=")
        assert response.status_code in [400, 422]

class TestGenresEndpoints:
    """Tests para endpoints de géneros"""
    
    def test_get_top_genres(self):
        """Prueba obtener top géneros"""
        response = client.get("/genres/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
    
    def test_get_genre_distribution(self):
        """Prueba obtener distribución de géneros"""
        response = client.get("/genres/distribution")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data
    
    def test_get_genres_count(self):
        """Prueba obtener total de géneros"""
        response = client.get("/genres/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_genres" in data["data"]

class TestTracksEndpoints:
    """Tests para endpoints de tracks"""
    
    def test_get_top_tracks(self):
        """Prueba obtener top tracks"""
        response = client.get("/tracks/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
    
    def test_get_tracks_count(self):
        """Prueba obtener total de tracks"""
        response = client.get("/tracks/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_tracks" in data["data"]
    
    def test_search_tracks(self):
        """Prueba buscar tracks"""
        response = client.get("/tracks/search/?q=love&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

class TestStatsEndpoints:
    """Tests para endpoints de estadísticas"""
    
    def test_get_general_stats(self):
        """Prueba obtener estadísticas generales"""
        response = client.get("/stats/general")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_tracks" in data["data"]
        assert "total_artists" in data["data"]
        assert "total_genres" in data["data"]
        assert "total_albums" in data["data"]
    
    def test_get_energy_distribution(self):
        """Prueba obtener distribución de energía"""
        response = client.get("/stats/energy-distribution")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_get_audio_features(self):
        """Prueba obtener características de audio"""
        response = client.get("/stats/audio-features")
        assert response.status_code in [200, 404]
        data = response.json()
        assert "status" in data
    
    def test_get_popularity_distribution(self):
        """Prueba obtener distribución de popularidad"""
        response = client.get("/stats/popularity-distribution")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)

class TestErrorHandling:
    """Tests para manejo de errores"""
    
    def test_invalid_limit(self):
        """Prueba que límite inválido falla"""
        response = client.get("/artists/top?limit=0")
        assert response.status_code in [400, 422]
    
    def test_limit_too_high(self):
        """Prueba que límite muy alto se restringe"""
        response = client.get("/artists/top?limit=1000")
        assert response.status_code in [400, 422]
    
    def test_nonexistent_endpoint(self):
        """Prueba que endpoint inexistente retorna 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

class TestResponseFormat:
    """Tests para formato de respuestas"""
    
    def test_success_response_format(self):
        """Prueba que las respuestas exitosas tienen formato correcto"""
        response = client.get("/artists/top?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "data" in data
    
    def test_response_is_json(self):
        """Prueba que todas las respuestas son JSON válido"""
        response = client.get("/artists/top")
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
