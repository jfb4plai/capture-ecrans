# Capture d'écran PLAI — mode d'emploi

Pour photographier un **menu déroulant** (qui se ferme dès qu'on clique ailleurs), l'ajouter des **flèches, textes, numéros**, puis en faire une **fiche** ou une **vidéo sous-titrée**. Il peut aussi **filmer votre écran** (une zone, avec votre voix).

## 1. Installer (une seule fois)
**Option A — l'installateur (conseillé)** : téléchargez `Capture-ecran-PLAI-installateur.exe` sur jfb4plai.com et double-cliquez dessus (aucun droit d'administrateur). Si Windows affiche « Windows a protégé votre ordinateur » (programme non signé) : *Informations complémentaires* › *Exécuter quand même*. Choisissez dans l'assistant le raccourci du bureau et le lancement avec Windows. Le programme apparaît aussi dans le menu Démarrer.

**Option A bis — le dossier zippé (sans installation)** :
1. **Avant d'extraire** : clic droit sur le fichier `.zip` › *Propriétés* › en bas de l'onglet *Général*, cochez **« Débloquer »** › *OK*. (La case n'apparaît que si Windows a marqué le fichier comme venant d'Internet.) Cela évite en général l'avertissement décrit plus bas.
2. Clic droit sur le zip › *Extraire tout…*
3. Dans le dossier extrait, double-cliquez sur `Capture-ecran-PLAI.exe` (ne le lancez pas depuis l'intérieur du zip).
4. Si Windows affiche quand même « Windows a protégé votre ordinateur » (le programme n'est pas signé numériquement) : cliquez sur *Informations complémentaires* puis *Exécuter quand même*.

**Est-il sûr ?** Chaque version est analysée par Microsoft Defender et par ClamAV pendant sa fabrication ; le rapport d'analyse et l'empreinte du fichier (SHA-256) sont publiés avec la version, sur la page des versions du dépôt. Attention : un résultat propre ne fait **pas** disparaître l'avertissement ci-dessus, qui dépend de la signature numérique du programme et de sa notoriété, pas de la présence d'un virus. Si votre école bloque les programmes inconnus, remettez le rapport à votre service informatique.

**Option B — avec Python** (si votre école l'autorise) : installez Python 3 depuis python.org (cochez « Add to PATH »), puis double-cliquez sur `Lancer.bat`.

Rien n'est envoyé sur Internet.

**Où sont mes captures ?** Au premier lancement, le programme crée sur votre **bureau** un dossier **« Capture-ecran-jfb4plai »** (avec le logo jfb4plai) et l'ouvre. Chaque série de captures y a son sous-dossier (date et heure). Le chemin est toujours affiché en haut de la fenêtre : cliquez dessus pour ouvrir le dossier. Dans chaque série : les images annotées, un dossier `originales` (sans annotation), `audio`, et vos exports (`document.docx`, `fiche_pas_a_pas.html`, `video`).

> ⚠ **Bureau synchronisé (OneDrive…)** : sur beaucoup d'ordinateurs, le bureau est copié automatiquement dans le cloud de Microsoft. Si vos captures peuvent montrer des noms ou des écrans d'élèves, choisissez un autre dossier (*Réglages…*) ou le choix « Documents » proposé au premier lancement. Le programme vous avertit quand il détecte ce cas (détection indicative : en cas de doute, vérifiez vous-même).

Les versions précédentes (1.0 et 1.1 avant ce changement) rangeaient les captures dans `Images\Captures PLAI` : retrouvez-les avec le bouton **Rouvrir…**.

## Ouvrir facilement le programme
Contrairement à l'outil de capture de Windows (`Windows`+`Maj`+`S`), **mes raccourcis ne fonctionnent que si le programme est ouvert** (la touche `Windows`+`Maj`+`S` est réservée par Windows : j'utilise `Ctrl`+`Maj`+`F9` à `F12`). Pour l'avoir toujours sous la main :
- **Raccourci sur le bureau** : le programme vous le propose au premier lancement. Vous pouvez aussi le créer ou le retirer dans *Réglages › Ouvrir facilement*, avec un raccourci dans le menu Démarrer.
- **Lancement automatique à l'ouverture de Windows** : même endroit. Le programme démarre alors **réduit dans la barre des tâches** : il est prêt quand vous en avez besoin.
- **Épingler à la barre des tâches** : clic droit sur le raccourci › *Épingler à la barre des tâches*.
- Si le programme est déjà ouvert, un second lancement ramène simplement la fenêtre au premier plan.
- **`Windows`+`Maj`+`Q` rouvre la fenêtre** quand le programme tourne (par exemple lancé au démarrage de Windows). Si cette combinaison est déjà prise par un autre programme, le message d'état l'indique : changez-la dans *Réglages › Raccourcis clavier*.
- **Et si le programme est fermé ?** Windows n'autorise pas la touche `Windows` pour *lancer* un programme. Alternative : *Réglages › Ouvrir facilement*, case « Les raccourcis s'ouvrent aussi avec **Ctrl+Alt+Q** ». Sur un clavier belge, `Ctrl`+`Alt` est la touche AltGr : à désactiver si vous tapez souvent `AltGr`+`Q`. (Je n'ai pas pu vérifier cette combinaison sur un vrai poste.)

> ⚠ **Avant de créer un raccourci**, déplacez le dossier extrait du zip (`Capture-ecran-PLAI`) à un endroit **durable**, par exemple dans *Documents*. Le raccourci pointe vers ce dossier : si vous le videz (Téléchargements) ou le supprimez, il ne fonctionnera plus. Le programme vous prévient quand il tourne depuis « Téléchargements » ou un dossier temporaire. Pour réparer un raccourci après un déplacement : relancez le programme depuis son nouvel emplacement et revalidez *Réglages › Ouvrir facilement*.

## Mettre à jour le programme
- **Avec l'installateur** : lancez le nouvel installateur. Il ferme le programme s'il est ouvert, remplace l'ancienne version et garde vos raccourcis. Captures (dossier « Capture-ecran-jfb4plai » du bureau) et réglages (`%APPDATA%\CaptureEcranPLAI`) sont en dehors du programme : ils sont conservés.
- **Si vous aviez la version zip** : l'installateur ne supprime pas l'ancien dossier ; supprimez-le (et ses anciens raccourcis) après l'installation.
- **Avec le zip** : fermez le programme (clic droit sur son icône › Fermer), téléchargez et *Débloquez* le nouveau zip, extrayez-le **dans le même dossier** (remplacer les fichiers). Extrait ailleurs : supprimez l'ancien dossier, lancez la nouvelle version, recochez les raccourcis dans *Réglages*.
- **Désinstaller** (version installée) : Paramètres de Windows › Applications › Capture d'écran PLAI. Captures et réglages ne sont pas supprimés.

## 2. Photographier un menu déroulant
1. Lancez le programme (une petite fenêtre s'ouvre ; vous pouvez la réduire).
2. Ouvrez votre menu comme d'habitude (clic sur *Fichier*, clic droit…).
3. **Sans cliquer ailleurs**, appuyez sur le raccourci :

| Raccourci | Effet |
|---|---|
| **Ctrl + Maj + F9** | tout l'écran |
| **Ctrl + Maj + F10** | vous choisissez une zone (le menu est déjà « figé ») |
| **Ctrl + Maj + F11** | la fenêtre active seulement |
| **Ctrl + Maj + F12** | démarre / arrête la **série de clics** (voir ci-dessous) |
| **Ctrl + Maj + F8** | **capture simple**, comme `Windows`+`Maj`+`S` : vous tracez une zone, elle part dans le presse-papiers (`Ctrl+V` pour coller). Sans pointeur ni halo jaune. Par défaut : **presse-papiers seulement** (aucun fichier). *Réglages › Capture simple* permet aussi de la ranger dans votre série, ou de l'ouvrir dans l'éditeur |
| **Ctrl + Maj + F7** | **filme l'écran** (démarre, puis arrête) : voir « 3. Filmer l'écran en vidéo » |
| **Windows + Maj + Q** | **rouvre la fenêtre** du programme (réduite dans la barre des tâches) |

Un bip confirme la capture. Sur certains portables, ajoutez la touche **Fn**.
Les raccourcis se changent via le bouton *Raccourcis…* (évitez Ctrl+Alt : c'est la touche AltGr du clavier belge).

**Si le raccourci ne marche pas** : bouton **« Dans 3 secondes »**, ouvrez votre menu pendant le décompte.
Le pointeur est dessiné avec un halo jaune pour montrer où vous avez cliqué (désactivable).

### La série de clics (une capture numérotée par clic)
Idéal pour expliquer une manipulation : faites-la **une fois**, le programme prend une image à chaque clic.
1. Cliquez sur **● Enregistrer mes clics** (ou `Ctrl+Maj+F12`). Le bouton devient **■ Arrêter l'enregistrement (N clics)**, le titre de la fenêtre et la barre du bas indiquent le nombre de clics, et la liste de droite se remplit **en direct** (rouvrez la fenêtre avec `Win+Maj+Q` pour la voir).
2. Faites votre manipulation normalement. **Un bip = une étape enregistrée.** Chaque image reçoit un **cercle rouge** autour du clic, une **pastille numérotée** et la légende « Cliquez ici ».
3. Arrêtez avec `Ctrl+Maj+F12` (évitez de cliquer sur la barre des tâches pour rouvrir la fenêtre : ce clic serait enregistré).
4. Améliorez chaque étape (double-clic sur la ligne) : légende, flèche, voix.

*Moment de l'image* : **juste avant le clic** (recommandé : on voit le menu ouvert et le pointeur sur l'élément à cliquer) ou **0,5 s après** (on voit le résultat). Un double-clic est fusionné en une seule étape. Les clics dans notre propre fenêtre sont ignorés ; les clics gauche et droit sont enregistrés (pas le glisser-déposer ni le clavier).
Si vous supprimez ou déplacez des étapes : bouton **↻ Renuméroter**.

**Sélectionner plusieurs captures** : case **Tout sélectionner** sous la liste, ou `Ctrl+clic` (une par une) / `Maj+clic` (une plage). Sélection multiple : **Supprimer**, **▲ ▼** (déplace le bloc) et les exports (le programme demande alors s'il faut exporter seulement la sélection ; les fichiers portent le suffixe `_selection`, rien n'est écrasé).

## 3. Filmer l'écran en vidéo
Pour montrer une manipulation en mouvement, avec votre voix. Le résultat est **un fichier MP4** (image 15 par seconde, son AAC : votre voix et ce qui sort des haut-parleurs ou du casque, mélangés) rangé dans le dossier de la série en cours. À ne pas confondre avec la « vidéo sous-titrée » faite à partir de captures (section 5).

1. Dans la fenêtre, choisissez **Filmer** : *une zone* (par défaut), *tout l'écran* ou *la fenêtre active*. Cochez ou non **Enregistrer aussi le micro** et **Enregistrer aussi le son de l'ordinateur** (les deux sont cochés par défaut). Facultatif : indiquez un nombre de minutes dans **Arrêt automatique après** (par exemple 10) pour que l'enregistrement s'arrête tout seul ; laissez vide pour arrêter vous-même.
2. Cliquez sur **🎬 Enregistrer une vidéo** ou appuyez sur `Ctrl`+`Maj`+`F7` (modifiable dans *Réglages…*). La fenêtre se retire pour ne pas être filmée.
3. *Une zone* : l'écran se fige, tracez la zone avec la souris (`Échap` annule). Minimum 16 × 16 pixels.
4. Patientez **3 à 4 secondes** (« Préparation de l'enregistrement… », ouverture du micro). Un bip signale le début : parlez et agissez à partir de ce bip.
5. Une **barre sombre** reste au premier plan : temps écoulé, bouton **■ Arrêter**, rappel « ou Ctrl+Maj+F7 ». Avec un arrêt automatique, elle affiche le temps **restant** (« reste 03:12 »), orange sur les 10 dernières secondes, et un bip prévient 10 secondes avant la fin. Elle se place **hors de la zone filmée** (au-dessus, sinon en dessous, à droite ou à gauche) ; on la déplace en la faisant glisser.
6. Arrêtez avec **■ Arrêter** ou de nouveau `Ctrl`+`Maj`+`F7`. Comptez 1 à 2 secondes de finalisation : le dossier de la série s'ouvre avec `video_AAAA-MM-JJ_HHhMMmSS.mp4`.

- **Pendant l'enregistrement**, `Windows`+`Maj`+`Q` ne rouvre pas la fenêtre (elle se poserait sur la zone) : il ramène seulement la barre au premier plan. Les captures par raccourci et la série de clics sont refusées jusqu'à l'arrêt.
- **Pointeur** : filmé si *Réglages… › Montrer le pointeur de la souris* est coché. **Écran entier** : la barre ne peut pas se placer hors de l'image ; Windows est prié de l'exclure de l'enregistrement (essai du 21/10/2026 sur une image fixe, Windows 11 ; non garanti sur Windows 10 antérieur à la version 2004).

**Ce que cette fonction ne fait pas** : pas de pause ni de montage ; l'arrêt automatique se règle en minutes entières de 1 à 600 (pas d'heure de fin) et compte à partir du début de l'image ; les fichiers sont lourds (environ 29 Mo pour 1 minute d'écran entier, mesuré sur un seul écran) ; le son de l'ordinateur est celui de la **sortie audio utilisée au départ** (brancher un casque en cours de prise n'est pas suivi) ; les deux sons sont mélangés, le son de l'ordinateur baissé à 70 % (réglage à l'oreille non vérifié) ; si un son est indisponible, la vidéo est faite sans lui et la barre d'état le dit ; le premier micro détecté par Windows est utilisé (pas de choix dans le programme) ; la vidéo n'entre pas dans la liste des captures, ni dans le Word ou la fiche HTML ; dimensions arrondies au nombre pair ; fenêtres protégées par certains lecteurs vidéo : peut-être noires (non vérifié). La synchronisation n'a pas été contrôlée à l'oreille : mesure de test du 21/10/2026 (flash d'écran et bip simultanés), le son du système arrive de 0,23 à 0,24 s après l'image, dont une part vient du test (latence de lecture d'environ 0,1 s). Signalez tout décalage gênant. Coupez les notifications personnelles avant de filmer.

## 4. Annoter (l'éditeur s'ouvre tout seul)
Choisissez un outil, une couleur, une taille, puis glissez sur l'image.

| Outil | Usage |
|---|---|
| ➚ Flèche | montrer un bouton (Maj = flèche bien droite) |
| ▭ Cadre / ◯ Ovale / ▮ Surligner | entourer, mettre en évidence |
| T Texte | cliquer puis écrire ; **double-clic sur un texte pour le corriger** |
| ① Numéro | poser 1, 2, 3… pour les étapes |
| ✎ Crayon | dessin libre |
| ■ **Masquer** | aplat noir **définitif** sur un prénom, un nom d'élève, une adresse (**RGPD**) |
| ▦ Pixelliser | mosaïque, **déconseillée** pour les données personnelles (un flou léger peut être partiellement reconstitué) |
| ✂ Recadrer | garder seulement une zone |
| ☝ Déplacer | déplacer un objet (Suppr pour l'effacer) ; une **couleur** ou une **taille** choisie s'applique à l'objet sélectionné |

`Ctrl+Z` annule, `Ctrl+Y` rétablit. **Copier l'image** → collez avec `Ctrl+V` dans Word, Teams, un courriel.
**Ouvrir dans Paint** : les annotations sont fixées dans l'image, puis Paint s'ouvre (vous ne pourrez plus les déplacer dans notre éditeur).

> ⚠ **Masquer** est fixé dans l'image d'origine dès l'enregistrement (le dossier `originales` ne contient plus la donnée cachée) : pas de retour possible. Une flèche ou un texte posé *avant* le masque : supprimez-le plutôt que de le déplacer. Avec « Copier dans le presse-papiers », l'image **finale** est copiée à l'enregistrement. Pour partager, utilisez les **exports** (Word, HTML, vidéo), pas le dossier de la série. Séries d'avant la v1.1.2 : bouton « 🔒 Masques définitifs ».

**La légende** en bas de l'éditeur sera le **sous-titre** de la vidéo : une phrase courte par étape, à l'impératif (« Cliquez sur *Fichier* »).

**Ma voix** : bouton **🎙 Enregistrer ma voix**, lisez la légende, **⏹ Arrêter**, **▶ Écouter** pour vérifier (**✖ Effacer** pour recommencer). Il faut un micro (celui du portable convient) autorisé dans *Paramètres Windows › Confidentialité › Microphone*. Parlez dans une pièce calme, à 20 cm du micro.

## 5. Fabriquer une fiche ou une vidéo
Dans la fenêtre principale, réorganisez avec ▲ ▼ puis :
- **📝 Document Word** : `document.docx` (A4) avec un titre « Étape n », la légende et l'image ; police Verdana 12, vrais titres Word (navigation, lecteurs d'écran) et **texte alternatif** sur chaque image. À retoucher dans Word.
- **📄 Fiche HTML/PDF** : page web numérotée, imprimable ou « Enregistrer au format PDF ».
- **🎬 Vidéo** : crée le dossier `video` dans la série (sous-titres, et votre voix si enregistrée).

Voir **[MODE_EMPLOI_VIDEO.md](MODE_EMPLOI_VIDEO.md)** pour les détails.

## 6. Problèmes fréquents
| Problème | Solution |
|---|---|
| Message « raccourci déjà utilisé » | changer le raccourci (*Raccourcis…*) |
| Le menu se ferme avant la capture | utiliser « Dans 3 secondes » |
| Écran flou/décalé sur écran à zoom 125 % | normal sur d'anciens Windows : signalez-le avec votre version de Windows |
| « Impossible d'utiliser le micro » | autoriser le micro dans Windows (voir ci-dessus) et vérifier qu'il est le micro par défaut |
| Aucune étape enregistrée avec la série de clics | un antivirus ou une stratégie d'école peut bloquer l'écoute des clics : essayer les captures par raccourci |
| « L'enregistrement n'a pas démarré » (vidéo de l'écran) | le message donne la dernière ligne d'erreur de ffmpeg ; zone dans l'écran et d'au moins 16 × 16 pixels |
| La vidéo de l'écran n'a pas de son | vérifier que les deux cases « Enregistrer aussi… » sont cochées, autoriser le micro dans Windows ; la barre d'état dit quel son est « Indisponible » ; une sortie audio doit être active pour le son de l'ordinateur |
| « Durée d'arrêt : indiquez un nombre entier de minutes… » | le champ « Arrêt automatique après » n'accepte que des chiffres (1 à 600) : corrigez-le ou videz-le |
| La barre d'enregistrement gêne | la faire glisser ailleurs : elle n'apparaît pas dans la vidéo |
| Rien dans le presse-papiers | cochez l'option « Copier aussi dans le presse-papiers » |

*Limites connues* : écrit pour Windows ; non testé sur Mac/Linux (la capture se fait, pas les raccourcis globaux). Une fenêtre exécutée « en administrateur » peut ne pas laisser passer les raccourcis.
