from pydantic import BaseModel

# VO (ERD 테이블: post_extras / 게시글 부가 정보)
# PK이면서 posts를 참조하는 FK (1:1)
class PostExtraVO(BaseModel):
    post_id: int

    post_prefix: str
    video_key: str | None = None
    video_url: str | None = None
    video_duration: int | None = None
    place_name: str | None = None
    place_address: str | None = None
    poll_question: str | None = None
    poll_options: list | None = None


# VO (ERD 테이블: post_photos / 게시글 사진)
class PostPhotoVO(BaseModel):
    id: int

    photo_key: str
    photo_url: str
    thumb_url: str | None = None
    photo_order: int = 0

    post_id: int


# VO (ERD 테이블: post_poll_votes / 투표 참여)
class PostPollVoteVO(BaseModel):
    id: int

    option_index: int

    post_id: int
    user_id: int
