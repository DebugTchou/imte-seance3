#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import urllib.request
import urllib.error


API_URL = "https://api.whatdoestrumpthink.com/api/v1/quotes/random"


def get_random_trump_quote(timeout: int = 10) -> str:
    """
    Appelle l'API WhatDoesTrumpThink et renvoie une citation aléatoire (champ 'message').
    """
    req = urllib.request.Request(
        API_URL,
        headers={"Accept": "application/json", "User-Agent": "trump-quote-codespace/1.0"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Réponse HTTP inattendue: {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))

    except urllib.error.URLError as e:
        raise RuntimeError(f"Impossible de contacter l'API: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError("Réponse reçue mais JSON invalide.") from e

    quote = data.get("message")
    if not quote or not isinstance(quote, str):
        raise RuntimeError(f"Réponse inattendue de l'API: {data}")

    return quote.strip()


def main() -> None:
    try:
        quote = get_random_trump_quote()
        print("🗨️ Citation aléatoire :\n")
        print(f"“{quote}”")
    except Exception as e:
        print(f"Erreur: {e}")


if __name__ == "__main__":
    main()
