"""병원 목록 API의 공개 조회와 Enum 검증, VO 변환을 검사합니다. DB는 변경하지 않습니다."""
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.map_api import router
from app.enum.hospital_enum import HospitalTypeEnum
from app.service.hospital_service import HospitalService, get_hospital_service


class MapApiTests(unittest.TestCase):
    def setUp(self):
        self.repo = SimpleNamespace(get_hospitals=AsyncMock(return_value=[SimpleNamespace(
            id=1, hospital_latitude=Decimal("37.4925498"), hospital_longitude=Decimal("127.0465275"),
            hospital_type=HospitalTypeEnum.CLINIC, hospital_name="조회 검사용 기관",
            hospital_address="검사용 주소", hospital_phone="", hospital_night_service=False,
        )]))
        self.app = FastAPI()
        self.app.include_router(router, prefix="/maps")
        self.app.dependency_overrides[get_hospital_service] = lambda: HospitalService(self.repo)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_public_list_keeps_decimal_coordinate_precision(self):
        response = self.client.get("/maps/hospitals")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"][0]["hospital_latitude"], 37.4925498)
        self.assertEqual(body["data"][0]["hospital_type"], "의원")
        self.assertNotIn("hospital_registration_file_key", body["data"][0])
        self.repo.get_hospitals.assert_awaited_once_with(None)

    def test_type_filter_reaches_repository(self):
        response = self.client.get("/maps/hospitals?hospital_type=종합병원")
        self.assertEqual(response.status_code, 200)
        self.repo.get_hospitals.assert_awaited_once_with(HospitalTypeEnum.GENERAL_HOSPITAL)

    def test_unknown_type_returns_422_without_database_call(self):
        response = self.client.get("/maps/hospitals?hospital_type=INVALID")
        self.assertEqual(response.status_code, 422)
        self.repo.get_hospitals.assert_not_awaited()

    def test_every_original_kind_can_be_serialized(self):
        for kind in HospitalTypeEnum:
            with self.subTest(kind=kind):
                self.repo.get_hospitals.return_value[0].hospital_type = kind
                response = self.client.get("/maps/hospitals")
                self.assertEqual(response.json()["data"][0]["hospital_type"], kind.value)

    def test_old_service_categories_are_rejected(self):
        for old in ("OBSTETRICS", "EMERGENCYROOM"):
            self.assertEqual(self.client.get("/maps/hospitals", params={"hospital_type":old}).status_code,422)

    def test_empty_list_is_successful(self):
        self.repo.get_hospitals.return_value = []
        self.assertEqual(self.client.get("/maps/hospitals").json()["data"], [])


if __name__ == "__main__":
    unittest.main()
