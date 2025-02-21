FAIRDM_ALLOWED_IDENTIFIERS = {
    "samples.Sample": {
        "IGSN": "https://igsn.org/",
        # "DOI": "https://doi.org/",
    },
    "contributors.Person": {
        "ORCID": "https://orcid.org/",
        # "researcher_id": "https://app.geosamples.org/sample/researcher_id/",
        # "scopus_id": "https://app.geosamples.org/sample/scopus_id/",
        # "researchgate_id": "https://app.geosamples.org/sample/researchgate_id/",
    },
    "contributors.Organization": {
        "ROR": "https://ror.org/",
        "GRID": "https://www.grid.ac/institutes/",
        "Wikidata": "https://www.wikidata.org/wiki/",
        "ISNI": "https://isni.org/isni/",
        "Crossref Funder ID": "https://doi.org/",
    },
}


FAIRDM_X_COORD = {
    "decimal_places": 5,
    "max_digits": None,
}

FAIRDM_Y_COORD = {
    "decimal_places": 5,
    "max_digits": None,
}

FAIRDM_CRS = "EPSG:4326"


FAIRDM_DATASET = {
    "keyword_vocabularies": [
        "fairdm_geo.vocabularies.cgi.geosciml.SimpleLithology",
        "fairdm_geo.vocabularies.stratigraphy.GeologicalTimescale",
    ],
}
