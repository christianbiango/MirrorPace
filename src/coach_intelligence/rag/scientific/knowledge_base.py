"""Built-in scientific knowledge base — entries mapped to KB rules and training concepts."""

SCIENTIFIC_ENTRIES: list[dict] = [
    {
        "id": "acwr_gabbett_2016",
        "tags": ["RULE-003", "RULE-004", "acwr", "charge_aigue", "charge_chronique", "blessure", "risque", "ratio"],
        "source": "Gabbett (2016) — The training-injury prevention paradox",
        "claim": "Un ACWR > 1.5 multiplie par 2 à 4 le risque de blessure.",
        "explanation": (
            "Gabbett (2016) démontre que les pics de charge à court terme par rapport à la charge chronique "
            "constituent le principal prédicteur de blessures en endurance. La zone 'sweet spot' (ACWR 0.8–1.3) "
            "associe progression et protection blessure. Au-delà de 1.5, le risque de blessure double à quadruple."
        ),
    },
    {
        "id": "acwr_hulin_2016",
        "tags": ["RULE-003", "RULE-004", "RULE-005", "acwr", "pic_charge", "monotonie", "charge_chronique"],
        "source": "Hulin et al. (2016) — Spikes in acute workload are associated with increased injury risk",
        "claim": "C'est le ratio charge aiguë/chronique, non la charge absolue, qui prédit le risque de blessure.",
        "explanation": (
            "Hulin et al. montrent qu'un coureur habitué à 70 km/sem supporte mieux un pic à 80 km "
            "qu'un débutant à 40 km/sem. La charge absolue est moins prédictive que la variation relative. "
            "Une charge chronique élevée est protectrice à condition que l'augmentation reste graduelle."
        ),
    },
    {
        "id": "pain_stop_cook_2009",
        "tags": ["RULE-001", "RULE-002", "douleur", "tendon", "tendinopathie", "blessure", "critique", "arrêt", "pathologie"],
        "source": "Cook & Purdam (2009) — Is tendon pathology a continuum?",
        "claim": "Courir avec une douleur tendineuse > 3/10 risque de faire évoluer la lésion vers un stade chronique irréversible.",
        "explanation": (
            "Le modèle continuum de Cook & Purdam distingue la tendinopathie réactive (aiguë, réversible) "
            "du stade dégénératif (chronique). Les charges répétées sur un tendon enflammé accélèrent "
            "la progression vers l'irréversible. L'arrêt précoce est la seule stratégie efficace."
        ),
    },
    {
        "id": "deload_issurin_2010",
        "tags": ["RULE-006", "deload", "recuperation", "supercompensation", "charge", "semaine_recuperation", "surmenage"],
        "source": "Issurin (2010) — Block periodization versus traditional training theory",
        "claim": "Les semaines de décharge permettent la supercompensation et réduisent le risque de surentraînement.",
        "explanation": (
            "Issurin recommande des cycles de 3+1 (3 semaines de charge, 1 semaine de récupération) "
            "pour les coureurs intermédiaires à avancés. Sans phases de récupération planifiées, "
            "les adaptations ne peuvent se consolider et le risque de syndrome de surentraînement augmente."
        ),
    },
    {
        "id": "taper_mujika_2003",
        "tags": ["RULE-007", "RULE-021", "taper", "affûtage", "marathon", "pre_race", "J7", "J14", "course", "performance"],
        "source": "Mujika & Padilla (2003) — Scientific bases for precompetition tapering strategies",
        "claim": "Une réduction de 40–60 % du volume sur 2–3 semaines avant la course optimise la performance de 2–3 %.",
        "explanation": (
            "Mujika & Padilla montrent que l'affûtage correctement dosé — maintien de l'intensité, "
            "réduction du volume — améliore les performances de 2–3 %. Couper trop tôt ou trop brusquement "
            "est contre-productif. La fréquence des séances doit rester identique pendant l'affûtage."
        ),
    },
    {
        "id": "injury_return_warden_2021",
        "tags": ["RULE-008", "RULE-026", "blessure", "reprise", "return_to_run", "progressivité", "interruption", "protocole"],
        "source": "Warden et al. (2021) — Return to running after injury",
        "claim": "La reprise après blessure doit suivre un protocole progressif : marche → marche/course → course continue.",
        "explanation": (
            "Les protocoles de reprise progressifs réduisent les récidives de 40 %. La règle d'or : "
            "si la douleur dépasse 3/10 pendant l'effort, on stoppe et on régresse au stade précédent. "
            "La durée de la phase de reprise dépend de la durée d'interruption (ratio 1:2 minimum)."
        ),
    },
    {
        "id": "beginner_buist_2010",
        "tags": ["RULE-010", "RULE-016", "debutant", "progression", "base", "novice", "10_percent_rule", "surcharge"],
        "source": "Buist et al. (2010) — No effect of a graded training program on the number of running-related injuries",
        "claim": "La règle des 10 % est insuffisante pour les débutants — une progression de 5–7 %/sem est plus adaptée.",
        "explanation": (
            "Buist et al. remettent en question la règle des 10 % pour les coureurs novices. "
            "Une progression plus graduelle avec des semaines de récupération fréquentes protège mieux "
            "les structures tendineuses et osseuses pas encore adaptées à l'impact de la course."
        ),
    },
    {
        "id": "polarized_seiler_2009",
        "tags": ["RULE-009", "RULE-011", "RULE-012", "polarisé", "zone", "intensité", "80_20", "facile", "seuil", "distribution"],
        "source": "Seiler & Tønnessen (2009) — Intervals, thresholds, and long slow distance",
        "claim": "Les coureurs de performance optimisent avec ~80 % d'effort facile et ~20 % d'effort intense.",
        "explanation": (
            "Seiler & Tønnessen montrent que les coureurs d'élite évitent la zone grise (modéré) "
            "et polarisent leur entraînement. Trop de volume à intensité modérée accumule de la fatigue "
            "sans les adaptations neuromusculaires de l'intensité élevée ni les adaptations aérobies du volume lent."
        ),
    },
    {
        "id": "speed_billat_2001",
        "tags": ["RULE-018", "VMA", "VO2max", "vitesse", "cycle_vitesse", "interval", "allure", "performance"],
        "source": "Billat (2001) — Interval training for performance: a scientific and empirical practice",
        "claim": "Les séances à 90–100 % de VMA sont le stimulus optimal pour améliorer la VO2max.",
        "explanation": (
            "Billat démontre que les intervalles courts à haute intensité (30/30, 1000 m répétitions) "
            "sont plus efficaces que le volume modéré pour progresser sur marathon. "
            "L'intégration d'un cycle vitesse est indiquée seulement sur une base aérobie solide (≥ 6 sem)."
        ),
    },
    {
        "id": "macro_plan_bompa_2009",
        "tags": ["RULE-015", "RULE-019", "periodisation", "macrocycle", "planification", "phases", "objectif", "marathon", "structuration"],
        "source": "Bompa & Haff (2009) — Periodization: Theory and Methodology of Training",
        "claim": "La périodisation structure le développement sur 16–24 semaines en phases (base, spécifique, affûtage).",
        "explanation": (
            "Bompa & Haff proposent un modèle en 3 phases pour le marathon : phase de base "
            "(volume élevé, faible intensité), phase spécifique (volume modéré, intensité croissante), "
            "affûtage (volume réduit). Canova adapte ce modèle en insistant sur les séances longues spécifiques."
        ),
    },
    {
        "id": "fatigue_foster_2001",
        "tags": ["RULE-009", "RULE-013", "fatigue", "RPE", "charge_interne", "surmenage", "recuperation", "monotonie"],
        "source": "Foster et al. (2001) — A new approach to monitoring exercise training",
        "claim": "L'RPE de session (RPE × durée en min) prédit la fatigue accumulée mieux que les métriques GPS seules.",
        "explanation": (
            "Foster et al. proposent la méthode de charge interne. Un ratio charge aiguë/chronique interne > 1.5 "
            "indique un risque élevé, indépendamment du kilométrage. La combinaison charge externe (GPS) "
            "et charge interne (RPE) donne une image plus précise de la récupération réelle."
        ),
    },
    {
        "id": "detraining_mujika_2011",
        "tags": ["RULE-020", "sessions_manquees", "adherence", "deentrainement", "interruption", "VO2max", "perte_condition"],
        "source": "Mujika (2011) — Detraining: Loss of training-induced physiological adaptations",
        "claim": "2 semaines de désentraînement peuvent réduire la VO2max de 4–14 %.",
        "explanation": (
            "Mujika quantifie la perte de condition lors des périodes d'inactivité. "
            "Les adaptations cardiovasculaires se dégradent plus vite que les adaptations musculaires. "
            "Reprendre trop vite après une interruption augmente le risque de blessure car le système "
            "musculo-squelettique se remet en condition plus lentement que le système cardiovasculaire."
        ),
    },
    {
        "id": "cho_burke_2011",
        "tags": ["RULE-025", "glucides", "glycogene", "carbohydrates", "nutrition", "race_day", "marathon", "pre_course"],
        "source": "Burke et al. (2011) — Carbohydrates for training and competition",
        "claim": "Une charge en glucides de 10–12 g/kg/j sur 24–36 h pré-course optimise les réserves de glycogène.",
        "explanation": (
            "Burke et al. recommandent la saturation glycogénique avant toute épreuve de durée > 90 min. "
            "La stratégie améliore l'endurance de course et retarde le 'mur' du marathon. "
            "L'hydratation et la réduction de volume d'entraînement sont complémentaires dans les 48 h pré-course."
        ),
    },
]
