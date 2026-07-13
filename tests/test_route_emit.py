"""Tests for the document-routing UserPromptSubmit hook (route_emit.py).

핵심 계약: 문서 작업이면 매 턴 FORMAT+STAGE 판정을 응답 맨 앞(omha ROUTE 줄
다음)에 출력하라는 contract 를 주입한다. omha 의 ROUTE(LANE)·oms 의 STAGE(paper)
와 레이블이 구분되고, 수식은 카드 VERIFIED 경로만이라는 단서가 박혀야 한다.
stdlib only, fail-open.

isomorphic 출처: oh-my-scholar/tests/test_scholar_route_emit.py (도메인만 docs).
OMD 는 tests/ 가 없었으므로 hook 계약 회귀를 위해 신설(T14)."""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "route_emit.py"


def run_hook(payload: dict) -> str:
    """훅을 서브프로세스로 실행하고 stdout 반환."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def context_of(stdout: str) -> str:
    if not stdout.strip():
        return ""
    return json.loads(stdout)["hookSpecificOutput"]["additionalContext"]


def test_emits_userpromptsubmit_context():
    """① UserPromptSubmit 이벤트로 라우팅 contract 주입."""
    out = run_hook({"prompt": "이 PDF로 디펜스 발표자료 만들어줘"})
    d = json.loads(out)
    assert d["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_context_states_stage_emit_contract():
    """② 매 턴 FORMAT+STAGE 한 줄 판정 contract 가 명시돼야 (omha ROUTE 와 동형)."""
    out = context_of(run_hook({"prompt": "이 슬라이드 검토해줘"}))
    assert "STAGE(docs) →" in out
    assert "누락 금지" in out  # 매 턴 출력 의무


def test_context_lists_all_stages():
    """③ 9개 단계가 contract 에 모두 열거돼야 (skill 과 정합).

    revise 는 docs-revise 스킬이 실재하므로 STAGE 카탈로그에 포함돼야 한다
    (T14 에서 누락을 수정). pilot 은 docs-pilot 로 표기.
    learn 은 docs-learn 스킬(관찰→style-spec 기본값 승격, 사람 게이트)이
    실재하므로 메타 단계로 포함돼야 한다 (H9 에서 추가)."""
    out = context_of(run_hook({"prompt": "문서 작업"}))
    for stage in ("intake", "standardize", "plan", "build",
                  "inspect", "verify", "revise", "learn", "docs-pilot"):
        assert stage in out, f"stage '{stage}' missing from contract"


def test_learn_stage_in_routing_token_line():
    """③-b learn 메타 단계가 STAGE 토큰 줄에 명시돼야 (H9)."""
    out = context_of(run_hook({"prompt": "이 양식 기본값으로 굳혀줘"}))
    assert "learn" in out
    assert "사람 게이트" in out  # 자동 발동 아님


def test_learn_routing_keeps_content_guard():
    """③-c learn 추가가 content-preservation 가드를 깨지 않아야 (H9·§6.F)."""
    out = context_of(run_hook({"prompt": "promote default"}))
    # content 는 learn 승격 대상이 아님(form 만)이 라우팅에 박혀야
    assert "content 는 승격 대상 아님" in out or "form 만" in out


def test_context_lists_formats():
    """④ 여섯 포맷(pptx/docx/xlsx/hwpx/repo-docs/site)이 STAGE 토큰 줄에 열거돼야 — 어디서든
    등장이 아니라 FORMAT 슬롯인 STAGE(docs) 줄 자체에 박혀야 한다.

    xlsx 는 references/formats/xlsx.md 카드(openpyxl/xlsxwriter 라우팅, <v>0</v> 함정,
    구조검증 게이트)가 실재하므로 포맷 목록에 포함돼야 한다 (2026-05-31 신설)."""
    out = context_of(run_hook({"prompt": "발표자료"}))
    stage_lines = [l for l in out.splitlines() if l.startswith("STAGE(docs)")]
    assert stage_lines, "STAGE token line must exist"
    for fmt in ("pptx", "docx", "xlsx", "hwpx", "repo-docs", "site"):
        assert fmt in stage_lines[0], f"format '{fmt}' missing from STAGE token line"


def test_context_states_format_card_authority():
    """⑤ 수식·함정의 단일 진실 = references/formats/<format>.md 카드라는 단서."""
    out = context_of(run_hook({"prompt": "수식 들어간 docx"}))
    assert "references/formats" in out
    assert "VERIFIED" in out  # 수식은 카드가 VERIFIED 표시한 경로만


def test_context_states_consensus_rationale():
    """⑥ Deliberate(디펜스·심사·외부 공식) → docs-plan --consensus 단서가 박혀야 (T14)."""
    out = context_of(run_hook({"prompt": "심사 발표자료"}))
    assert "--consensus" in out
    assert "Deliberate" in out


def test_pdf_is_not_a_generation_format():
    """H5 결정: pdf는 입력·변환 층위 — FORMAT/STAGE 슬롯에 절대 편입 금지."""
    out = context_of(run_hook({"prompt": "이 PDF로 발표자료 만들어줘"}))
    stage_lines = [l for l in out.splitlines() if l.startswith("STAGE(docs)")]
    assert stage_lines, "STAGE token line must exist"
    assert "pdf" not in stage_lines[0]          # STAGE 토큰 줄에 pdf 없음
    assert "입력·변환 층위" in out                 # 층위 표기는 존재


def test_stage_label_distinct_from_paper_and_lane():
    """⑦ omd 레이블(STAGE(docs))이 oms(STAGE(paper))·omha(ROUTE)와 달라
    한 화면에 같이 떠도 구분 가능. 이모지 미사용."""
    out = context_of(run_hook({"prompt": "문서"}))
    assert "STAGE(docs)" in out       # omd 전용 레이블
    assert "STAGE(paper)" not in out  # oms 레이블과 충돌 없음
    assert "ROUTE →" not in out       # omha 레인 레이블과 충돌 없음
    assert "📑" not in out and "📄" not in out and "🧭" not in out


def test_stdlib_only_no_third_party_imports():
    """⑧ stdlib only — 외부 의존 없이 import 성공 가능 (a test enforces this)."""
    src = HOOK.read_text()
    assert "import json" in src and "import sys" in src
    assert "import a2a" not in src and "import requests" not in src


def test_fail_open_on_bad_input():
    """⑨ fail-open: 잘못된 입력에도 exit 0, 세션 안 막음."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all", capture_output=True, text=True,
    )
    assert proc.returncode == 0


