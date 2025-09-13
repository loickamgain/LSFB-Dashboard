import pytest
import numpy as np
from route.route import get_real_video_duration_s, format_time
from unittest import mock
import os

# Test de format_time
@pytest.mark.parametrize("input_value, expected", [
    (120000, "02:00"),         # 2 minutes
    (65000, "01:05"),          # 1 minute et 5 secondes
    ("03:45", "03:45"),        # déjà au format MM:SS
    ("invalid", "Invalid time format"),  # invalide
    (None, "Invalid time format"),
])
def test_format_time(input_value, expected):
    assert format_time(input_value) == expected

# Test de get_real_video_duration_s avec un mock
def test_get_real_video_duration_s_file_not_found():
    assert get_real_video_duration_s("fichier_inexistant.mp4") == 0.0

@mock.patch("route.route.MediaInfo")
@mock.patch("os.path.exists", return_value=True)
def test_get_real_video_duration_s_mocked(mock_exists, mock_media_info):
    fake_track = mock.Mock()
    fake_track.track_type = "Video"
    fake_track.duration = 123456
    mock_media_info.parse.return_value.tracks = [fake_track]

    result = get_real_video_duration_s("test.mp4")
    # Vérification du résultat
    assert result == pytest.approx(123.456, rel=1e-4)  # La durée attendue est 123.456 secondes (123456 ms)
