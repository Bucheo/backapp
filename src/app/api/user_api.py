from fastapi import APIRouter, Query, Depends, UploadFile, File, Form
from app.service.user_service import get_user_service, UserService
from app.service.s3_service import get_s3_service, S3Service
from app.enum.user_enum import UserProvider
from app.enum.s3_enum import S3Folder
from app.schema.user_schema import UserCreateDTO, UserClaimDTO, UserUpdateDTO
from app.schema.common_schema import ApiResponseDTO
from app.schema.s3_schema import ImageUploadResponseDTO
from app.dependency.auth_dependency import get_current_user


router = APIRouter()

@router.post(
    "/check-user", 
    response_model=ApiResponseDTO
)
async def check_user(
    user_email: str, 
    user_provider: str, 
    user_service = Depends(get_user_service)
):
    await user_service.check_duplicate_user(user_email, user_provider)
    return ApiResponseDTO(
        success=True,
        message="중복되지 않은 사용자",
    )