def test_context_states_ssot_first_gate():
    """⑩ SSOT-first 필독 게이트: 첫 생성·방향 제시 전 .omd/wiki/ 를 소스/기억보다
    먼저 SSOT 로 읽고, .omd/<slug>/ 존재를 확인해 기존 build 를 재사용하라는
    contract 가 박혀야 한다 (oms 의 SSOT 게이트와 동형).

    Origin: 2026-07-09 multibeam-sonar 세션. 이미 v01~v04 로 진화한 herolab
    템플릿 build 시스템(.omd/<slug>/)과 스타일 규칙(.omd/wiki/)이 전부 있었는데
    담당 세션이 그 어느 것도 읽지 않고 빈 Presentation() 백지에서 새로 만들어
    전면 반려됨. 근본원인 = omd 라우팅에 oms 의 'SSOT 우선 필독' 게이트가 없던
    구조적 갭. wiki note: pattern/read-existing-work-before-building.md."""
    out = context_of(run_hook({"prompt": "이 발표자료 개선해줘"}))
    assert ".omd/wiki/" in out            # wiki 를 SSOT 로 먼저
    assert "먼저" in out                  # 소스/일반론/기억보다 '먼저'
    assert "결함" in out                  # wiki 두고 즉흥 스타일 = 결함 명시
    assert ".omd/<slug>/" in out          # 진행 중 산출물 존재 확인
    assert "재사용" in out                # 기존 build 파이프라인 재사용
    assert "Presentation()" in out        # 빈 백지 금지 (herolab 템플릿 산출물)


def test_ssot_gate_forbids_direction_before_recon():
    """⑩-b 지형 미파악 상태의 방향 제시 금지 — '이렇게 개선하겠다'를
    wiki·slug 확인 전에 내놓지 말라는 규율이 박혀야 (백지 재시작 직결)."""
    out = context_of(run_hook({"prompt": "이 슬라이드 이렇게 바꾸자"}))
    assert "방향 제시" in out
    assert "백지" in out  # 지형 미파악 방향 제시 → 백지 재시작


def test_repo_docs_in_stage_token_line():
    """R2: repo-docs 장르가 FORMAT 슬롯(STAGE 토큰 줄)에 광고돼야 — 카드 실재와 동기."""
    out = context_of(run_hook({"prompt": "README 만들어줘"}))
    stage_lines = [l for l in out.splitlines() if l.startswith("STAGE(docs)")]
    assert stage_lines and "repo-docs" in stage_lines[0]


def test_site_advertised_with_card():
    """R3: site 카드가 실재하므로 FORMAT 슬롯 광고 해제 (R2 pin 의 반전 — 광고는 카드 실존과 동기)."""
    card = Path(__file__).parent.parent / "references" / "formats" / "site.md"
    assert card.is_file(), "advertising requires the card to exist (H1-isomorphic rule)"
    out = context_of(run_hook({"prompt": "문서 사이트 만들어줘"}))
    stage_lines = [l for l in out.splitlines() if l.startswith("STAGE(docs)")]
    assert stage_lines and "site" in stage_lines[0]
