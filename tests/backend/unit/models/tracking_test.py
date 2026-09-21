from app.models.tracking import APPEARANCE_EMBEDDING_DIMENSION, TrackingSubject


def test_tracking_subject_embedding_contract():
    embedding_column = TrackingSubject.__table__.c.reference_embedding

    assert APPEARANCE_EMBEDDING_DIMENSION == 1280
    assert embedding_column.nullable is True
    assert "1280" in str(embedding_column.type)