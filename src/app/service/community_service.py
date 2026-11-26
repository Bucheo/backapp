import math

from fastapi import Depends, HTTPException, status

from app.enum.post_enum import PostCategory, PostStatus, PostWriterType
from app.model.post_model import Post
from app.model.post_extra_model import PostExtra, PostPhoto
from app.repository.community_repository import CommunityRepository, get_community_repository
from app.schema.post_schema import (
    CATEGORY_TO_ENUM, ENUM_TO_CATEGORY,
    PostCreateDTO, PostFeedItemDTO, PostFeedListDTO, PostDetailDTO,
    PostVideoOutDTO, PostPlaceDTO, PostPollOutDTO, PostPollOptionOutDTO,
)


WRITER_TYPE_LABELS = {
    PostWriterType.GUARDIAN.value: "보호자",
    PostWriterType.EXPECTANT_MOM.value: "예비맘",
    PostWriterType.PARENTING_MOM.value: "육아맘",
}


# DB 카테고리(PostCategory 값) 기준 작성자 타입
def _writer_type(db_category: str) -> str:
    if db_category == PostCategory.PARENTING_STORY.value:
        return PostWriterType.PARENTING_MOM.value
    return PostWriterType.EXPECTANT_MOM.value


# 화면에 보여줄 작성자 태그(한글)
def _author_tag(db_category: str) -> str:
    return WRITER_TYPE_LABELS[_writer_type(db_category)]


class CommunityService:
    def __init__(self, repo: CommunityRepository):
        self.repo = repo

    async def create_post(self, user_id: int, dto: PostCreateDTO) -> int:
        db_category = CATEGORY_TO_ENUM[dto.category].value
        post = Post(
            post_category=db_category,
            post_title=dto.title,
            post_content=dto.content,
            post_status=PostStatus.POSTING.value,
            post_writer_type=_writer_type(db_category),  # 카테고리 기준 작성자 타입
            user_id=user_id,
        )
        extra = PostExtra(
            post_prefix=dto.prefix,
            video_key=dto.video.key if dto.video else None,
            video_url=dto.video.url if dto.video else None,
            video_duration=dto.video.duration if dto.video else None,
            place_name=dto.place.name.strip() if dto.place else None,
            place_address=dto.place.address.strip() if dto.place else None,
            poll_question=dto.poll.question.strip() if dto.poll else None,
            poll_options=dto.poll.options if dto.poll else None,
        )
        photos = [
            PostPhoto(photo_key=p.key, photo_url=p.url, thumb_url=p.thumb_url, photo_order=i)
            for i, p in enumerate(dto.photos)
        ]
        created = await self.repo.create_post(post, extra, photos)
        return int(created.id)

    async def list_posts(self, category: str | None, sort: str, q: str, page: int, size: int) -> PostFeedListDTO:
        db_category = CATEGORY_TO_ENUM[category].value if category in CATEGORY_TO_ENUM else category
        rows, total = await self.repo.list_posts(db_category, sort, q.strip(), page, size)
        items = [
            PostFeedItemDTO(
                id=post.id,
                category=ENUM_TO_CATEGORY.get(post.post_category, post.post_category),
                author_tag=_author_tag(post.post_category),
                title=post.post_title,
                author_name=nickname,
                thumbnail_url=thumb,
                like_count=post.post_like,
                comment_count=comments,
                view_count=0,
                created_at=post.post_created_at,
            )
            for post, nickname, comments, thumb in rows
        ]
        return PostFeedListDTO(
            items=items,
            page=page,
            page_size=size,
            total_count=total,
            total_pages=max(1, math.ceil(total / size)),
        )

    async def get_post(self, post_id: int, viewer_id: int | None) -> PostDetailDTO:
        row = await self.repo.get_post(post_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
        post, nickname, comments = row

        extra = await self.repo.get_extra(post_id)
        photos = await self.repo.get_photos(post_id)

        poll = None
        if extra and extra.poll_question and extra.poll_options:
            counts = await self.repo.get_vote_counts(post_id)
            my_vote = await self.repo.get_my_vote(post_id, viewer_id) if viewer_id else None
            poll = PostPollOutDTO(
                question=extra.poll_question,
                options=[PostPollOptionOutDTO(text=text, votes=counts.get(i, 0)) for i, text in enumerate(extra.poll_options)],
                my_vote=my_vote,
            )

        video = PostVideoOutDTO(url=extra.video_url, duration=extra.video_duration or 0) if extra and extra.video_url else None
        place = PostPlaceDTO(name=extra.place_name, address=extra.place_address or "") if extra and extra.place_name else None

        return PostDetailDTO(
            id=post.id,
            category=ENUM_TO_CATEGORY.get(post.post_category, post.post_category),
            author_tag=_author_tag(post.post_category),
            title=post.post_title,
            author_name=nickname,
            thumbnail_url=photos[0].photo_url if photos else None,
            like_count=post.post_like,
            comment_count=comments,
            view_count=0,
            created_at=post.post_created_at,
            prefix=extra.post_prefix if extra else "질문",
            content=post.post_content,
            photos=[p.photo_url for p in photos],
            video=video,
            place=place,
            poll=poll,
        )

    async def vote(self, post_id: int, user_id: int, option_index: int) -> PostDetailDTO:
        extra = await self.repo.get_extra(post_id)
        if not extra or not extra.poll_options:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="투표가 없는 게시글입니다.")
        if option_index >= len(extra.poll_options):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바르지 않은 투표 항목입니다.")
        if not await self.repo.add_vote(post_id, user_id, option_index):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 투표했습니다.")
        return await self.get_post(post_id, user_id)


def get_community_service(repo: CommunityRepository = Depends(get_community_repository)):
    return CommunityService(repo)
