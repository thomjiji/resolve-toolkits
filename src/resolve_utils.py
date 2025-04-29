"""
Utility functions for working with DaVinci Resolve API.
"""

import logging
from typing import Tuple

from dri import Resolve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def initialize_resolve(
    need_media_storage: bool = False,
    need_media_pool: bool = False,
    need_root_folder: bool = False,
    need_current_timeline: bool = False,
    need_current_folder: bool = False,
) -> Tuple:
    """Initialize DaVinci Resolve API and get common objects based on needs.

    Parameters
    ----------
    need_media_storage : bool, optional
        Whether to initialize media storage, by default False
    need_media_pool : bool, optional
        Whether to initialize media pool, by default False
    need_root_folder : bool, optional
        Whether to initialize root folder, by default False
    need_current_timeline : bool, optional
        Whether to initialize current timeline, by default False
    need_current_folder : bool, optional
        Whether to initialize current folder, by default False

    Returns
    -------
    Tuple
        Tuple containing initialized objects based on parameters.
        Always includes resolve, project_manager, and project.
        Other objects are included based on the parameters.
    """
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()

    result = [resolve, project_manager, project]

    if need_media_storage:
        media_storage = resolve.GetMediaStorage()
        result.append(media_storage)

    if need_media_pool:
        media_pool = project.GetMediaPool()

    if need_root_folder:
        if not need_media_pool:
            media_pool = project.GetMediaPool()
        root_folder = media_pool.GetRootFolder()
        result.append(root_folder)

    if need_current_timeline:
        current_timeline = project.GetCurrentTimeline()
        result.append(current_timeline)

    if need_current_folder:
        if not need_media_pool:
            media_pool = project.GetMediaPool()
        current_folder = media_pool.GetCurrentFolder()
        result.append(current_folder)

    # Log what was initialized
    logger.info(f"Initialized Resolve with project: {project.GetName()}")
    if need_current_timeline:
        logger.info(f"Current timeline: {result[-1].GetName()}")

    return tuple(result)
