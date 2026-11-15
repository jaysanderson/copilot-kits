"""Closed-vocabulary feedback codes for the document-triage verdict.

8 Aug 2026 revision: remapped to the EXACT 24 codes from the target PRD
("AI Agent for Document Review at the Degree Equivalency Application
Submission Stage", section 10) - these are no longer this build's own
invented vocabulary. Every code has a full translation in all five
supported languages (HE, RU, EN, UK, FR) per the PRD's closing instruction
on section 10.

`implemented` is honest metadata, not part of the PRD spec: True means this
build's pipeline actively detects and can emit that code from a real check;
False means the code is catalogued (translated, ready) but the underlying
detection isn't built yet - most of these need a capability this build
doesn't have (first/last name splitting across scripts, institution-name
extraction and cross-document comparison). See README "Known gaps" for the
reasoning on each - never emitted, never faked.
"""

SEVERITY_INFO = "INFO"
SEVERITY_ATTENTION = "ATTENTION"
SEVERITY_REVIEW = "REVIEW"

FULL_LANGS = ("he", "ru", "en", "uk", "fr")
PARTIAL_LANGS = ()
ALL_LANGS = FULL_LANGS + PARTIAL_LANGS

# code -> {severity, implemented, text: {lang: str}}
CATALOGUE = {
    "DOC_MISSING_DIPLOMA": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "A diploma / degree certificate is missing.",
            "he": "חסרה תעודת תואר / דיפלומה.",
            "ru": "Отсутствует диплом / документ о высшем образовании.",
            "uk": "Відсутній диплом / документ про вищу освіту.",
            "fr": "Un diplôme est manquant.",
        },
    },
    "DOC_MISSING_TRANSCRIPT": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "A transcript is missing.",
            "he": "חסר גיליון ציונים.",
            "ru": "Отсутствует академическая справка (выписка оценок).",
            "uk": "Відсутня академічна довідка (виписка оцінок).",
            "fr": "Un relevé de notes est manquant.",
        },
    },
    "DOC_MISSING_NAME_CHANGE": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "A mismatch was found in the first name or last name between the submitted documents. A name change certificate must be attached.",
            "he": "נמצאה אי-התאמה בשם הפרטי או שם המשפחה בין המסמכים שהוגשו. יש לצרף תעודת שינוי שם.",
            "ru": "Обнаружено несоответствие имени или фамилии между поданными документами. Необходимо приложить свидетельство о смене имени.",
            "uk": "Виявлено невідповідність імені або прізвища між поданими документами. Необхідно додати свідоцтво про зміну імені.",
            "fr": "Une incohérence a été détectée dans le prénom ou le nom de famille entre les documents soumis. Un certificat de changement de nom doit être joint.",
        },
    },
    "DOC_UNREADABLE": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The document is unclear or not sufficiently legible. It is recommended to upload a higher-quality scan.",
            "he": "המסמך אינו ברור או אינו קריא מספיק. מומלץ להעלות סריקה באיכות גבוהה יותר.",
            "ru": "Документ нечёткий или недостаточно разборчив. Рекомендуется загрузить скан более высокого качества.",
            "uk": "Документ нечіткий або недостатньо розбірливий. Рекомендується завантажити скан вищої якості.",
            "fr": "Le document n'est pas clair ou pas suffisamment lisible. Il est recommandé de télécharger un scan de meilleure qualité.",
        },
    },
    "DOC_ROTATED": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The document is rotated or is not displayed in the correct orientation.",
            "he": "המסמך מסובב או אינו מוצג בכיוון הנכון.",
            "ru": "Документ повёрнут или отображается в неправильной ориентации.",
            "uk": "Документ повернутий або відображається в неправильній орієнтації.",
            "fr": "Le document est pivoté ou ne s'affiche pas dans la bonne orientation.",
        },
    },
    "DOC_DARK_OR_LOW_QUALITY": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The document quality is low or the image is too dark.",
            "he": "איכות המסמך נמוכה או שהתמונה כהה מדי.",
            "ru": "Качество документа низкое, или изображение слишком тёмное.",
            "uk": "Якість документа низька, або зображення занадто темне.",
            "fr": "La qualité du document est faible ou l'image est trop sombre.",
        },
    },
    "DOC_UNKNOWN_TYPE": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "We were unable to identify the document type.",
            "he": "לא הצלחנו לזהות את סוג המסמך.",
            "ru": "Не удалось определить тип документа.",
            "uk": "Не вдалося визначити тип документа.",
            "fr": "Nous n'avons pas pu identifier le type de document.",
        },
    },
    "DOC_DUPLICATE_TYPE": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "Multiple documents of the same type were uploaded. It is recommended to verify that all relevant documents have been attached.",
            "he": "הועלו מספר מסמכים מאותו הסוג. מומלץ לוודא שכל המסמכים הרלוונטיים צורפו.",
            "ru": "Загружено несколько документов одного типа. Рекомендуется проверить, что все необходимые документы приложены.",
            "uk": "Завантажено кілька документів одного типу. Рекомендується перевірити, що додано всі необхідні документи.",
            "fr": "Plusieurs documents du même type ont été téléchargés. Il est recommandé de vérifier que tous les documents pertinents ont été joints.",
        },
    },
    "DOC_STAMP_MISSING": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "A required stamp was not identified in the document.",
            "he": "לא זוהתה אשרה נדרשת במסמך.",
            "ru": "На документе не обнаружена требуемая печать/отметка.",
            "uk": "На документі не виявлено необхідної печатки/позначки.",
            "fr": "Un cachet requis n'a pas été identifié sur le document.",
        },
    },
    "DOC_STAMP_NOT_CLEAR": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "A stamp was identified, but it is not sufficiently clear.",
            "he": "זוהתה אשרה, אך אינה ברורה מספיק.",
            "ru": "Печать обнаружена, но недостаточно чёткая.",
            "uk": "Печатку виявлено, але вона недостатньо чітка.",
            "fr": "Un cachet a été identifié, mais il n'est pas suffisamment clair.",
        },
    },
    "DOC_FIRST_NAME_MISMATCH": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The first name in the document does not match the first name entered in the application.",
            "he": "השם הפרטי במסמך אינו תואם לשם הפרטי שהוזן בבקשה.",
            "ru": "Имя в документе не совпадает с именем, указанным в заявке.",
            "uk": "Ім'я в документі не збігається з ім'ям, зазначеним у заявці.",
            "fr": "Le prénom figurant sur le document ne correspond pas au prénom saisi dans la demande.",
        },
    },
    "DOC_LAST_NAME_MISMATCH": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The last name in the document does not match the last name entered in the application.",
            "he": "שם המשפחה במסמך אינו תואם לשם המשפחה שהוזן בבקשה.",
            "ru": "Фамилия в документе не совпадает с фамилией, указанной в заявке.",
            "uk": "Прізвище в документі не збігається з прізвищем, зазначеним у заявці.",
            "fr": "Le nom de famille figurant sur le document ne correspond pas au nom de famille saisi dans la demande.",
        },
    },
    "DOC_INSTITUTION_NOT_CLEAR": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The name of the educational institution is unclear in the document.",
            "he": "שם המוסד הלימודי אינו ברור במסמך.",
            "ru": "Название учебного заведения в документе неразборчиво.",
            "uk": "Назва навчального закладу в документі нерозбірлива.",
            "fr": "Le nom de l'établissement d'enseignement n'est pas clair sur le document.",
        },
    },
    "DOC_DEGREE_NOT_CLEAR": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The degree name or degree type is unclear in the document.",
            "he": "שם התואר או סוג התואר אינו ברור במסמך.",
            "ru": "Название или тип степени в документе неразборчивы.",
            "uk": "Назва або тип ступеня в документі нерозбірливі.",
            "fr": "Le nom ou le type de diplôme n'est pas clair sur le document.",
        },
    },
    "DOC_DATE_NOT_CLEAR": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The document date or study dates are unclear.",
            "he": "תאריך המסמך או תאריכי הלימודים אינם ברורים.",
            "ru": "Дата документа или даты обучения неразборчивы.",
            "uk": "Дата документа або дати навчання нерозбірливі.",
            "fr": "La date du document ou les dates d'études ne sont pas claires.",
        },
    },
    "DOC_LANGUAGE_UNSUPPORTED": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "The document language was not identified or is not fully supported.",
            "he": "שפת המסמך לא זוהתה או אינה נתמכת במלואה.",
            "ru": "Язык документа не определён или поддерживается не полностью.",
            "uk": "Мову документа не визначено або вона підтримується не повністю.",
            "fr": "La langue du document n'a pas été identifiée ou n'est pas entièrement prise en charge.",
        },
    },
    "DOC_FILE_TYPE_NOT_SUPPORTED": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "The file type is not supported. Only PDF, JPG, or PNG files may be uploaded.",
            "he": "סוג הקובץ אינו נתמך. ניתן להעלות רק קבצי PDF, JPG או PNG.",
            "ru": "Тип файла не поддерживается. Можно загружать только файлы PDF, JPG или PNG.",
            "uk": "Тип файлу не підтримується. Можна завантажувати лише файли PDF, JPG або PNG.",
            "fr": "Le type de fichier n'est pas pris en charge. Seuls les fichiers PDF, JPG ou PNG peuvent être téléchargés.",
        },
    },
    "DOC_CAN_SUBMIT_WITH_WARNINGS": {
        "severity": SEVERITY_INFO,
        "implemented": True,
        "text": {
            "en": "You may continue submitting the application, but additional documents may be requested later.",
            "he": "ניתן להמשיך ולהגיש את הבקשה, אך ייתכן שיידרשו מסמכים נוספים בהמשך.",
            "ru": "Вы можете продолжить подачу заявки, однако в дальнейшем могут быть запрошены дополнительные документы.",
            "uk": "Ви можете продовжити подання заявки, проте надалі можуть бути запитані додаткові документи.",
            "fr": "Vous pouvez continuer à soumettre la demande, mais des documents supplémentaires pourront être demandés ultérieurement.",
        },
    },
    "DOC_ALL_VALID": {
        "severity": SEVERITY_INFO,
        "implemented": True,
        "text": {
            "en": "All required documents were identified, and no material issues were found in the preliminary review.",
            "he": "כל המסמכים הנדרשים זוהו, ולא נמצאו בעיות מהותיות בבדיקה המקדימה.",
            "ru": "Все необходимые документы определены, существенных проблем при предварительной проверке не выявлено.",
            "uk": "Усі необхідні документи визначено, суттєвих проблем під час попередньої перевірки не виявлено.",
            "fr": "Tous les documents requis ont été identifiés et aucun problème significatif n'a été détecté lors de l'examen préliminaire.",
        },
    },
    "DOC_MISSING_NAME_CHANGE_CERTIFICATE": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "A name change certificate is missing.",
            "he": "חסרה תעודת שינוי שם.",
            "ru": "Отсутствует свидетельство о смене имени.",
            "uk": "Відсутнє свідоцтво про зміну імені.",
            "fr": "Un certificat de changement de nom est manquant.",
        },
    },
    "DOC_MISSING_INSTITUTION_NAME_APPRO": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "An institution name certificate or supporting evidence identifying the educational institution is missing.",
            "he": "חסרה תעודת שם מוסד או אסמכתא התומכת בזיהוי המוסד הלימודי.",
            "ru": "Отсутствует свидетельство о названии учебного заведения или подтверждающий документ, устанавливающий его название.",
            "uk": "Відсутнє свідоцтво про назву навчального закладу або підтвердний документ, що встановлює його назву.",
            "fr": "Un certificat de dénomination de l'établissement ou une pièce justificative identifiant l'établissement d'enseignement est manquant.",
        },
    },
    "DOC_NAME_TRANSLATION_MISMATCH": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The name translated from the document into Hebrew does not match the applicant's name.",
            "he": "השם המתורגם מהמסמך לעברית אינו תואם לשם המבקש.",
            "ru": "Имя, переведённое из документа на иврит, не совпадает с именем заявителя.",
            "uk": "Ім'я, перекладене з документа на іврит, не збігається з ім'ям заявника.",
            "fr": "Le nom traduit du document vers l'hébreu ne correspond pas au nom du demandeur.",
        },
    },
    "DOC_INSTITUTION_NAME_MISMATCH": {
        "severity": SEVERITY_ATTENTION,
        "implemented": True,
        "text": {
            "en": "The name of the educational institution in the document does not match or requires additional supporting evidence.",
            "he": "שם המוסד הלימודי במסמך אינו תואם או דורש אסמכתא נוספת.",
            "ru": "Название учебного заведения в документе не совпадает или требует дополнительного подтверждения.",
            "uk": "Назва навчального закладу в документі не збігається або потребує додаткового підтвердження.",
            "fr": "Le nom de l'établissement d'enseignement dans le document ne correspond pas ou nécessite une pièce justificative supplémentaire.",
        },
    },
    "DOC_FILE_SIZE_EXCEEDED": {
        "severity": SEVERITY_REVIEW,
        "implemented": True,
        "text": {
            "en": "The file exceeds the permitted size limit.",
            "he": "הקובץ חורג ממגבלת הגודל המותרת.",
            "ru": "Файл превышает допустимый предел размера.",
            "uk": "Файл перевищує допустиму межу розміру.",
            "fr": "Le fichier dépasse la taille maximale autorisée.",
        },
    },
}


def message_for(code: str, lang: str) -> dict:
    entry = CATALOGUE.get(code)
    if not entry:
        return {"code": code, "severity": SEVERITY_REVIEW, "text": code}
    text = entry["text"].get(lang) or entry["text"].get("en")
    return {"code": code, "severity": entry["severity"], "text": text}


def coverage_report() -> dict:
    report = {}
    for code, entry in CATALOGUE.items():
        report[code] = {
            "severity": entry["severity"],
            "implemented": entry["implemented"],
            "languages": sorted(entry["text"].keys()),
        }
    return report
