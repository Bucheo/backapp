from fastapi import Depends
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgresql import get_postgresql_db
from app.enum.post_enum import PostStatus
from app.model.post_model import Post
from app.model.comment_model import Comment
from app.model.user_model import User
from app.model.post_extra_model import PostExtra, PostPhoto, PostPollVote


def _comment_count():
    return select(func.count(Comment.id)).where(Comment.post_id == Post.id).correlate(Post).scalar_subquery()


class CommunityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 게시글 + 부가 정보 + 사진을 한 트랜잭션으로 저장
    async def create_post(self, post: Post, extra: PostExtra, photos: list[PostPhoto]) -> Post:
        try:
            self.db.add(post)
            await self.db.flush()  # post.id 확보
            extra.post_id = post.id
            self.db.add(extra)
            for photo in photos:
                photo.post_id = post.id
                self.db.add(photo)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return post

    async def list_posts(self, category: str | None, sort: str, q: str, page: int, size: int):
        first_photo = (
            select(PostPhoto.photo_url)
            .where(PostPhoto.post_id == Post.id)
            .order_by(PostPhoto.photo_order, PostPhoto.id)
            .limit(1)
            .correlate(Post)
            .scalar_subquery()
        )

        conditions = [Post.post_status == PostStatus.POSTING.value]
        if category:
            conditions.append(Post.post_category == category)
        if q:
            like = f"%{q}%"
            conditions.append(or_(Post.post_title.ilike(like), Post.post_content.ilike(like)))

        total = (await self.db.execute(select(func.count()).select_from(Post).where(*conditions))).scalar_one()

        if sort == "popular":
            order = [Post.post_like.desc(), Post.id.desc()]
        else:
            order = [Post.post_created_at.desc(), Post.id.desc()]

        rows = (
            await self.db.execute(
                select(Post, User.user_nickname, _comment_count(), first_photo)
                .join(User, User.id == Post.user_id)
                .where(*conditions)
                .order_by(*order)
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
        return rows, total

    async def get_post(self, post_id: int):
        return (
            await self.db.execute(
                select(Post, User.user_nickname, _comment_count())
                .join(User, User.id == Post.user_id)
                .where(Post.id == post_id, Post.post_status == PostStatus.POSTING.value)
            )
        ).first()

    async def get_extra(self, post_id: int) -> PostExtra | None:
        return await self.db.get(PostExtra, post_id)

    async def get_photos(self, post_id: int) -> list[PostPhoto]:
        result = await self.db.execute(
            select(PostPhoto).where(PostPhoto.post_id == post_id).order_by(PostPhoto.photo_order, PostPhoto.id)
        )
        return list(result.scalars().all())

    async def get_vote_counts(self, post_id: int) -> dict[int, int]:
        result = await self.db.execute(
            select(PostPollVote.option_index, func.count())
            .where(PostPollVote.post_id == post_id)
            .group_by(PostPollVote.option_index)
        )
        return {index: count for index, count in result.all()}

    async def get_my_vote(self, post_id: int, user_id: int) -> int | None:
        result = await self.db.execute(
            select(PostPollVote.option_index).where(PostPollVote.post_id == post_id, PostPollVote.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # 회원당 1표. 이미 투표했으면 False
    async def add_vote(self, post_id: int, user_id: int, option_index: int) -> bool:
        try:
            self.db.add(PostPollVote(post_id=post_id, user_id=user_id, option_index=option_index))
            await self.db.commit()
            return True
        except IntegrityError:
            await self.db.rollback()
            return False


def get_community_repository(db: AsyncSession = Depends(get_postgresql_db)):
    return CommunityRepository(db)
