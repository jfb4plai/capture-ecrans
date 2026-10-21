# Sources des phrases du mode d'emploi (fonction vidéo, v1.3.0)

Chaque comportement décrit dans le mode d'emploi renvoie à une ligne de code ou à un essai.

| Phrase du manuel | Source |
|---|---|
| Raccourci par défaut Ctrl+Maj+F7 | `capture_ecran/config.py` `hotkey_video`; test `test_manual_documents_video_with_the_real_default_shortcut` |
| Choix « une zone / tout l'écran / la fenêtre active », zone par défaut | `app.py` boutons radio `v_varea`, `config.py` `video_area` |
| « Enregistrer aussi le micro » coché par défaut | `config.py` `video_mic: True` |
| La fenêtre se retire | `app.py` `start_video` : `self.withdraw()` |
| Tracer la zone, Échap annule | `selector.py` `select_box` (texte « Échap pour annuler ») |
| Zone minimale 16 × 16, dimensions paires | `recorder.py` `MIN_SIDE`, `_even`; `tests/test_recorder.py` |
| 3 à 4 s de préparation | mesuré le 2026-10-21 : `start 3.5s` et `4.5s` (version sans détection du message) ; message « Préparation… » : `app.py` `_start_video` |
| Bip au début | `app.py` `_start_video` : `winapi.beep()` après `rec.start` |
| 1 à 2 s de finalisation | mesuré le 2026-10-21 : `stop 1.7s` |
| Barre : temps, ■ Arrêter, « ou Ctrl+Maj+F7 », déplaçable | `recordbar.py`; `tests/test_app_gui.py` |
| Barre hors de la zone | `recordbar.bar_position`; `tests/test_recordbar.py` |
| Barre exclue de l'enregistrement | essai du 2026-10-21 : pixel magenta visible sans exclusion, absent avec (gdigrab, Windows 11) ; Windows 10 < 2004 : déduit, non testé |
| Win+Maj+Q ne rouvre pas la fenêtre pendant la vidéo | `app.py` `_show_window`; test GUI |
| Captures par raccourci et série de clics refusées | `app.py` `request` (message « Une vidéo est en cours ») et `toggle_steps` |
| Fichier `video_AAAA-MM-JJ_HHhMMmSS.mp4` dans la série, dossier ouvert à l'arrêt | `app.py` `_start_video`, `stop_video` |
| 15 images/s, H.264 + AAC | `recorder.py` `FPS`, `build_command` (`h264_mf`), `build_mux_command` (`aac`) |
| Pas de son de l'ordinateur | non implémenté (aucun code loopback) |
| Sans micro : vidéo sans son et message | `recorder.py` `mic_failed`; `app.py` `no_mic` |
| Vidéo absente de la liste de la série | `app.py` : `_start_video` n'appelle pas `session.add` |
| Pointeur filmé selon le réglage | `app.py` : `rec.start(..., self.v_cursor.get())`; libellé `Montrer le pointeur de la souris` |
| ffmpeg fourni, LGPL, licence et sources | `tools/fetch_ffmpeg.py`; `lanceur.py` `_selftest`; dossier `ffmpeg\` de l'installateur |
| Synchronisation | durées mesurées égales (9,13 s / 9,13 s) ; non contrôlée à l'oreille |
