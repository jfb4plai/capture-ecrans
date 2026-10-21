# Plan v1.3 : capture vidéo et audio de la zone

Décisions de JF (2026-10-21) : micro + son du système ; ffmpeg embarqué ; pas de pause.
Statut au 2026-10-21 : tâches 1, 2, 3, 6 (sans cadre rouge) faites, micro inclus ; non commité. Tests : 114 passés, 2 ignorés.
Restent : cadre rouge, son du système, ffmpeg embarqué (PyInstaller + .iss + licences), mode d'emploi, recette R1-R10 par JF.
Constats : encodeur h264_mf du build LGPL BtbN OK ; aac_mf coupe le son (utiliser aac) ; micro et image dans une seule commande ffmpeg perdent 2-3 s d'audio, donc image et micro sont enregistrés à part puis assemblés (fin calée sur la fin de l'image). Les points « déduit » ne sont pas testés.

## Cadre
- Mêmes modes que la capture : écran entier, zone, fenêtre active.
- Sortie : un MP4 (H.264 + AAC) rangé dans le dossier de la série.
- Audio : micro seul, système seul, les deux (mixés), ou aucun. Réglage mémorisé.
- Arrêt par raccourci ou bouton. Pas de pause.

## Tâches
1. **Zone avec coordonnées** : `selector.select_region` renvoie aussi le rectangle (x, y, l, h) en pixels de l'écran virtuel (origine `winapi.virtual_screen()`). Garder la signature actuelle pour la capture simple (nouvelle fonction `select_box`, `select_region` l'appelle).
2. **Rectangle pour fenêtre active** : `winapi.foreground_window_rect()` existe déjà ; l'utiliser comme rectangle.
3. **Module `recorder.py`** : lance `ffmpeg` en sous-processus. Entrées : `-f gdigrab -framerate 15 -offset_x -offset_y -video_size -draw_mouse 1 -i desktop` ; audio dshow micro et/ou loopback. Largeur et hauteur arrondies au pair. `-c:v libx264 -preset ultrafast -pix_fmt yuv420p`. Arrêt : écrire `q` sur stdin, attendre la fin, sinon `terminate`.
4. **Son du système** : voir « Point dur » ci-dessous.
5. **Cadre d'enregistrement** : fenêtre topmost sans bordure, cliquable à travers (style `WS_EX_TRANSPARENT`), dessinée **autour** de la zone pour ne pas apparaître dans la vidéo. Compte à rebours 3 s avant le début.
6. **Interface** : modes « Vidéo zone / écran / fenêtre » dans [app.py](../capture_ecran/app.py), menu des sources audio dans les réglages, raccourci de démarrage/arrêt dans [config.py](../capture_ecran/config.py) (`hotkey_video`, proposition `ctrl+shift+f7`, à vérifier libre), durée affichée pendant l'enregistrement.
7. **Série** : la vidéo apparaît dans la liste comme un élément (vignette = première image) ; exclue de l'export Word/HTML, ou lien seulement. À trancher à l'étape 6.
8. **ffmpeg embarqué** : voir « Licence ». `find_ffmpeg` cherche déjà « à côté du programme » ([exporter.py:129](../capture_ecran/exporter.py)) ; ajouter `ffmpeg.exe` au PyInstaller et à [capture-ecran.iss](../installer/capture-ecran.iss).
9. **Mode d'emploi** : section vidéo dans `MODE_EMPLOI.md` et le manuel intégré. Chaque phrase de comportement cite sa source (ligne de code ou capture) avant d'être écrite. Le guide `MODE_EMPLOI_VIDEO.md` actuel concerne l'export vidéo des séries, pas cette fonction : ne pas les confondre.
10. **Tests** : unitaires (construction de la ligne de commande, arrondi au pair, rectangles négatifs multi-écrans) ; recette réelle ci-dessous.

## Point dur : son du système
- `dshow` ne voit le son du système que si « Mixage stéréo » est activé (rare, déduit).
- Solution : loopback WASAPI par une bibliothèque Python (`soundcard` ou `PyAudioWPatch`, à choisir après essai sur le PC de JF), enregistré en WAV à part.
- Le micro et le système sont enregistrés en pistes séparées puis mixés par ffmpeg (`amix`) à l'arrêt, ce qui évite de synchroniser deux flux en direct.
- Risque : dérive de synchronisation sur de longues prises. Limite à mesurer sur 10 min avant de promettre quoi que ce soit.
- Si aucune bibliothèque ne passe dans le paquet PyInstaller : repli sur micro seul, annoncé dans l'interface.

## Licence
- Le dépôt est sous PolyForm NC. Un `ffmpeg.exe` GPL (builds « full » de gyan.dev) obligerait à fournir les sources et à vérifier la compatibilité.
- Piste : build **LGPL** (BtbN « lgpl »), qui n'a pas `libx264`. Encodage alors par `h264_mf` (Media Foundation, intégré à Windows, déduit disponible) ou `mpeg4`. À tester sur le PC de JF et sur une machine de collègue.
- Si aucun encodeur LGPL n'est acceptable : ne pas embarquer, proposer l'installation guidée de ffmpeg (winget) au premier usage.
- Dans tous les cas : joindre la licence et la mention de source de ffmpeg à l'installateur.
- **À valider avant d'écrire le code d'encodage.**

## Recette (à faire sur le vrai parcours)
| N° | Test | Attendu |
|---|---|---|
| R1 | Vidéo zone 30 s, sans audio | MP4 lisible, taille de la zone, pointeur visible, cadre rouge absent de l'image |
| R2 | Écran secondaire à gauche (coordonnées négatives) | zone correcte |
| R3 | Affichage Windows à 125 % et 150 % | zone alignée sur ce qui a été tracé |
| R4 | Micro seul | voix audible |
| R5 | Système seul (vidéo YouTube) | son audible |
| R6 | Micro + système | les deux audibles, volumes équilibrés |
| R7 | 10 min micro + système | décalage son/image mesuré, noté |
| R8 | Fermer l'appli ou verrouiller la session en cours d'enregistrement | fichier récupérable |
| R9 | PC sans micro | message clair, enregistrement possible sans micro |
| R10 | Installateur sur machine propre | ffmpeg trouvé, aucune installation à faire |

## Ordre
Licence ffmpeg (essai encodeur) → tâches 1-3 (vidéo sans son) → 5-6 → son micro → son système → 7-9 → recette.

## Ce que l'outil ne fera pas bien (à dire dans le mode d'emploi)
- Pas de pause ni de montage.
- Pas de capture d'une fenêtre protégée (lecteurs avec DRM : image noire, déduit).
- Fichiers lourds au-delà de quelques minutes.
