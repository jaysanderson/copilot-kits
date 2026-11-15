"""
Locked ElevenLabs voice cast for the call-analysis corpus (Meridian Health
Plan, fictional US health insurer). One voice per named agent (5 recurring
characters, locked - each appears in 4-5 of the 24 calls) and one voice per
member/caller (24 one-off callers - not recurring, per memberId, but still
cast distinctly by gender/age from the dialogue so within a call the two
speakers are always clearly two different people, and no member ever shares
a voice with any agent).

Agent voices are also registered in brand/voices.json under "ca-<firstname>"
keys (the locked-recurring-character pattern already used by the ci-demo
corpus) since they recur; the 24 member castings live only here since they
never recur elsewhere.

All voice_ids below are ElevenLabs shared-library American voices, picked
2026-09-18 via GET /v1/shared-voices?accent=american for gender/age fit
against each character's dialogue. eleven_turbo_v2_5 is used for rendering
(cheap/fast, ample quality for a demo corpus - no multilingual need here).
"""

AGENT_VOICES = {
    "Maria Gonzales": {
        "voice_id": "h2OBoQqre8SPfGehinER",
        "name": "Melanie - Conversational, Trustworthy",
        "registry_key": "ca-maria",
    },
    "Darnell Price": {
        "voice_id": "gZgeCxzVQJzACoAiZkVF",
        "name": "Oliver - Warm & Conversational",
        "registry_key": "ca-darnell",
    },
    "Priya Nair": {
        "voice_id": "0KvU03FZJTjhzbcaS2vc",
        "name": "Mayuri - Calm, Educational & Friendly",
        "registry_key": "ca-priya",
    },
    "Tom Whitfield": {
        "voice_id": "CwHAQ8PNhNqs7NaSW2ST",
        "name": "Robert - calm, informative",
        "registry_key": "ca-tom",
    },
    "Sofia Marchetti": {
        "voice_id": "lAaEXiMr0SpoeuXVOpl6",
        "name": "Stacy - Warm Conversational Narrator",
        "registry_key": "ca-sofia",
    },
}

# Keyed by memberId (unique per call - see scripts_py/scenarios.py). Each
# entry is one-off (members never recur across calls in this corpus), but
# still individually cast for gender/age fit and to guarantee no collision
# with that call's own agent voice.
MEMBER_VOICES = {
    "IFP-558201": {"name": "Robert Carlisle", "voice_id": "DIb5otVtEmkHvXfhjUAF", "voice_name": "Jeff"},
    "MA-770914": {"name": "Eleanor Whitfield", "voice_id": "8fwYhwfiWkLjR4FKLHSQ", "voice_name": "Elise Hart"},
    "EG-330145": {"name": "Jason Toomey", "voice_id": "tcW4NjMUkjoAjqX53ftU", "voice_name": "Samuel Tyler"},
    "IFP-204417": {"name": "Angela Reyes", "voice_id": "u91OxrFDaRINovYRRue2", "voice_name": "Diane"},
    "EG-661238": {"name": "Marcus Lee", "voice_id": "ha8Ha8N5d3VxsYOP2bzo", "voice_name": "Che"},
    "MA-559070": {"name": "Helen Park", "voice_id": "oCPWCqvWZNZ2Enj4auIw", "voice_name": "Cathy"},
    "IFP-119922": {"name": "Greg Sandoval", "voice_id": "rHEkjR83FMA1FlCJ9R4A", "voice_name": "Humberto Garay"},
    "MCD-880145": {"name": "Tanya Brooks", "voice_id": "ZnitN0ogILq2hQcwdNYN", "voice_name": "Shakiera"},
    "EG-447781": {"name": "David Okonkwo", "voice_id": "JDEKaa0qIJDQxqEQ49DG", "voice_name": "Didier"},
    "IFP-665012": {"name": "Nadia Hassan", "voice_id": "DhBr1pmEn3dpypIu7P5H", "voice_name": "Kim"},
    "IFP-773300": {"name": "Brian Foster", "voice_id": "LVe69ZQIfJzglR4mbHPa", "voice_name": "Johnny"},
    "MA-220198": {"name": "Walter Briggs", "voice_id": "kTPvNEwuWEZMKvOhvWEi", "voice_name": "Phillip Lerdahl"},
    "EG-905512": {"name": "Carmen Diaz", "voice_id": "Nnxlhkwt7L1cYF8crHSV", "voice_name": "Sri"},
    "MCD-330871": {"name": "Dorothy Vance", "voice_id": "xIzR6egd3S3LJZbVW0c1", "voice_name": "Nana Margaret"},
    "IFP-556677": {"name": "Priya Raman", "voice_id": "XuJvYV8ALV1PJ1Xxafp9", "voice_name": "Evelyn"},
    "MA-668120": {"name": "Frank Mueller", "voice_id": "dIa7afHH94O36L8tjJ0L", "voice_name": "Dejuan"},
    "DV-114520": {"name": "Kevin Tran", "voice_id": "z5CqQQP5BEAJODKuNgsn", "voice_name": "Leo"},
    "IFP-889431": {"name": "Olivia Bennett", "voice_id": "20MWQ6ZbJgxGQBcAoxVk", "voice_name": "KC"},
    "IFP-330960": {"name": "Rachel Kim", "voice_id": "ru04Mt8xGdftsWAuVUPq", "voice_name": "Amanda"},
    "MA-447712": {"name": "Gloria Hayes", "voice_id": "pELYl0F9HFykExYZefks", "voice_name": "Angela"},
    "EG-770345": {"name": "Samuel Adeyemi", "voice_id": "xhl7YnYr7oJP8I57z5cS", "voice_name": "Arthur"},
    "SUP-220114": {"name": "James Whitaker", "voice_id": "J8YceriT0MhktUAUsxgm", "voice_name": "Dr. Christian Frazier"},
    "EG-558840": {"name": "Marcus Bell", "voice_id": "5tVfZyOAdyKxosgzS7nu", "voice_name": "Buster"},
    "MA-119087": {"name": "Arthur Greene", "voice_id": "yJYX0af9YgTf8sOP8vbP", "voice_name": "Gerard"},
}

ELEVEN_MODEL = "eleven_turbo_v2_5"


def voice_for_turn(agent_name: str, member_id: str, speaker: str) -> str:
    """Return the ElevenLabs voice_id for one dialogue turn."""
    if speaker == "Agent":
        return AGENT_VOICES[agent_name]["voice_id"]
    return MEMBER_VOICES[member_id]["voice_id"]
