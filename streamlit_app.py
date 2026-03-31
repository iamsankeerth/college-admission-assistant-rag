from __future__ import annotations

from typing import Any

import streamlit as st


EXAMS = [
    "JEE Advanced",
    "JEE Main",
    "BITSAT",
    "VITEEE",
    "WBJEE",
    "TNEA",
]

DEFAULT_BRANCHES = [
    "Computer Science and Engineering",
    "Electronics and Communication Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
]

DEFAULT_STATES = [
    "Delhi",
    "Karnataka",
    "Maharashtra",
    "Tamil Nadu",
    "Telangana",
    "West Bengal",
]

DEFAULT_ZONES = ["North", "South", "East", "West"]


def _get_recommendation_backend() -> tuple[Any | None, Any | None, Any | None, str | None]:
    try:
        from app.models import RecommendationRequest
        from app.recommendation.service import RecommendationService, build_preference_guide

        return RecommendationService(), RecommendationRequest, build_preference_guide(), None
    except Exception as exc:  # pragma: no cover
        return None, None, None, str(exc)


def _normalize_items(response: Any) -> list[dict[str, Any]]:
    if response is None:
        return []
    items = getattr(response, "recommendations", response)
    normalized: list[dict[str, Any]] = []
    for item in items or []:
        if hasattr(item, "model_dump"):
            normalized.append(item.model_dump())
        elif isinstance(item, dict):
            normalized.append(item)
    return normalized


def _render_preference_guide(guide: Any) -> None:
    with st.expander("Student Preference Configuration Guide", expanded=False):
        if hasattr(guide, "overview"):
            st.write(guide.overview)
        if hasattr(guide, "fields"):
            st.markdown("**How to configure your profile**")
            for field in guide.fields:
                st.write(f"- `{field.field}`: {field.description}")
        if hasattr(guide, "tips") and guide.tips:
            st.markdown("**Tips**")
            for tip in guide.tips:
                st.write(f"- {tip}")


def _render_recommendation_card(item: dict[str, Any], rank: int) -> None:
    title = item.get("college_name", f"Recommendation {rank}")
    score = float(item.get("score", 0.0))
    location = ", ".join(part for part in [item.get("city"), item.get("state")] if part)
    reasons = item.get("reasons", [])
    rag_evidence = item.get("rag_evidence") or {}
    citations = rag_evidence.get("citations", [])

    with st.container(border=True):
        cols = st.columns([5, 2])
        with cols[0]:
            st.subheader(f"{rank}. {title}")
            if location:
                st.caption(location)
        with cols[1]:
            st.metric("Match Score", f"{score:.2f}")

        badges = [
            f"Fit: {item.get('fit_bucket', 'target').title()}",
            f"Branch: {item.get('matched_branch', 'General')}",
            f"Annual cost: {float(item.get('annual_cost_lakh', 0.0)):.2f} lakh",
            "Hostel: Yes" if item.get("hostel_available") else "Hostel: No/Unknown",
        ]
        st.write(" | ".join(badges))

        if reasons:
            st.markdown("**Why it matches you**")
            for reason in reasons:
                st.write(f"- {reason}")

        if rag_evidence.get("summary"):
            st.markdown("**Official evidence snapshot**")
            st.write(rag_evidence["summary"])

        if citations:
            with st.expander("Official citations"):
                for citation in citations:
                    st.markdown(f"- **{citation.get('title', citation.get('chunk_id', 'Evidence'))}**")
                    if citation.get("url"):
                        st.write(citation["url"])
                    if citation.get("supporting_text"):
                        st.caption(citation["supporting_text"])


def main() -> None:
    st.set_page_config(page_title="College Admission Assistance Agent", page_icon="🎓", layout="wide")
    st.title("College Admission Assistance Agent")
    st.caption("Python + RAG + Streamlit recommendation demo for Indian college shortlisting.")

    backend, request_model, guide, error = _get_recommendation_backend()
    if error:
        st.error("The recommendation backend could not be loaded.")
        st.caption(error)
        return

    _render_preference_guide(guide)

    with st.sidebar:
        st.header("Student Preferences")
        exam = st.selectbox("Entrance exam", EXAMS, index=0)
        rank = st.number_input("Rank", min_value=1, max_value=500000, value=8500, step=100)
        budget = st.slider("Max annual budget (lakh INR)", min_value=1.0, max_value=15.0, value=5.0)
        branches = st.multiselect(
            "Preferred branches",
            DEFAULT_BRANCHES,
            default=["Computer Science and Engineering", "Electrical Engineering"],
        )
        states = st.multiselect("Preferred states", DEFAULT_STATES, default=["Telangana", "Tamil Nadu"])
        zones = st.multiselect("Preferred zones", DEFAULT_ZONES, default=["South"])
        cities_raw = st.text_input("Preferred cities (comma separated)", "Hyderabad, Chennai")
        hostel_required = st.checkbox("Hostel preference matters", value=True)
        max_results = st.slider("Number of recommendations", min_value=3, max_value=10, value=5)
        include_rag_summary = st.checkbox("Include official RAG summary", value=True)
        submitted = st.button("Find Best-Fit Colleges", type="primary")

    if not submitted:
        st.info("Choose your preferences in the sidebar, then click **Find Best-Fit Colleges**.")
        return

    preferred_cities = [city.strip() for city in cities_raw.split(",") if city.strip()]
    request = request_model(
        entrance_exam=exam,
        rank=int(rank),
        preferred_branches=branches,
        budget_lakh=float(budget),
        preferred_states=states,
        preferred_cities=preferred_cities,
        preferred_zones=zones,
        hostel_required=hostel_required,
        max_results=max_results,
        include_rag_summary=include_rag_summary,
    )
    response = backend.recommend(request)
    items = _normalize_items(response)

    st.success(f"Generated {len(items)} ranked college recommendations.")

    summary_cols = st.columns(4)
    summary_cols[0].metric("Exam", exam)
    summary_cols[1].metric("Rank", f"{int(rank):,}")
    summary_cols[2].metric("Budget", f"{float(budget):.1f} lakh")
    summary_cols[3].metric("Hostel Priority", "Yes" if hostel_required else "No")

    with st.expander("Preference Summary", expanded=False):
        st.json(request.model_dump())

    if not items:
        st.warning("No colleges matched the current filters. Try widening the rank or budget range.")
        return

    st.subheader("Ranked Recommendations")
    for idx, item in enumerate(items, start=1):
        _render_recommendation_card(item, idx)

    if getattr(response, "notes", None):
        st.markdown("### Recommendation Notes")
        for note in response.notes:
            st.write(f"- {note}")


if __name__ == "__main__":
    main()
