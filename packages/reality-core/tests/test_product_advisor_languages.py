from reality.services.product_advisor import detect_question_language


def test_detects_representative_question_languages() -> None:
    assert detect_question_language("Wie funktioniert eine Teillieferung?") == "de"
    assert detect_question_language("¿Cómo funciona una factura?") == "es"
    assert detect_question_language("Comment fonctionne une facture ?") == "fr"
    assert detect_question_language("Jak działa faktura?") == "pl"
    assert detect_question_language("Sipariş ve fatura nasıl çalışır?") == "tr"
    assert detect_question_language("كيف تعمل الفاتورة؟") == "ar"
    assert detect_question_language("請求書はどのように処理されますか？") == "ja"


def test_short_follow_up_uses_history_then_surface_language() -> None:
    history = (
        {"role": "user", "content": "Wie funktioniert eine Teillieferung?"},
        {"role": "assistant", "content": "Die Restmenge bleibt offen."},
    )

    assert detect_question_language("Und später?", history=history) == "de"
    assert detect_question_language("H02?", surface_language="nl") == "nl"
