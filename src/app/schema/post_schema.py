from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from datetime import datetime
from app.enum.post_enum import PostStatus, PostWriterType, PostCategory

# VO (ERD 테이블: posts / 게시글)
class PostVO(BaseModel):
    id: int

    post_category: PostCategory
    post_title: str
    post_content: str
    post_status: PostStatus
    post_created_at: datetime
    post_updated_at: datetime | None = None
    post_like: int
    post_writer_type: PostWriterType

    user_id: int


# ---------------------------------------------------------------------------
# 커뮤니티 게시글 API DTO (프론트와 camelCase 로 주고받는다)
# ---------------------------------------------------------------------------
# 프론트가 쓰는 게시판 값 -> DB(PostCategory enum) 값
CATEGORY_TO_ENUM = {
    "pregnancy": PostCategory.PREGNANCY_STORY,
    "parenting": PostCategory.PARENTING_STORY,
    "neighborhood": PostCategory.NEIGHBORHOOD,
    "health": PostCategory.HEALTH,
    "living": PostCategory.LIVELIHOOD,
}
ENUM_TO_CATEGORY = {enum.value: key for key, enum in CATEGORY_TO_ENUM.items()}
POST_CATEGORIES = tuple(CATEGORY_TO_ENUM.keys())
POST_PREFIXES = ("질문", "후기", "정보 공유", "일상")
MAX_VIDEO_SECONDS = 60


class _CamelDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class PostPhotoInDTO(_CamelDTO):
    key: str
    url: str
    thumb_url: str | None = None


class PostVideoInDTO(_CamelDTO):
    key: str
    url: str
    duration: int = Field(ge=0, le=MAX_VIDEO_SECONDS)  # 최대 1분


class PostPlaceDTO(_CamelDTO):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=300)


class PostPollInDTO(_CamelDTO):
    question: str = Field(min_length=1, max_length=300)
    options: list[str] = Field(min_length=2, max_length=5)

    @field_validator("options")
    @classmethod
    def _clean_options(cls, options: list[str]) -> list[str]:
        cleaned = [option.strip() for option in options if option.strip()]
        if len(cleaned) < 2:
            raise ValueError("투표 항목은 2개 이상이어야 합니다.")
        return cleaned


class PostCreateDTO(_CamelDTO):
    category: str
    prefix: str = "질문"
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    is_public: bool = True
    photos: list[PostPhotoInDTO] = Field(default_factory=list, max_length=10)
    video: PostVideoInDTO | None = None
    place: PostPlaceDTO | None = None
    poll: PostPollInDTO | None = None

    @field_validator("category")
    @classmethod
    def _check_category(cls, value: str) -> str:
        if value not in POST_CATEGORIES:
            raise ValueError("올바르지 않은 게시판입니다.")
        return value

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, value: str) -> str:
        if value not in POST_PREFIXES:
            raise ValueError("올바르지 않은 말머리입니다.")
        return value

    @field_validator("title", "content")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("비어 있을 수 없습니다.")
        return value


class PostVoteDTO(_CamelDTO):
    option_index: int = Field(ge=0)


# 목록 한 건 (프론트 FeedPost)
class PostFeedItemDTO(_CamelDTO):
    id: int
    category: str
    author_tag: str
    title: str
    author_name: str
    thumbnail_url: str | None = None
    like_count: int
    comment_count: int
    view_count: int
    created_at: datetime


class PostFeedListDTO(_CamelDTO):
    items: list[PostFeedItemDTO]
    page: int
    page_size: int
    total_count: int
    total_pages: int


class PostVideoOutDTO(_CamelDTO):
    url: str
    duration: int


class PostPollOptionOutDTO(_CamelDTO):
    text: str
    votes: int


class PostPollOutDTO(_CamelDTO):
    question: str
    options: list[PostPollOptionOutDTO]
    my_vote: int | None = None


class PostDetailDTO(PostFeedItemDTO):
    prefix: str
    content: str
    photos: list[str]
    video: PostVideoOutDTO | None = None
    place: PostPlaceDTO | None = None
    poll: PostPollOutDTO | None = None
