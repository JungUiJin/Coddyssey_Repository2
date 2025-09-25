#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KBS 헤드라인 수집기 (reworked)
- 공개 XHR(JSON) 엔드포인트만 사용
- 인터페이스는 유지, 내부구현은 전면 재구성

사용 예:
    python crawling_KBS.py --date 20250925 --rows 20 --bonus --debug
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup  # --bonus(KOSPI) 전용

# =========================
# 상수/기본값
# =========================
BASE_URL = "https://news.kbs.co.kr"
XHR_PATH = "/api/getNewsList"
REQ_TIMEOUT = 15  # seconds

# 서버가 쓰는 파라미터의 고정값
DEFAULT_EXCEPT_PHOTO = "Y"
DEFAULT_CONTENTS_CODE = "ALL"
DEFAULT_LOCAL_CODE = "00"

# CLI 기본값
CLI_DEFAULT_DATE = "20250925"  # YYYYMMDD
CLI_DEFAULT_PAGE = 1
CLI_DEFAULT_ROWS = 12

NAVER_KOSPI = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "ko,ko-KR;q=0.9,en;q=0.8",
    "Connection": "close",
}


# =========================
# 로깅
# =========================
log = logging.getLogger("kbs_headlines")


def init_logger(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    log.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%H:%M:%S"))
    log.setLevel(level)
    handler.setLevel(level)
    log.addHandler(handler)


# =========================
# 유틸
# =========================
def squish(text: str) -> str:
    """연속 공백을 1칸으로 정리하고 앞뒤 공백 제거."""
    t = (text or "").replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", t)


def coalesce(d: Mapping[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    """여러 키 후보 중 먼저 존재하는 값을 반환."""
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def abs_url(u: str) -> str:
    """
    URL 보정:
        - 숫자만 오면 /news/view.do?ncd= 로 변환
      - // 로 시작 → https: 접두
        - / 로 시작 → 도메인 결합
        - 그 외 → 원문 유지
    """
    s = (u or "").strip()
    if not s:
        return ""
    if s.isdigit():
        return urljoin(BASE_URL, f"/news/view.do?ncd={s}")
    if s.startswith("//"):
        return "https:" + s
    if s.startswith("/"):
        return urljoin(BASE_URL, s)
    return s


# =========================
# 데이터 모델
# =========================
@dataclass
class Headline:
    title: str
    image_src: str
    date: str
    link: str

    def __str__(self) -> str:
        return (
            f"[제목] {self.title}\n"
            f"  - 이미지: {self.image_src}\n"
            f"  - 날짜  : {self.date}\n"
            f"  - 링크  : {self.link}"
        )


# =========================
# XHR 호출 & 파싱
# =========================
def make_xhr_url(date_yyyymmdd: str, page: int, rows: int) -> str:
    begin, end = f"{date_yyyymmdd}000000", f"{date_yyyymmdd}235959"
    q = {
        "currentPageNo": page,
        "rowsPerPage": rows,
        "exceptPhotoYn": DEFAULT_EXCEPT_PHOTO,
        "datetimeBegin": begin,
        "datetimeEnd": end,
        "contentsCode": DEFAULT_CONTENTS_CODE,
        "localCode": DEFAULT_LOCAL_CODE,
    }
    url = f"{BASE_URL}{XHR_PATH}?{urlencode(q)}"
    log.debug("[make_xhr_url] %s", url)
    return url


def request_json(url: str) -> Any:
    log.debug("[request_json] GET %s", url)
    with requests.Session() as sess:
        resp = sess.get(url, headers=HTTP_HEADERS, timeout=REQ_TIMEOUT)
    log.debug(
        "[request_json] status=%s, len=%s, content-type=%s",
        resp.status_code,
        len(resp.content),
        resp.headers.get("Content-Type"),
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception as e:
        log.error("[request_json] JSON 디코드 실패: %s", e)
        raise


def _find_list_candidates(data: Any) -> Sequence[dict]:
    """
    다양한 JSON 스키마에 대응.
    - 우선순위: dict 특정 키들 → dict 내부 값의 list → 최상위 list
    - 리스트 안이 dict가 아닐 경우는 제외
    """
    if isinstance(data, dict):
        for key in ("newsList", "items", "list", "data", "result", "rows", "contents", "body"):
            val = data.get(key)
            if isinstance(val, list) and val:
                log.debug('[extract] 목록 키 "%s" 감지 (len=%d)', key, len(val))
                return [x for x in val if isinstance(x, dict)]
        # dict 값들 중 첫 list를 픽업
        for v in data.values():
            if isinstance(v, list) and v:
                log.debug("[extract] dict 값에서 list 감지 (len=%d)", len(v))
                return [x for x in v if isinstance(x, dict)]
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def extract_headlines(data: Any) -> list[Headline]:
    """
    레코드의 키 이름이 바뀌어도 견디도록 후보 키를 분기.
    (원본과 달리, title/img/date/link 각각에 대해 별도 coalesce 처리)
    """
    items = _find_list_candidates(data)
    results: list[Headline] = []

    if not items:
        log.warning("[extract_headlines] 목록을 찾지 못했습니다.")
        return results

    for idx, rec in enumerate(items):
        title = squish(str(coalesce(rec, ("newsTitle", "title", "headline", "subject"), "")))
        img = abs_url(str(coalesce(rec, ("imgUrl", "imageUrl", "thumb", "image"), "")))
        date = squish(str(coalesce(rec, ("deskTime", "date", "publishedAt", "regdt"), "")))
        link = abs_url(str(coalesce(rec, ("newsCode", "link", "url", "path"), "")))

        h = Headline(title=title, image_src=img, date=date, link=link)
        log.info("항목 #%d: %s", idx, asdict(h))
        results.append(h)

    log.debug("[extract_headlines] 총 %d건", len(results))
    return results


# =========================
# 보너스: KOSPI
# =========================
def fetch_kospi() -> str:
    """
    네이버 금융 페이지에서 현재 KOSPI 지수를 추출.
    - 1차: 정규식으로 빠르게 긁기
    - 2차: BeautifulSoup fallback
    """
    log.debug("[fetch_kospi] 요청: %s", NAVER_KOSPI)
    r = requests.get(
        NAVER_KOSPI,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ko,ko-KR;q=0.9,en;q=0.8"},
        timeout=REQ_TIMEOUT,
    )
    r.raise_for_status()

    # 1) 정규식 (id="now_value">숫자)
    m = re.search(r'id=["\']now_value["\']\s*>\s*([0-9,]+(?:\.\d+)?)\s*<', r.text)
    if m:
        return m.group(1)

    # 2) Soup fallback: 다양한 후보 셀렉터 시도
    soup = BeautifulSoup(r.text, "html.parser")
    for css in ("#now_value", ".now_value", ".price", ".num", ".today dd"):
        el = soup.select_one(css)
        if not el:
            continue
        txt = squish(el.get_text(" ", strip=True))
        if re.search(r"[0-9,]+(?:\.\d+)?", txt):
            return txt
    log.warning("[fetch_kospi] 지수 파싱 실패")
    return ""


# =========================
# CLI
# =========================
def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KBS 헤드라인 크롤러 (XHR 전용, reworked)")
    p.add_argument("--date", default=CLI_DEFAULT_DATE, help="YYYYMMDD (기본: 20250925)")
    p.add_argument("--page", type=int, default=CLI_DEFAULT_PAGE, help="페이지 번호 (기본: 1)")
    p.add_argument("--rows", type=int, default=CLI_DEFAULT_ROWS, help="행 수 (기본: 12)")
    p.add_argument("--bonus", action="store_true", help="KOSPI 지수도 함께 출력")
    p.add_argument("--debug", action="store_true", help="DEBUG 로깅")
    return p.parse_args(argv)


def run_once(date_str: str, page: int, rows: int) -> list[Headline]:
    url = make_xhr_url(date_str, page, rows)
    data = request_json(url)
    return extract_headlines(data)


def main() -> None:
    args = parse_args()
    # 기본은 INFO, --debug 시 DEBUG
    init_logger(args.debug)

    log.info("[main] date=%s page=%s rows=%s", args.date, args.page, args.rows)

    try:
        headlines = run_once(args.date, args.page, args.rows)
    except Exception:
        log.exception("[main] 수집 실패")
        headlines = []

    print(f"KBS 헤드라인 목록 (XHR, date={args.date}, page={args.page}):")
    for i, h in enumerate(headlines, 1):
        print(f"{i:02d}. {h}")

    try:
        kospi = fetch_kospi()
        print("보너스) 현재 KOSPI 지수:", kospi or "(파싱 실패)")
    except Exception:
        log.exception("[main] KOSPI 수집 실패")


if __name__ == "__main__":
    main()
