from fastapi import APIRouter, Depends, status
from app.service.pregnancy_service import get_pregnancy_service, PregnancyService
from app.schema.pregnancy_schema import PregnancyCreateDTO
from app.schema.user_schema import UserClaimDTO
from app.schema.common_schema import ApiResponseDTO
from app.dependency.auth_dependency import get_current_user

router = APIRouter()


# 임신 + 태아 등록 (POST /pregnancies)
# user_id는 화면이 보낸 값이 아니라 로그인 토큰에서 꺼낸 값을 쓴다.
@router.post(
    "",
    response_model=ApiResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_pregnancy(
    pregnancy: PregnancyCreateDTO,
    current_user: UserClaimDTO = Depends(get_current_user),
    pregnancy_service: PregnancyService = Depends(get_pregnancy_service),
):
    result = await pregnancy_service.create_pregnancy(current_user.id, pregnancy)
    return ApiResponseDTO(
        success=True,
        message="임신 정보가 등록되었습니다.",
        data=result,
    )
