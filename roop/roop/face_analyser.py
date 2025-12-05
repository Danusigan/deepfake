import threading
from typing import Any, Optional, List
import insightface
import numpy

import roop.globals
from roop.typing import Frame, Face

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()


def get_face_analyser() -> Any:
    global FACE_ANALYSER

    with THREAD_LOCK:
        if FACE_ANALYSER is None:
            FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=roop.globals.execution_providers)
            FACE_ANALYSER.prepare(ctx_id=0)
    return FACE_ANALYSER


def clear_face_analyser() -> Any:
    global FACE_ANALYSER
    FACE_ANALYSER = None


def get_one_face(frame: Frame, position: int = 0) -> Optional[Face]:
    """Get one face - PRIORITIZES FRONT-FACING FACES"""
    many_faces = get_many_faces(frame)
    if many_faces:
        # Sort faces by priority: front-facing first, then by size
        sorted_faces = sort_faces_by_priority(many_faces)
        try:
            return sorted_faces[position]
        except IndexError:
            return sorted_faces[-1]
    return None


def sort_faces_by_priority(faces: List[Face]) -> List[Face]:
    """
    Sort faces by priority:
    1. Front-facing faces (low pose angle) first
    2. Larger faces (closer to camera) first
    """
    def face_priority_score(face):
        # Calculate face size (area)
        bbox = face.bbox
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        size = width * height
        
        # Calculate face angle (frontal vs profile)
        # Lower pose values = more frontal
        pose_penalty = 0
        if hasattr(face, 'pose'):
            # Pose is [pitch, yaw, roll]
            # Yaw is most important for front/back distinction
            yaw = abs(face.pose[1]) if face.pose is not None else 0
            pose_penalty = yaw * 1000  # Heavy penalty for side profiles
        
        # Score: Higher = Better (front-facing + large)
        # Subtract pose penalty (front faces have low yaw)
        score = size - pose_penalty
        
        return score
    
    # Sort descending (highest score first)
    return sorted(faces, key=face_priority_score, reverse=True)


def get_many_faces(frame: Frame) -> Optional[List[Face]]:
    """Get all detected faces"""
    try:
        faces = get_face_analyser().get(frame)
        if faces:
            # Sort by priority automatically
            return sort_faces_by_priority(faces)
        return faces
    except ValueError:
        return None


def find_similar_face(frame: Frame, reference_face: Face) -> Optional[Face]:
    """Find similar face in frame"""
    many_faces = get_many_faces(frame)
    if many_faces:
        for face in many_faces:
            if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
                distance = numpy.sum(numpy.square(face.normed_embedding - reference_face.normed_embedding))
                if distance < roop.globals.similar_face_distance:
                    return face
    return None