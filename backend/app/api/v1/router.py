"""Aggregated v1 API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.auth import router as auth_router
from app.api.v1.brokers import router as brokers_router
from app.api.v1.detection_config import router as detection_config_router
from app.api.v1.instruments import router as instruments_router
from app.api.v1.profile import router as profile_router
from app.api.v1.trendlines import router as trendlines_router
from app.api.v1.watchlist import router as watchlist_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(brokers_router)
router.include_router(api_keys_router)
router.include_router(instruments_router)
router.include_router(trendlines_router)
router.include_router(watchlist_router)
router.include_router(detection_config_router)
router.include_router(alerts_router)
