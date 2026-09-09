import numpy as np

from ai.pipeline.utils.thumbnail import annotate_frame


def test_annotate_frame_draws_a_box_without_model_inference():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    annotated = annotate_frame(
        frame,
        [
            {
                "track_id": "threat_0",
                "confidence": 0.91,
                "bbox": [20, 30, 80, 90],
                "detection_type": "gun" 
            }
        ]  
    )

    assert annotated.shape == frame.shape

    assert not np.array_equal(annotated, frame)

    ##  ensuring the input frame was not modified in place

    assert np.array_equal(
        frame,
        np.zeros((120, 160, 3), dtype=np.uint8) 

        
    )