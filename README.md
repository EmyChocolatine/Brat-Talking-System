# Discord TTS Bot — ElevenLabs v3

Bot Discord Python permettant aux membres d'envoyer du texte à lire dans un canal vocal avec leur voix ElevenLabs personnelle.

## Fonctionnalités de cette première version

- `/t texte` : lit le texte dans le canal vocal où se trouve l'utilisateur.
- `/set-personal-voice voice_id [user]` : chacun configure sa voix ; les administrateurs peuvent cibler un autre membre.
- `/set-timeout minutes` : administrateurs uniquement, délai d'inactivité par serveur (30 minutes par défaut).
- Voix et timeout stockés par serveur Discord (guild).
- File d'attente par serveur.
- Validation de l'identifiant de voix auprès d'ElevenLabs.

## Prérequis

- Python 3.11 ou plus récent.
- FFmpeg installé et accessible dans le `PATH`, avec l'encodeur `libopus`.
- Une application/bot Discord et son token.
- Une clé API ElevenLabs et une voix accessible par cette clé.

Dans le portail Discord Developer, active les scopes `bot` et `applications.commands`. Permissions minimales : `View Channels`, `Connect`, `Speak`, `Send Messages` (pour les réponses). Aucun intent privilégié n'est requis.

## Installation

```bash
python -m venv .venv
# Windows :
.venv\Scripts\activate
# Linux/macOS :
source .venv/bin/activate

pip install -r requirements.txt
```

Copie `.env.example` vers `.env`, puis renseigne `DISCORD_TOKEN` et `ELEVENLABS_API_KEY`.

Lance le bot :

```bash
python bot.py
```

Les commandes slash sont synchronisées globalement au démarrage ; leur propagation peut prendre quelques minutes.

## Utilisation

- `/set-personal-voice voice_id:<ID>` configure ta propre voix.
- `/set-personal-voice voice_id:<ID> user:@Membre` permet à un administrateur de configurer la voix d'un autre membre.
- `/t texte:Bonjour tout le monde !`
- `/set-timeout minutes:30`

La voix personnelle est indépendante sur chaque serveur. Un membre peut donc avoir une voix différente selon la communauté.

## Notes importantes sur Eleven v3

Cette version appelle l'endpoint HTTP TTS `/v1/text-to-speech/{voice_id}/stream` avec `model_id=eleven_v3`, puis récupère le flux MP3 avant de le transmettre à FFmpeg. Le WebSocket `text-to-speech/{voice_id}/stream-input` n'est pas utilisé : la documentation ElevenLabs indique qu'il ne prend pas en charge `eleven_v3`.

Le bot limite volontairement `/t` à 2 000 caractères, en cohérence avec la limite d'une option slash Discord. Eleven v3 accepte jusqu'à 3 000 caractères côté modèle.

## À connaître avant une mise en production

Cette base est un premier socle fonctionnel, pas encore une version durcie pour un gros serveur public. À ajouter avant un déploiement à grande échelle : rate limiting par utilisateur, plafonds de dépenses/quota, tests automatisés, gestion de reconnexion, journalisation structurée et politique anti-abus.

La commande `/set-personal-voice` valide que la voix est accessible avec la clé API du bot. Les voix personnelles sont donc des identifiants de voix disponibles dans le compte ElevenLabs utilisé par le bot ; ce n'est pas une connexion séparée au compte ElevenLabs de chaque membre.

Le bot doit respecter les conditions d'utilisation ElevenLabs et les droits/consentements associés aux voix utilisées.
