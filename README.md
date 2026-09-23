# Popote

Menus du soir, liste de courses et répertoire d'aliments pour un mangeur difficile. PWA publiée sur GitHub Pages, données dans Supabase, dans le même monde que Cockpit D2 et Pages contre minutes (lavande, hippo pixel).

- App : https://natnaat.github.io/popote/ (dépôt https://github.com/NatNaat/popote)
- Page : `index.html` (HTML, CSS et JS dans un seul fichier), `config.js` (URL et clé anon Supabase, publiques), `sw.js`, `manifest.webmanifest`, icônes marmite (`icon.svg`, `icon-180.png`, `icon-512.png`).
- Base : `supabase/schema.sql`, à exécuter une fois dans le même projet Supabase que Pages contre minutes.
- Ancienne version Artifact (abandonnée le 23 septembre 2026) : https://claude.ai/artifact/3BdAnvyfpLLT5SCBmtV5pa

## Principe

- **Répertoire** : tri de cartes (≈130 aliments et plats courants) en quatre verdicts : j'adore, ça va, à essayer, jamais. Les menus ne sortent jamais du répertoire ; un « jamais » n'apparaît jamais, un « à essayer » seulement dans le créneau essai.
- **Semaine** : « Composer ma semaine » tire dans les recettes autorisées (18 recettes, 10 secours intégrés, plus celles écrites par Claude), le midi seulement hors RU, le soir toujours, avec un repas de secours de 10 minutes par soir. Les semaines composées par Claude arrivent par la base, depuis Claude Code (voir plus bas).
- **Ce soir** : une ardoise avec le plat, deux boutons (Motivé / Flemme), « C'est fait ». Série de soirs cuisinés, humeurs de l'hippo en toque.
- **Courses** : liste agrégée des repas à venir, par rayon, cochable, disponible hors ligne ; « Copier » ; « Envoyer dans Rappels » via le raccourci iOS `Courses`. Le placard (ce qu'on a toujours) sort de la liste.
- **Essai de la semaine** : un aliment « à essayer », une bouchée à côté d'un plat aimé ; résultat : adopté (passe en « ça va »), à refaire autrement, jamais.

## Installation (une fois)

1. Supabase › SQL Editor : coller `supabase/schema.sql`, Run. Il réutilise `is_owner()` et le compte propriétaire de Pages contre minutes.
2. iPhone : ouvrir https://natnaat.github.io/popote/ dans Safari, se connecter (même email et mot de passe que Pages contre minutes), Partager › « Sur l'écran d'accueil ». L'icône marmite et l'ouverture plein écran viennent du manifest.
3. Réglages › « Clé pour Claude Code » › Copier, puis la coller dans `~/.config/popote/secret` sur le Mac (fichier hors dépôt). Elle permet à Claude Code de lire et d'écrire les documents.
4. Facultatif : `python3 shortcuts/build_courses.py` produit `Courses.shortcut` (un rappel par ligne dans la liste Rappels « Courses »).

## Données

Table `popote_docs (coll, id, data jsonb)`, un document par ligne, protégée par RLS (propriétaire seulement). Fonctions `popote_dump(secret)` et `popote_put(secret, docs)` pour l'accès par secret.

| coll | id | data |
|---|---|---|
| `config` | `main` | équipement, jours au RU (`midiRU`), budget, magasin, nom du raccourci, placard, essai par semaine |
| `aliments` | id du catalogue ou `x-…` | `{nom, cat, rayon, verdict, notes, essais[]}` |
| `recettes` | `c-…` (Claude) ou `b-…`/`s-…` (avis sur une recette de base) | `{nom, mode:'recette'|'secours', minutes, equipement[], ing:[{a, q, u, opt}], etapes[], source, avis, nbFaits}` |
| `stock` | `main` | `{items:{<alimentId>:{depuis}}}` : ce qu'il a au frigo et au placard en ce moment (le frais expire après 8 jours, le reste après 90). Les menus s'en servent d'abord, la liste de courses le retire, cocher un article acheté l'y ajoute |
| `semaines` | lundi ISO | `{jours:{date:{midi?, soir:{recette, secours, statut, flemme}}}, essai, courses:{items[]}, resume, source}` |

La page garde un miroir dans `localStorage` (`popote-mirror`) et une file d'attente hors ligne (`pop:outbox`) : les modifications faites sans réseau partent au retour.

## Composer la semaine depuis Claude Code

```bash
python3 tools/popote_db.py dump
```

donne tout (répertoire, recettes, semaines). Claude compose ensuite les repas selon les règles de l'app (aliments adore/ok seulement, jamais un « jamais », un seul essai, assiette protéine + féculent + légume ou fruit, ≤ 30 min, secours ≤ 10 min, équipement de `config/main`, et en priorité ce qu'il a déjà dans `stock/main`), écrit les nouvelles recettes (`c-<slug>`, ingrédients avec `a` = id d'aliment du répertoire ou `placard:true`) et la semaine (`source:"claude"`, `resume`), puis :

```bash
python3 tools/popote_db.py put /chemin/semaine.json
```

L'app recharge à l'ouverture ou au retour au premier plan.

## Republier

Modifier `index.html`, incrémenter `CACHE` dans `sw.js`, commit et push sur `main`. GitHub Pages sert avec un cache de 10 minutes que le service worker contourne ; un relancement complet de l'app suffit.

## Test local

Configuration `popote` de `~/.claude/launch.json` (python `http.server` 8794), puis `http://localhost:8794/?demo` : mode local sans Supabase, données dans le navigateur, mêmes écrans.
