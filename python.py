#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mini-jeu console : Explorateur de donjon (initiation Python)
- Déplace-toi dans une grille (zqsd ou wasd)
- Ramasse des trésors (T) pour gagner des points
- Évite les pièges (X) qui te font perdre de la vie
- Bonus soin (❤) pour récupérer des PV
- Quand tous les trésors sont ramassés, une sortie (E) apparaît : marche dessus pour gagner

Aucune dépendance externe. Fonctionne dans un terminal (GitHub Codespaces).
"""

import random
import os
import sys


# ---------- Utilitaires d'affichage ----------

def clear_screen() -> None:
    """Efface l'écran du terminal (Windows/Linux/Mac)."""
    os.system("cls" if os.name == "nt" else "clear")


def clamp(n: int, lo: int, hi: int) -> int:
    """Force n à rester entre lo et hi."""
    return max(lo, min(hi, n))


def count_symbol(grid: list[list[str]], symbol: str) -> int:
    """Compte le nombre d'occurrences d'un symbole dans la grille."""
    return sum(row.count(symbol) for row in grid)


# ---------- Génération du monde ----------

def make_grid(width: int, height: int, fill: str = ".") -> list[list[str]]:
    """Crée une grille height x width remplie par 'fill'."""
    return [[fill for _ in range(width)] for _ in range(height)]


def place_random(grid: list[list[str]], symbol: str, count: int, forbidden: set[tuple[int, int]]) -> None:
    """Place 'count' éléments 'symbol' aléatoirement, en évitant forbidden et les cases déjà occupées."""
    h = len(grid)
    w = len(grid[0])
    placed = 0
    tries = 0
    while placed < count and tries < 10_000:
        tries += 1
        x = random.randrange(w)
        y = random.randrange(h)
        if (x, y) in forbidden:
            continue
        if grid[y][x] != ".":
            continue
        grid[y][x] = symbol
        placed += 1


