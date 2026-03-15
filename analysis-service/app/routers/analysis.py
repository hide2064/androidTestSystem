from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.models.requests import (
    StatisticsRequest,
    TimeseriesRequest,
    DistributionRequest,
    CorrelationRequest,
    GroupbyRequest,
)
from app.models.responses import AnalysisResponse
from app.analyzers import statistics, timeseries, distribution, correlation, groupby

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _run(analysis_type: str, runner, request):
    try:
        with get_connection() as conn:
            data = runner(conn, request)
        return AnalysisResponse(type=analysis_type, data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/statistics", response_model=AnalysisResponse)
def run_statistics(req: StatisticsRequest):
    return _run("statistics", statistics.run, req)


@router.post("/timeseries", response_model=AnalysisResponse)
def run_timeseries(req: TimeseriesRequest):
    return _run("timeseries", timeseries.run, req)


@router.post("/distribution", response_model=AnalysisResponse)
def run_distribution(req: DistributionRequest):
    return _run("distribution", distribution.run, req)


@router.post("/correlation", response_model=AnalysisResponse)
def run_correlation(req: CorrelationRequest):
    return _run("correlation", correlation.run, req)


@router.post("/groupby", response_model=AnalysisResponse)
def run_groupby(req: GroupbyRequest):
    return _run("groupby", groupby.run, req)
