"""Conversation — sistema de agentes (Sprint 9, Hito 5). Funciones puras, sin IA ni DB."""

from core.conversation.domain.personas import (
    PERSONAS,
    personas_for_context,
    system_prompt_for,
)


def test_personas_for_context_returns_the_right_specialist():
    result = personas_for_context("rutas")
    assert [p.persona_id for p in result] == ["dany"]


def test_personas_for_context_negocio_returns_the_full_board():
    result = personas_for_context("negocio")
    assert {p.persona_id for p in result} == {"tommy", "gabby", "ivan", "marcus"}


def test_personas_for_context_unknown_context_falls_back_to_angela():
    result = personas_for_context("algo_que_no_existe")
    assert [p.persona_id for p in result] == ["angela"]


def test_personas_for_context_never_returns_empty():
    for context in ["resumen", "rutas", "documentos", "presupuesto", "planificacion",
                     "tramites", "traslado", "empleo", "comunidad", "mercado", "negocio", ""]:
        assert len(personas_for_context(context)) > 0


def test_every_persona_has_a_unique_id_matching_its_dict_key():
    for key, persona in PERSONAS.items():
        assert persona.persona_id == key


def test_system_prompt_includes_name_profession_and_personality():
    angela = PERSONAS["angela"]
    prompt = system_prompt_for(angela)
    assert "Angela" in prompt
    assert angela.profession in prompt
    assert angela.personality in prompt


def test_system_prompt_discloses_ai_identity():
    prompt = system_prompt_for(PERSONAS["dany"])
    assert "IA" in prompt or "inteligencia artificial" in prompt.lower()


def test_system_prompt_forbids_argentine_voseo_and_never_uses_it_itself():
    for persona in PERSONAS.values():
        prompt = system_prompt_for(persona)
        assert "vos" not in prompt.split("voseo")[0].lower().replace("nosotros", "")
        for voseo_form in (" tenés", " podés", " sos ", "llamás", "hablá "):
            assert voseo_form not in prompt.lower(), f"{persona.persona_id}: voseo leak -> {voseo_form!r}"
