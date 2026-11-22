from fastapi import APIRouter, Depends, Query

from app.enum.hospital_enum import HospitalTypeEnum
from app.schema.common_schema import ApiResponseDTO
from app.schema.hospital_schema import HospitalVO
from app.service.hospital_service import HospitalService, get_hospital_service


router = APIRouter()


@router.get(
    "/hospitals",
    response_model=ApiResponseDTO[list[HospitalVO]],
    summary="지도용 의료기관 목록 조회",
)
async def get_hospitals(
    hospital_type: HospitalTypeEnum | None = Query(
        default=None, description="원본 종별: 상급종합병원, 종합병원, 병원, 의원, 조산원. 생략하면 전체 목록"
    ),
    service: HospitalService = Depends(get_hospital_service),
):
    # 의료기관의 공개 정보만 반환하므로 로그인 없이 조회할 수 있습니다.
    hospitals = await service.get_hospitals(hospital_type)
    return ApiResponseDTO(success=True, message="의료기관 목록을 조회했습니다.", data=hospitals)
