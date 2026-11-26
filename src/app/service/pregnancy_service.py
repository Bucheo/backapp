import secrets
import string

from fastapi import Depends, HTTPException
from app.repository.pregnancy_repository import PregnancyRepository, get_pregnancy_repository
from app.schema.pregnancy_schema import PregnancyCreateDTO
from app.enum.pregnancy_enum import PregnancyStatus

# 보호자 승인 코드 설정 (ERD: VARCHAR(20) 이하)
PREGNANCY_CODE_LENGTH = 8
PREGNANCY_CODE_CHARS = string.ascii_uppercase + string.digits
PREGNANCY_CODE_MAX_TRIES = 10  # 중복 코드가 계속 나올 때 무한 반복 방지


# 규칙 검사, 값 채우기, 순서 정하기를 담당 (DB 작업은 repository에 맡긴다)
class PregnancyService:

    def __init__(self, repo: PregnancyRepository):   # repository를 받아서 보관
        self.repo = repo


    # 보호자 승인 코드 생성: 추측하기 어렵게 secrets를 쓰고, DB에 없는 코드가 나올 때까지 시도
    async def _generate_unique_code(self) -> str:
        for _ in range(PREGNANCY_CODE_MAX_TRIES):
            code = "".join(secrets.choice(PREGNANCY_CODE_CHARS) for _ in range(PREGNANCY_CODE_LENGTH))
            if not await self.repo.exists_pregnancy_by_code(code):
                return code

        raise HTTPException(
            status_code=500,
            detail="승인 코드 생성에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )


    # 임신 + 태아 등록
    async def create_pregnancy(self, user_id: int, pregnancy: PregnancyCreateDTO) -> dict:

        # 1. 규칙 검사 (필드 하나씩 보는 검사는 DTO가, 필드끼리 비교하는 검사는 여기서)
        if pregnancy.pregnancy_previous_birth > pregnancy.pregnancy_previous_pregnancy:
            raise HTTPException(
                status_code=400,
                detail="이전 출산 횟수는 이전 임신 횟수보다 클 수 없습니다.",
            )

        # 2. 진행 중인 임신이 이미 있으면 중복 등록 방지
        #    (여러 개를 허용하려면 이 블록을 지우면 된다)
        in_progress_count = await self.repo.count_pregnancies_by_user_and_status(
            user_id, PregnancyStatus.PREBIRTH.value
        )
        if in_progress_count > 0:
            raise HTTPException(
                status_code=409,
                detail="이미 진행 중인 임신 정보가 있습니다.",
            )

        # 3. 서버가 채우는 값 만들기 (user_id는 토큰에서, 코드는 자동 생성, 상태는 임신 중)
        pregnancy_code = await self._generate_unique_code()

        # 4. DTO -> repository가 받는 dict로 변환
        #    fetuses는 pregnancies 테이블의 컬럼이 아니므로 제외하고, 태아는 따로 넘긴다.
        pregnancy_values = pregnancy.model_dump(exclude={"fetuses"})
        pregnancy_values["user_id"] = user_id
        pregnancy_values["pregnancy_code"] = pregnancy_code
        pregnancy_values["pregnancy_status"] = PregnancyStatus.PREBIRTH.value

        fetus_values_list = [
            {
                "fetus_name": fetus.fetus_name,
                "fetus_gender": fetus.fetus_gender.value,  # enum -> 문자열
            }
            for fetus in pregnancy.fetuses
        ]

        # 5. 저장 (임신 + 태아를 한 트랜잭션으로) 후 결과 반환
        pregnancy_id = await self.repo.create_pregnancy_with_fetuses(
            pregnancy_values, fetus_values_list
        )

        return {"id": pregnancy_id, "pregnancy_code": pregnancy_code}


# 주입 함수: FastAPI가 repository를 만들어서 service에 끼워 줌
def get_pregnancy_service(repo: PregnancyRepository = Depends(get_pregnancy_repository)):
    return PregnancyService(repo)
