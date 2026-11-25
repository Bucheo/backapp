from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status

from app.dependency.auth_dependency import get_current_user
from app.schema.common_schema import ApiResponseDTO
from app.schema.post_schema import PostCreateDTO, PostVoteDTO, PostFeedListDTO, PostDetailDTO, POST_CATEGORIES
from app.schema.user_schema import UserClaimDTO
from app.service.community_service import CommunityService, get_community_service

router = APIRouter()


# 로그인한 경우에만 사용자 id 를 돌려준다 (조회처럼 비로그인도 허용하는 API 용)
def get_optional_user_id(request: Request) -> int | None:
    try:
        return get_current_user(request).id
    except HTTPException:
        return None


# 게시글 등록
# POST /communities/posts
@router.post("/posts", summary="게시글 등록", response_model=ApiResponseDTO[PostDetailDTO], status_code=status.HTTP_201_CREATED)
async def create_post(
    dto: PostCreateDTO,
    user: UserClaimDTO = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    post_id = await service.create_post(user.id, dto)
    return ApiResponseDTO(success=True, message="게시글 등록 성공", data=await service.get_post(post_id, user.id))


# 게시글 목록
# GET /communities/posts?category=all&sort=latest&q=&page=1&size=10
@router.get("/posts", summary="게시글 목록", response_model=ApiResponseDTO[PostFeedListDTO])
async def list_posts(
    category: str = Query("all"),
    sort: Literal["popular", "latest"] = Query("latest"),
    q: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    service: CommunityService = Depends(get_community_service),
):
    if category != "all" and category not in POST_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바르지 않은 게시판입니다.")
    data = await service.list_posts(None if category == "all" else category, sort, q, page, size)
    return ApiResponseDTO(success=True, message="게시글 목록 조회 성공", data=data)


# 게시글 상세
# GET /communities/posts/{post_id}
@router.get("/posts/{post_id}", summary="게시글 상세", response_model=ApiResponseDTO[PostDetailDTO])
async def get_post(
    post_id: int,
    viewer_id: int | None = Depends(get_optional_user_id),
    service: CommunityService = Depends(get_community_service),
):
    return ApiResponseDTO(success=True, message="게시글 조회 성공", data=await service.get_post(post_id, viewer_id))


# 투표 (회원당 1회)
# POST /communities/posts/{post_id}/vote
@router.post("/posts/{post_id}/vote", summary="투표하기", response_model=ApiResponseDTO[PostDetailDTO])
async def vote(
    post_id: int,
    dto: PostVoteDTO,
    user: UserClaimDTO = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    return ApiResponseDTO(success=True, message="투표 성공", data=await service.vote(post_id, user.id, dto.option_index))
