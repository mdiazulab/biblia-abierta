"""Datos por libro en un solo lugar: número de Aquifer, nombre en HCF, nombre español y versículos sensibles
(revisión doble: segunda traducción y firma de Claude). Agregar un libro = una entrada aquí."""

LIBROS = {
    "JHN": {"aquifer": "43", "hcf": "John", "es": "Juan", "titulo": "Evangelio según Juan",
            "base": [], "oriente": [("John Chrysostom", "Homily on the Gospel of John"), ("Cyril of Alexandria", "Commentary on the Gospel of John")],
            "occidente": [("Augustine of Hippo", "Tractates on John")],
            "sensibles": ["1.1", "1.14", "1.18", "3.5", *[f"6.{v}" for v in range(51, 59)], "14.6",
                          "20.22", "20.23", "20.28", "21.15", "21.16", "21.17"]},
    # Hebreos: cristología (1:3, 1:8), perfección de Cristo (2:10, 5:7-9, 7:28), impecabilidad (4:15),
    # apostasía (6:4-6, 10:26-29), sacerdocio e intercesión (7:25, 9:24), sacrificio único (9:14, 10:10-14),
    # comunión de los santos (11:39-40, 12:1, 12:22-24), altar (13:10)
    # sin Catena Aurea: la base es el único comentario patrístico completo en dominio público (Crisóstomo,
    # 34 homilías); el complemento, otras voces por versículo (hasta 2; 4 en sensibles), primero Occidente
    "HEB": {"aquifer": "58", "hcf": "Hebrews", "es": "Hebreos", "titulo": "Epístola a los Hebreos",
            "base": [("John Chrysostom", "Homily on Hebrews")], "oriente": [], "occidente": [], "libre": (2, 4),
            "sensibles": ["1.3", "1.8", "2.10", "4.15", "5.7", "5.8", "5.9", "6.4", "6.5", "6.6", "7.25", "7.28",
                          "9.14", "9.24", "10.10", "10.14", "10.26", "10.27", "10.28", "10.29", "11.39", "11.40",
                          "12.1", "12.22", "12.23", "12.24", "13.10"]},
}