def build_world(width: int, height: int) -> dict:
    """
    Construit le monde et renvoie un dict contenant :
    - grid
    - player_pos (x, y)
    - score
    - hp
    - turn
    - exit_spawned (bool)
    - won (bool)
    """
    grid = make_grid(width, height)

    # Position initiale du joueur
    px, py = width // 2, height // 2
    forbidden = {(px, py)}

    # Bordures (murs)
    for x in range(width):
        grid[0][x] = "#"
        grid[height - 1][x] = "#"
    for y in range(height):
        grid[y][0] = "#"
        grid[y][width - 1] = "#"

    # Interdiction sur les murs + position joueur
    for x in range(width):
        forbidden.add((x, 0))
        forbidden.add((x, height - 1))
    for y in range(height):
        forbidden.add((0, y))
        forbidden.add((width - 1, y))

    # Place quelques obstacles internes
    place_random(grid, "#", count=max(6, (width * height) // 18), forbidden=forbidden)

    # Place des trésors et pièges
    place_random(grid, "T", count=max(4, (width * height) // 30), forbidden=forbidden)
    place_random(grid, "X", count=max(4, (width * height) // 35), forbidden=forbidden)

    # Place un bonus rare
    place_random(grid, "❤", count=1, forbidden=forbidden)

    return {
        "grid": grid,
        "player_pos": (px, py),
        "score": 0,
        "hp": 5,
        "turn": 0,
        "message": "Bienvenue ! Déplace-toi avec zqsd (ou wasd).",
        "exit_spawned": False,
        "won": False,
    }


# ---------- Logique du jeu ----------

def render(world: dict) -> None:
    """Affiche la grille et l'état du joueur."""
    grid = world["grid"]
    px, py = world["player_pos"]

    clear_screen()
    print("=== 🗺️  Explorateur de donjon ===\n")
    print(f"PV: {world['hp']}   Score: {world['score']}   Tour: {world['turn']}")
    print("Commandes: zqsd / wasd pour bouger, r pour relancer, h pour aide, x pour quitter\n")

    # Affichage de la grille avec le joueur
    for y, row in enumerate(grid):
        line = []
        for x, cell in enumerate(row):
            if (x, y) == (px, py):
                line.append("🙂")
            else:
                line.append(cell)
        print(" ".join(line))

    print("\n" + world["message"])


def help_text() -> str:
    return (
        "AIDE:\n"
        "- '.' = sol\n"
        "- '#' = mur (bloque)\n"
        "- 'T' = trésor (+10 points)\n"
        "- 'X' = piège (-1 PV)\n"
        "- '❤' = soin (+2 PV)\n"
        "- 'E' = sortie (apparaît quand tous les trésors sont ramassés)\n"
        "Objectif: Ramasser tous les trésors puis trouver la sortie.\n"
    )


def spawn_exit(world: dict) -> None:
    """Place une sortie 'E' sur une case libre."""
    grid = world["grid"]
    px, py = world["player_pos"]
    h = len(grid)
    w = len(grid[0])

    for _ in range(200):
        x = random.randrange(1, w - 1)
        y = random.randrange(1, h - 1)
        if (x, y) == (px, py):
            continue
        if grid[y][x] == ".":
            grid[y][x] = "E"
            world["exit_spawned"] = True
            world["message"] = "✨ Tous les trésors sont ramassés ! Une sortie 'E' est apparue !"
            return

    world["message"] = "⚠️ Sortie impossible à placer (carte trop remplie)."


def try_move(world: dict, dx: int, dy: int) -> None:
    """Tente de déplacer le joueur et gère les interactions."""
    grid = world["grid"]
    px, py = world["player_pos"]
    nx = px + dx
    ny = py + dy

    # Hors limites (normalement bordé par des murs)
    ny = clamp(ny, 0, len(grid) - 1)
    nx = clamp(nx, 0, len(grid[0]) - 1)

    target = grid[ny][nx]
    if target == "#":
        world["message"] = "🧱 Ouch, un mur !"
        return

    # Déplacement
    world["player_pos"] = (nx, ny)
    world["turn"] += 1

    # Interaction avec la case
    if target == "T":
        world["score"] += 10
        world["message"] = "💰 Trésor trouvé ! +10 points."
        grid[ny][nx] = "."  # consommé
    elif target == "X":
        world["hp"] -= 1
        world["message"] = "💥 Piège ! -1 PV."
        grid[ny][nx] = "."  # consommé
    elif target == "❤":
        world["hp"] += 2
        world["message"] = "💖 Soin ! +2 PV."
        grid[ny][nx] = "."  # consommé
    elif target == "E":
        world["won"] = True
        world["message"] = "🏁 Tu as trouvé la sortie ! VICTOIRE !"
        return
    else:
        world["message"] = random.choice([
            "Tu avances prudemment...",
            "Rien d'intéressant ici.",
            "Le donjon est silencieux.",
            "Tu entends un bruit au loin 👀",
        ])

    # Si plus de trésors, on fait apparaître la sortie (une seule fois)
    if (not world["exit_spawned"]) and count_symbol(grid, "T") == 0:
        spawn_exit(world)

    # Un peu de dynamique : avant la sortie, on peut faire apparaître des choses
    maybe_spawn(world)


def maybe_spawn(world: dict) -> None:
    """Ajoute un peu de 'vie' : spawn aléatoire de trésors/pièges (désactivé une fois la sortie apparue)."""
    if world.get("exit_spawned", False):
        return

    grid = world["grid"]
    px, py = world["player_pos"]

    roll = random.random()

    # 12%: nouveau trésor, 8%: nouveau piège
    if roll < 0.12:
        symbol = "T"
    elif roll < 0.20:
        symbol = "X"
    else:
        return

    h = len(grid)
    w = len(grid[0])
    for _ in range(60):
        x = random.randrange(1, w - 1)
        y = random.randrange(1, h - 1)
        if (x, y) == (px, py):
            continue
        if grid[y][x] == ".":
            grid[y][x] = symbol
            if symbol == "T":
                world["message"] += " (Un éclat doré apparaît quelque part...)"
            else:
                world["message"] += " (Une sensation de danger plane...)"
            return


def parse_command(cmd: str) -> str:
    """Normalise la commande."""
    return cmd.strip().lower()[:1] if cmd else ""


def game_loop(width: int = 15, height: int = 11) -> None:
    world = build_world(width, height)

    while True:
        render(world)

        # Victoire
        if world.get("won", False):
            print("\n🎉 BRAVO ! Tu as gagné !")
            print(f"Score final: {world['score']}  |  Tours: {world['turn']}")
            cmd = parse_command(input("Tape 'r' pour rejouer ou 'x' pour quitter: "))
            if cmd == "r":
                world = build_world(width, height)
                continue
            return

        # Défaite
        if world["hp"] <= 0:
            print("\n☠️  GAME OVER !")
            print(f"Score final: {world['score']}  |  Tours survivus: {world['turn']}")
            cmd = parse_command(input("Tape 'r' pour rejouer ou 'x' pour quitter: "))
            if cmd == "r":
                world = build_world(width, height)
                continue
            return

        cmd = parse_command(input("\n> "))

        if cmd == "x":
            return
        if cmd == "h":
            world["message"] = help_text()
            continue
        if cmd == "r":
            world = build_world(width, height)
            continue

        # Contrôles AZERTY: zqsd ; QWERTY: wasd
        moves = {
            "z": (0, -1),  # up
            "w": (0, -1),  # up (qwerty)
            "s": (0, 1),   # down
            "q": (-1, 0),  # left (azerty)
            "a": (-1, 0),  # left (qwerty)
            "d": (1, 0),   # right
        }

        if cmd in moves:
            dx, dy = moves[cmd]
            try_move(world, dx, dy)
        else:
            world["message"] = "Commande inconnue. Tape 'h' pour l'aide."


def main() -> None:
    random.seed()
    game_loop(width=15, height=11)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye 👋")
        sys.exit(0)
